"""Prima indicizzazione completa del corpus in un indice SQLite FTS5.

Uso:
    uv run python scripts/bootstrap_index.py

Legge i percorsi da config (CORPUS_PATH, INDEX_PATH). Richiede che il submodule
`italia-corpus` sia presente sotto data/. Ricostruisce l'indice da zero.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from legal_consultant.config import CORPUS_PATH, INDEX_PATH
from legal_consultant.index import fts
from legal_consultant.ingest.parser import parse_act

_SKIP_NAMES = {"README.md", "CONTRIBUTING.md", "LICENSE", "LICENSE.md"}


def main() -> int:
    corpus = Path(CORPUS_PATH)
    db = Path(INDEX_PATH)
    if not corpus.is_dir():
        print(f"Corpus non trovato in {corpus}. Aggiungi il submodule italia-corpus.")
        return 1

    db.parent.mkdir(parents=True, exist_ok=True)
    if db.exists():
        db.unlink()  # ricostruzione completa
    conn = fts.connect(db)
    if not fts.fts5_available(conn):
        print("ERRORE: questo build di SQLite non ha FTS5 abilitato.")
        return 2
    fts.init_db(conn)

    files = [p for p in corpus.rglob("*.md") if p.name not in _SKIP_NAMES]
    total = len(files)
    print(f"Atti da indicizzare: {total}")

    chunks = 0
    errors = 0
    t0 = time.monotonic()
    for i, f in enumerate(files, 1):
        try:
            parsed = parse_act(f, corpus)
            chunks += fts.insert_act(conn, parsed)
        except Exception as e:  # noqa: BLE001 - log e prosegui
            errors += 1
            print(f"  skip {f.name}: {e}")
        if i % 1000 == 0:
            conn.commit()
            print(f"  {i}/{total} atti, {chunks} chunk, {time.monotonic() - t0:.0f}s")

    conn.commit()
    conn.execute("INSERT INTO chunks(chunks) VALUES('optimize')")
    conn.commit()
    conn.close()
    print(f"Fatto: {total} atti, {chunks} chunk, {errors} errori, "
          f"{time.monotonic() - t0:.0f}s. Indice: {db}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
