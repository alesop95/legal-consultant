"""Benchmark della qualità del retrieval sull'indice reale.

Uso:
    uv run python scripts/benchmark_retrieval.py

Misura, su un insieme di domande reali con l'articolo atteso, se la ricerca fa emergere
l'articolo giusto tra i primi K risultati. Confronta il ranking BM25 attuale (pesi uniformi)
con un ranking che pesa di più le corrispondenze in rubrica e titolo dell'articolo. Serve a
decidere se adottare la pesatura e/o se serve la ricerca ibrida con embedding (ADR-003).

Non è un test unitario (richiede l'indice reale, non le fixture): è uno strumento di misura.
"""

from __future__ import annotations

import sys

from legal_consultant.config import INDEX_PATH
from legal_consultant.index import fts

# Colonne FTS5: 0 urn,1 tipo,2 numero,3 data,4 titolo,5 collezione,6 articolo,7 rubrica,
# 8 vigente,9 path,10 testo. La pesatura alza titolo(4) e rubrica(7).
_W_DEFAULT = "bm25(chunks)"
_W_RUBRICA = "bm25(chunks, 0,0,0,0, 3.0, 0, 1.0, 12.0, 0,0, 1.0)"

# (domanda, sottostringa che identifica l'atto nel titolo, numero articolo atteso)
GOLD = [
    ("risarcimento del danno per fatto illecito", "codice civile", "2043"),
    ("prescrizione ordinaria dei diritti dieci anni", "codice civile", "2946"),
    ("nullità del contratto", "codice civile", "1418"),
    ("risoluzione del contratto per inadempimento", "codice civile", "1453"),
    ("maggiore età e capacità di agire", "codice civile", "2"),
    ("buona fede nell'esecuzione del contratto", "codice civile", "1375"),
    ("tutela delle condizioni di lavoro sicurezza datore", "codice civile", "2087"),
    ("diritti e doveri reciproci dei coniugi", "codice civile", "143"),
    ("doveri dei genitori verso i figli mantenimento", "codice civile", "147"),
    ("nozione di testamento", "codice civile", "587"),
    ("recesso dal rapporto di lavoro per giusta causa", "codice civile", "2119"),
    ("periodo feriale ferie del lavoratore", "codice civile", "2109"),
    ("prescrizione del reato tempo necessario a prescrivere", "codice penale", "157"),
    ("reato di diffamazione", "codice penale", "595"),
    ("furto", "codice penale", "624"),
    ("truffa", "codice penale", "640"),
    ("omicidio", "codice penale", "575"),
    ("legittima difesa", "codice penale", "52"),
    ("stato di necessità", "codice penale", "54"),
    ("usura", "codice penale", "644"),
    ("concorso di persone nel reato", "codice penale", "110"),
    ("corrispondenza tra il chiesto e il pronunciato", "procedura civile", "112"),
    ("procedimento di ingiunzione decreto ingiuntivo", "procedura civile", "633"),
    ("diritto di recesso del consumatore", "consumo", "52"),
    ("garanzia legale di conformità dei beni", "consumo", "128"),
    ("danno ambientale risarcimento", "ambientale", "300"),
]

_TOPK = 8


def _ranked(conn, weight_expr, query):
    """Lista (titolo, articolo) dei primi risultati vigenti, deduplicati, per l'espressione
    di peso data."""
    match = fts.to_match_query(query)
    sql = (
        f"SELECT urn, titolo, articolo, {weight_expr} AS sc "
        "FROM chunks WHERE chunks MATCH ? AND vigente='true' ORDER BY sc LIMIT ?"
    )
    rows = conn.execute(sql, (match, _TOPK * 5)).fetchall()
    seen, out = set(), []
    for r in rows:
        key = (r["urn"], r["articolo"])
        if key in seen:
            continue
        seen.add(key)
        out.append((r["titolo"] or "", r["articolo"] or ""))
        if len(out) >= _TOPK:
            break
    return out


def _rank_of(results, code, art):
    for i, (titolo, articolo) in enumerate(results, 1):
        if articolo == art and code.lower() in titolo.lower():
            return i
    return None


def main() -> int:
    if not INDEX_PATH.exists():
        print(f"Indice non trovato in {INDEX_PATH}. Esegui prima scripts/bootstrap_index.py.")
        return 1
    conn = fts.connect(INDEX_PATH)

    print(f"{'domanda':52} {'atteso':22} {'def':>4} {'pesato':>7}")
    print("-" * 88)
    agg = {"def": {1: 0, 5: 0, 8: 0}, "wt": {1: 0, 5: 0, 8: 0}}
    for q, code, art in GOLD:
        rd = _rank_of(_ranked(conn, _W_DEFAULT, q), code, art)
        rw = _rank_of(_ranked(conn, _W_RUBRICA, q), code, art)
        for tag, r in (("def", rd), ("wt", rw)):
            for k in (1, 5, 8):
                if r is not None and r <= k:
                    agg[tag][k] += 1
        atteso = f"{code} art.{art}"
        print(f"{q[:52]:52} {atteso[:22]:22} {str(rd or '-'):>4} {str(rw or '-'):>7}")

    n = len(GOLD)
    print("-" * 88)
    for k in (1, 5, 8):
        print(f"recall@{k}:  default {agg['def'][k]}/{n}   pesato {agg['wt'][k]}/{n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
