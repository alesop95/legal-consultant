"""Parser di un atto di italia-corpus.

Ogni atto è un file Markdown con frontmatter YAML (metadati) e un corpo in cui gli
articoli sono marcati da intestazioni `## Art. N.` con rubrica opzionale dopo un
trattino lungo. Il parser separa i metadati e spezza il corpo in chunk a
granularità di articolo (più un chunk di preambolo per il testo che precede il
primo articolo), così che ogni chunk mappi 1:1 a un riferimento citabile.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import frontmatter

from ..config import long_path

# Intestazione di articolo, es:
#   "## Art. 1."
#   "## Art. 1. — Approvazione del codice e delle disposizioni connesse"
#   "## Art. 2-bis."
_ARTICLE_RE = re.compile(
    r"^##\s+Art\.?\s*(?P<num>[\w\-]+(?:\s+\w+)?)\.?(?:\s*[—–-]\s*(?P<rubrica>.+))?\s*$"
)

# Collezione del corpus che raccoglie le leggi abrogate. Nel frontmatter di italia-corpus
# il campo `vigente` risulta True anche per questi atti, quindi non è affidabile per
# escluderli: l'appartenenza a questa collezione è il segnale corretto, e qui declassa
# l'atto a non vigente.
_ABROGATI_COLLECTION = "Atti normativi abrogati (in originale)"


@dataclass
class Act:
    """Metadati di un atto, dal frontmatter YAML più la collocazione nel corpus."""

    tipo: str
    numero: str
    data: str
    titolo: str
    urn: str
    codice_redazionale: str
    vigente: bool
    collezione: str
    path: str  # percorso relativo alla radice del corpus, in forma posix


@dataclass
class Chunk:
    """Un'unità citabile: un articolo (o il preambolo, con articolo None)."""

    articolo: str | None
    rubrica: str | None
    testo: str


@dataclass
class ParsedAct:
    act: Act
    chunks: list[Chunk]


def parse_act(file_path: Path, corpus_root: Path) -> ParsedAct:
    """Parsa un file .md del corpus in metadati + chunk per articolo."""
    post = frontmatter.load(long_path(file_path))
    meta = post.metadata
    rel = file_path.resolve().relative_to(corpus_root.resolve()).as_posix()
    collezione = rel.split("/", 1)[0]

    # `vigente` dal frontmatter, ma declassato a False per gli atti della collezione delle
    # abrogate (vedi nota su _ABROGATI_COLLECTION).
    vigente = bool(meta.get("vigente", False)) and collezione != _ABROGATI_COLLECTION

    act = Act(
        tipo=str(meta.get("tipo", "")).strip(),
        numero=str(meta.get("numero", "")).strip(),
        data=str(meta.get("data", "")).strip(),
        titolo=str(meta.get("titolo", "")).strip(),
        urn=str(meta.get("urn", "")).strip(),
        codice_redazionale=str(meta.get("codice_redazionale", "")).strip(),
        vigente=vigente,
        collezione=collezione,
        path=rel,
    )
    return ParsedAct(act=act, chunks=_split_chunks(post.content))


def _split_chunks(body: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    cur_articolo: str | None = None
    cur_rubrica: str | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf
        testo = "\n".join(buf).strip()
        if testo or cur_articolo is not None:
            chunks.append(Chunk(articolo=cur_articolo, rubrica=cur_rubrica, testo=testo))
        buf = []

    for line in body.splitlines():
        m = _ARTICLE_RE.match(line.strip())
        if m:
            flush()
            cur_articolo = m.group("num").strip()
            rub = (m.group("rubrica") or "").strip()
            cur_rubrica = rub or None
        else:
            buf.append(line)
    flush()
    return chunks
