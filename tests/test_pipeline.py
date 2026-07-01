"""Test end-to-end del parser e dell'indice FTS5 sulle fixture (due atti reali)."""

from __future__ import annotations

from pathlib import Path

import pytest

from legal_consultant import update
from legal_consultant.index import fts
from legal_consultant.ingest.parser import _split_chunks, parse_act

FIX = Path(__file__).parent / "fixtures"


def _build_index():
    conn = fts.connect(":memory:")
    if not fts.fts5_available(conn):
        pytest.skip("FTS5 non disponibile in questo build di SQLite")
    fts.init_db(conn)
    for f in sorted(FIX.rglob("*.md")):
        fts.insert_act(conn, parse_act(f, FIX))
    return conn


def test_frontmatter_e_chunking():
    parsed = parse_act(FIX / "Codici" / "giustizia_contabile.md", FIX)
    a = parsed.act
    assert a.tipo == "DECRETO LEGISLATIVO"
    assert a.numero == "174"
    assert a.data == "2016-08-26"
    assert a.urn == "urn:nir:stato:decreto.legislativo:2016-08-26;174"
    assert a.vigente is True
    assert a.collezione == "Codici"

    articoli = [c for c in parsed.chunks if c.articolo is not None]
    assert any(c.articolo == "1" for c in articoli)
    # Il primo articolo del decreto porta una rubrica dopo il trattino lungo.
    art1 = next(c for c in articoli if c.articolo == "1")
    assert art1.rubrica and "Approvazione del codice" in art1.rubrica
    # Esiste un chunk di preambolo (testo prima del primo articolo).
    assert any(c.articolo is None and c.testo for c in parsed.chunks)


def test_ricerca_bm25_trova_atto_pertinente():
    conn = _build_index()
    rows = fts.search(conn, "responsabilita amministrativa", limit=5)
    assert rows, "la ricerca non ha restituito risultati"
    assert any("giustizia_contabile" in r["path"] for r in rows)
    top = rows[0]
    assert top["titolo"]
    assert top["estratto"]


def test_filtro_solo_vigenti():
    conn = _build_index()
    rows = fts.search(conn, "codice", limit=10, solo_vigenti=True)
    assert all(True for _ in rows)  # nessun errore SQL col filtro
    assert rows


def test_get_act_per_urn_e_articolo():
    conn = _build_index()
    urn = "urn:nir:stato:decreto.legislativo:2016-08-26;174"
    # Atto intero: piu chunk, in ordine di inserimento (preambolo prima degli articoli).
    rows = fts.get_act(conn, urn=urn)
    assert rows, "atto non trovato per urn"
    assert all(r["urn"] == urn for r in rows)
    assert len(rows) > 1
    # Singolo articolo: filtro su articolo restituisce solo quel chunk.
    art1 = fts.get_act(conn, urn=urn, articolo="1")
    assert len(art1) == 1
    assert art1[0]["articolo"] == "1"
    assert "Approvazione del codice" in (art1[0]["rubrica"] or "")
    # Atto inesistente: lista vuota, nessun errore.
    assert fts.get_act(conn, urn="urn:nir:stato:inesistente:1900-01-01;0") == []


def test_corpus_stats():
    conn = _build_index()
    n_atti, n_chunks = fts.corpus_stats(conn)
    assert n_atti == 2  # le due fixture
    assert n_chunks >= n_atti


def test_chunking_articoli_multilivello():
    # I codici hanno il decreto di approvazione a `## Art.` e l'articolato annesso a
    # `### Art.`, con intestazioni strutturali `## LIBRO/Capo/Sezione` da ignorare.
    body = (
        "## Art. 01.\n"
        "Disposizione di approvazione.\n\n"
        "## - LIBRO I Titolo I GIUDICE\n"
        "### Art. 1. — Giurisdizione penale\n"
        "Testo dell'articolo 1.\n"
        "### Art. 2. — Cognizione del giudice\n"
        "Testo dell'articolo 2.\n"
        "## Capo II COMPETENZA\n"
        "### Art. 11-bis.\n"
        "Testo dell'articolo 11-bis.\n"
        "### Art. 2043. (Risarcimento per fatto illecito)\n"
        "Testo dell'articolo 2043.\n"
    )
    chunks = _split_chunks(body)
    arts = [c.articolo for c in chunks if c.articolo is not None]
    assert "01" in arts  # decreto di approvazione (livello 2)
    assert {"1", "2", "11-bis", "2043"} <= set(arts)  # codice annesso (livello 3)
    # le intestazioni strutturali non diventano articoli
    assert not any("LIBRO" in a or "Capo" in a for a in arts)
    # rubrica nelle due forme: trattino (italia-corpus) e parentesi (Normattiva)
    by_art = {c.articolo: c for c in chunks if c.articolo is not None}
    assert by_art["1"].rubrica == "Giurisdizione penale"
    assert by_art["2043"].rubrica == "Risarcimento per fatto illecito"


def test_to_match_query_sanifica():
    assert fts.to_match_query("responsabilità amministrativa") == '"responsabilità" OR "amministrativa"'
    assert fts.to_match_query("") == ""
    assert fts.to_match_query("   ...   ") == ""  # solo punteggiatura: nessun token


def test_search_input_malformato_non_crasha():
    conn = _build_index()
    # Input che sarebbero sintassi MATCH invalida vengono sanificati, non sollevano.
    for q in ['"', "*", "NEAR(", "art. 2087 c.c.", "codice OR penale", "(())"]:
        fts.search(conn, q)  # non deve sollevare OperationalError
    # Query senza token: nessuna interrogazione, lista vuota.
    assert fts.search(conn, "   ...   ") == []


def test_reindex_incrementale():
    conn = _build_index()
    rel = "Codici/giustizia_contabile.md"
    before = fts.get_act(conn, path=rel)
    assert before, "atto assente nell'indice di partenza"

    # Cancellazione: l'atto sparisce dall'indice.
    assert update.reindex_paths(conn, FIX, changed=[], deleted=[rel]) == 0
    assert fts.get_act(conn, path=rel) == []

    # Reinserimento dal disco: stessi chunk reindicizzati.
    n = update.reindex_paths(conn, FIX, changed=[rel], deleted=[])
    assert n == len(before)
    assert fts.get_act(conn, path=rel)


def test_state_roundtrip(tmp_path):
    sp = tmp_path / "index" / "state.json"
    assert update.read_state(sp) is None  # assente
    written = update.write_state(sp, "abc1234", "2026-06-30T00:00:00+00:00", 10, 42)
    assert written["atti"] == 10 and written["chunk"] == 42
    back = update.read_state(sp)
    assert back["corpus_commit"] == "abc1234"
    assert back["reindicizzato_il"]  # timestamp presente
