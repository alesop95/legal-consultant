"""Aggiornamento del corpus e reindicizzazione incrementale (Fase 3).

Uso:
    uv run python scripts/update_corpus.py

Fa il git pull del submodule del corpus, calcola i file .md cambiati fra la vecchia e
la nuova revisione e reindicizza nell'indice FTS5 solo quelli, poi salva lo stato.
Pensato per essere schedulato (Windows Task Scheduler) per tenere la legge aggiornata.
Richiede un indice gia' costruito da `scripts/bootstrap_index.py`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from legal_consultant import update
from legal_consultant.config import CORPUS_PATH, INDEX_PATH, STATE_PATH
from legal_consultant.index import fts


def main() -> int:
    corpus = Path(CORPUS_PATH)
    if not corpus.is_dir():
        print(f"Corpus non trovato in {corpus}. Esegui prima scripts/setup.py.")
        return 1
    if not Path(INDEX_PATH).exists():
        print(f"Indice non trovato in {INDEX_PATH}. Esegui prima scripts/bootstrap_index.py.")
        return 1

    old_commit, _ = update.corpus_revision(corpus)
    if old_commit is None:
        print("Il corpus non risulta un repo git: impossibile aggiornare in modo incrementale.")
        return 2

    try:
        update.pull(corpus)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        print(f"git pull fallito: {e}")
        return 2

    new_commit, new_date = update.corpus_revision(corpus)
    conn = fts.connect(INDEX_PATH)
    try:
        if new_commit == old_commit:
            print(f"Corpus gia' aggiornato (commit {old_commit[:8]}). Reindex non necessario.")
            changed: list[str] = []
            deleted: list[str] = []
        else:
            changed, deleted = update.changed_files(corpus, old_commit, new_commit)
            n = update.reindex_paths(conn, corpus, changed, deleted)
            print(f"{old_commit[:8]} -> {new_commit[:8]}: "
                  f"{len(changed)} atti aggiornati, {len(deleted)} rimossi, {n} chunk reinseriti.")
        n_atti, n_chunks = fts.corpus_stats(conn)
    finally:
        conn.close()

    update.write_state(STATE_PATH, new_commit, new_date, n_atti, n_chunks)
    print(f"Stato salvato in {STATE_PATH}: {n_atti} atti, {n_chunks} chunk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
