"""Query rapida sull'indice FTS5 — sanità e uso manuale.

Uso:
    uv run python scripts/query.py "responsabilita amministrativa" 5

È anche il precursore del tool `cerca_normativa` del server MCP (Fase 2).
"""

from __future__ import annotations

import sys

from legal_consultant.config import INDEX_PATH
from legal_consultant.index import fts


def main() -> int:
    if len(sys.argv) < 2:
        print('Uso: uv run python scripts/query.py "<query>" [limit]')
        return 1
    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    if not INDEX_PATH.exists():
        print(f"Indice non trovato in {INDEX_PATH}. Esegui prima scripts/bootstrap_index.py.")
        return 1

    conn = fts.connect(INDEX_PATH)
    rows = fts.search(conn, query, limit=limit)
    if not rows:
        print("Nessun risultato.")
        return 0

    for r in rows:
        art = f"art. {r['articolo']}" if r["articolo"] else "(preambolo)"
        print(f"[{r['score']:.2f}] {r['tipo']} n.{r['numero']} {r['data']} — {art}")
        print(f"    {r['titolo']}")
        if r["rubrica"]:
            print(f"    rubrica: {r['rubrica']}")
        print(f"    {r['estratto']}")
        print(f"    {r['path']}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
