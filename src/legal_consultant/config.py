"""Configurazione: percorsi locali del corpus e dell'indice.

Legge le variabili da ambiente, con fallback su un file .env in radice e su
default relativi alla radice del progetto. Nessun segreto: il prodotto non usa
chiavi API (il ragionamento avviene in Claude Desktop).
"""

from __future__ import annotations

import os
from pathlib import Path

# Radice del progetto: due livelli sopra questo file (src/legal_consultant/config.py).
REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv(path: Path) -> None:
    """Carica chiavi KEY=VALUE da un .env, senza dipendenze esterne.

    Non sovrascrive variabili già presenti nell'ambiente.
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(REPO_ROOT / ".env")


def _resolve(env_key: str, default_rel: str) -> Path:
    raw = os.environ.get(env_key)
    p = Path(raw) if raw else (REPO_ROOT / default_rel)
    return p if p.is_absolute() else (REPO_ROOT / p)


CORPUS_PATH = _resolve("CORPUS_PATH", "data/italia-corpus")
INDEX_PATH = _resolve("INDEX_PATH", "data/index/legge.sqlite")
STATE_PATH = _resolve("STATE_PATH", "data/index/state.json")
