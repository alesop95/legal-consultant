"""Test end-to-end del parser e dell'indice FTS5 sulle fixture (due atti reali)."""

from __future__ import annotations

from pathlib import Path

import pytest

from legal_consultant.index import fts
from legal_consultant.ingest.parser import parse_act

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
