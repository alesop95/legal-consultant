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


def long_path(p: str | Path) -> str:
    """Percorso assoluto in forma adatta all'I/O su file.

    Su Windows antepone il prefisso extended-length `\\\\?\\` al path assoluto, così
    `open()` e `os.stat` superano il limite storico dei 260 caratteri (MAX_PATH) senza
    richiedere modifiche al registro di sistema né privilegi di amministratore: il
    corpus italiano ha nomi di file molto lunghi che altrimenti non sarebbero leggibili
    su Windows. Su sistemi POSIX restituisce il path risolto invariato.
    """
    s = str(Path(p).resolve())
    if os.name == "nt" and not s.startswith("\\\\?\\"):
        return "\\\\?\\" + s
    return s


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
# Collezione supplementare, fuori dal submodule: ospita i codici fondamentali (civile,
# penale, ecc.) il cui articolato manca in italia-corpus, scaricati da Normattiva con
# scripts/fetch_codici.py e indicizzati dal bootstrap insieme al corpus principale.
EXTRA_CORPUS_PATH = _resolve("EXTRA_CORPUS_PATH", "data/codici-extra")
# Seconda collezione supplementare: ospita le classi di atti che il corpus principale non
# contiene affatto perche' assenti dal catalogo delle collezioni preconfezionate di
# Normattiva (leggi ordinarie, decreti-legge vigenti, Costituzione), recuperate
# dall'API Open Data con scripts/fetch_normattiva.py. Vedi
# docs/audit-completezza-corpus.md per la misura della lacuna e la sua causa.
# A differenza di codici-extra, che e' piccola e tracciata, questa e' voluminosa
# (oltre diecimila atti) e resta fuori da git, come il corpus principale: si ricostruisce
# dalla fonte, non si spedisce nel repository.
SUPPL_CORPUS_PATH = _resolve("SUPPL_CORPUS_PATH", "data/normattiva-suppl")
INDEX_PATH = _resolve("INDEX_PATH", "data/index/legge.sqlite")
STATE_PATH = _resolve("STATE_PATH", "data/index/state.json")


def radici_corpus() -> list[Path]:
    """Tutte le radici di corpus da indicizzare, nell'ordine in cui vanno lette.

    Il corpus principale piu' le collezioni supplementari che esistono su disco. Chi
    indicizza itera su questa lista invece di conoscere i singoli percorsi, cosi'
    aggiungere una collezione non richiede di ritoccare ogni chiamante.
    """
    return [p for p in (CORPUS_PATH, EXTRA_CORPUS_PATH, SUPPL_CORPUS_PATH) if p.is_dir()]
