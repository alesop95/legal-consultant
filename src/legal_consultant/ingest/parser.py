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

# Intestazione di articolo. Il livello di cancelletti varia nel corpus: gli atti
# semplici e i decreti di approvazione usano `## Art. N.`, mentre l'articolato dei
# codici annessi (es. codice di procedura penale) usa `### Art. N. — Rubrica`. Si
# accettano quindi da 2 a 4 cancelletti. Le intestazioni strutturali dei codici
# (`## LIBRO ...`, `## Capo ...`, `## Sezione ...`) non iniziano con "Art" e non
# corrispondono, quindi restano testo e non creano falsi chunk.
# La rubrica, se presente, segue il numero in due forme alternative: dopo un trattino
# lungo (italia-corpus) o tra parentesi (Normattiva via normattiva2md). Entrambe sono
# catturate, in gruppi distinti poi unificati.
#   "## Art. 1."
#   "### Art. 11-bis. — Casi di connessione"
#   "### Art. 2043. (Risarcimento per fatto illecito)"
_ARTICLE_RE = re.compile(
    r"^#{2,4}\s+Art\.?\s*(?P<num>[\w\-]+(?:\s+\w+)?)\.?\s*"
    r"(?:[—–-]\s*(?P<rub_dash>.+)|\((?P<rub_par>.+)\))?\s*$"
)

# Allegato numerato, per esempio `## Allegato I` o `## Allegato 2 (Tabella A)`. Vale come
# confine di chunk allo stesso titolo di un articolo, perché un allegato è contenuto
# normativo a sé: le diciotto disposizioni transitorie e finali della Costituzione stanno
# tutte negli allegati. Senza questo confine finirebbero in coda all'ultimo articolo e
# verrebbero citate col numero di quello, cioè con una citazione falsa. L'unità citabile
# risultante è "Allegato I", che è come la fonte stessa la nomina.
# Il numero è obbligatorio: una intestazione di sola rassegna come `## Allegati`, presente
# nei codici, non corrisponde e resta testo.
_ALLEGATO_RE = re.compile(
    r"^#{2,4}\s+Allegato\s+(?P<num>[\w\-]+)\.?\s*"
    r"(?:[—–-]\s*(?P<rub_dash>.+)|\((?P<rub_par>.+)\))?\s*$",
    re.IGNORECASE,
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
        stripped = line.strip()
        m = _ARTICLE_RE.match(stripped)
        etichetta = ""
        if m is None:
            m = _ALLEGATO_RE.match(stripped)
            etichetta = "Allegato "
        if m:
            flush()
            cur_articolo = etichetta + m.group("num").strip()
            rub = (m.group("rub_dash") or m.group("rub_par") or "").strip()
            cur_rubrica = rub or None
        else:
            buf.append(line)
    flush()
    return chunks
