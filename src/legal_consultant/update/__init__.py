"""Aggiornamento del corpus e reindicizzazione incrementale (Fase 3).

Il corpus e' un submodule git: aggiornarlo e' un `git pull`, e reindicizzare significa
ritoccare nell'indice FTS5 i soli atti cambiati fra la vecchia e la nuova revisione,
non ricostruire tutto. Le funzioni qui sono divise fra logica pura, testabile sulle
fixture (`reindex_paths`, lettura/scrittura dello stato), e interazione con git
(`corpus_revision`, `changed_files`, `pull`), che richiede un repo reale.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ..config import long_path
from ..index import fts
from ..ingest.parser import parse_act

# Stessi file non normativi saltati dal bootstrap.
_SKIP_NAMES = {"README.md", "CONTRIBUTING.md", "LICENSE", "LICENSE.md"}


def _git(corpus_root: str | Path, *args: str, timeout: float = 30) -> str:
    """Esegue git nel repo del corpus e restituisce stdout. Solleva
    CalledProcessError sul fallimento, FileNotFoundError se git non c'e',
    TimeoutExpired oltre `timeout` secondi (così una chiamata non blocca mai un tool)."""
    res = subprocess.run(
        ["git", "-C", str(corpus_root), *args],
        capture_output=True, text=True, check=True, timeout=timeout,
    )
    return res.stdout.strip()


def corpus_revision(corpus_root: str | Path) -> tuple[str | None, str | None]:
    """(commit, data ISO 8601) dell'HEAD del corpus, o (None, None) se non e' un repo
    git o git non e' disponibile. Non solleva: la freschezza e' un'informazione
    accessoria che non deve far fallire un tool."""
    try:
        out = _git(corpus_root, "log", "-1", "--format=%H%x09%cI")
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return None, None
    commit, _, date = out.partition("\t")
    return (commit or None), (date or None)


def pull(corpus_root: str | Path) -> None:
    """Aggiorna il corpus all'ultimo commit del remoto, solo fast-forward."""
    _git(corpus_root, "pull", "--ff-only")


def changed_files(
    corpus_root: str | Path, old_rev: str, new_rev: str
) -> tuple[list[str], list[str]]:
    """Path .md (relativi al corpus, posix) aggiunti o modificati e cancellati fra due
    revisioni. Salta i file non normativi."""
    out = _git(corpus_root, "diff", "--name-status", old_rev, new_rev)
    changed: list[str] = []
    deleted: list[str] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, rel = parts[0], parts[-1]
        if not rel.endswith(".md") or Path(rel).name in _SKIP_NAMES:
            continue
        (deleted if status.startswith("D") else changed).append(rel)
    return changed, deleted


def reindex_paths(
    conn,
    corpus_root: str | Path,
    changed: list[str],
    deleted: list[str],
) -> int:
    """Reindicizzazione incrementale (upsert per path): rimuove dall'indice i path
    cancellati, e per ogni path cambiato cancella le righe vecchie e reinserisce i
    chunk ri-parsati. Un path cambiato ma non piu' presente su disco viene trattato
    come cancellato. Ritorna il numero di chunk reinseriti. Logica pura, testabile
    senza git."""
    corpus_root = Path(corpus_root)
    for rel in deleted:
        fts.delete_path(conn, rel)
    n_chunks = 0
    for rel in changed:
        f = corpus_root / rel
        fts.delete_path(conn, rel)
        if not os.path.isfile(long_path(f)):
            continue
        n_chunks += fts.insert_act(conn, parse_act(f, corpus_root))
    conn.commit()
    return n_chunks


def write_state(
    state_path: str | Path,
    commit: str | None,
    corpus_date: str | None,
    n_atti: int,
    n_chunks: int,
) -> dict:
    """Persiste lo stato dell'indice in JSON (commit e data del corpus, conteggi,
    timestamp del reindex), per `info_corpus` e per il prossimo aggiornamento."""
    state = {
        "corpus_commit": commit,
        "corpus_date": corpus_date,
        "atti": n_atti,
        "chunk": n_chunks,
        "reindicizzato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    p = Path(state_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return state


def read_state(state_path: str | Path) -> dict | None:
    """Stato persistito, o None se assente o illeggibile."""
    p = Path(state_path)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
