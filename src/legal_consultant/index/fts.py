"""Indice full-text BM25 su SQLite FTS5.

Una sola tabella virtuale `chunks`: le colonne testuali (titolo, articolo, rubrica,
testo) sono indicizzate, i metadati sono UNINDEXED ma memorizzati per la citazione e
i filtri. Il ranking è BM25 nativo di FTS5. L'aggiornamento incrementale per file si
fa cancellando le righe con quel `path` e reinserendole.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from pathlib import Path

from ..ingest.parser import ParsedAct

# Token alfanumerici unicode: lettere accentate e cifre incluse, punteggiatura esclusa.
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)

# Preposizioni (semplici e articolate), articoli, congiunzioni e pronomi comuni: parole
# prive di contenuto giuridico proprio ma frequentissime nel corpo degli articoli. Usate
# solo per calcolare la sovrapposizione domanda/rubrica (_rubrica_bonus), non per la query
# MATCH: FTS5 le cerca comunque, altrimenti "diritto DI recesso" perderebbe "di" come
# sintassi anziché come parola, ma la loro presenza in un testo lungo altrimenti gonfia il
# punteggio BM25 di righe irrilevanti solo perché condividono parole di funzione.
_STOPWORDS_IT = frozenset("""
a ad al allo ai agli all agl alla alle
con col coi
da dal dallo dai dagli dall dagl dalla dalle
di del dello dei degli dell degl della delle
in nel nello nei negli nell negl nella nelle
su sul sullo sui sugli sull sugl sulla sulle
per tra fra
il lo la i gli le un uno una
e ed o od ma se non
che chi cui
questo questa questi queste quello quella quelli quelle
suo sua suoi sue loro
""".split())


def to_match_query(text: str) -> str:
    """Trasforma testo libero in una query FTS5 sicura.

    Estrae i soli token alfanumerici (unicode), li cita come termini letterali e li
    unisce in OR: qualunque input dell'utente viene trattato come parole da cercare e
    mai come sintassi MATCH (virgolette, `*`, `NEAR`, parentesi), che altrimenti
    solleverebbe un errore SQL su testo malformato. Il ranking BM25 promuove comunque
    i chunk che contengono piu' termini. Restituisce stringa vuota se non c'e' alcun
    token: il chiamante interpreta l'assenza di token come "nessun risultato".

    Le stopword italiane (articoli, preposizioni, congiunzioni) sono escluse dall'OR:
    incluse, abbinano quasi ogni riga del corpus (es. "di" da solo abbina centinaia di
    migliaia di chunk), il che sia appesantisce la query sia diluisce il campione su cui si
    calcola il punteggio. Se la domanda è fatta di sole stopword si ripiega su tutti i
    token, per non restituire zero risultati.
    """
    tokens = _TOKEN_RE.findall(text or "")
    content = [t for t in tokens if t.lower() not in _STOPWORDS_IT]
    return " OR ".join(f'"{t}"' for t in (content or tokens))

_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
    urn UNINDEXED,
    tipo UNINDEXED,
    numero UNINDEXED,
    data UNINDEXED,
    titolo,
    collezione UNINDEXED,
    articolo,
    rubrica,
    vigente UNINDEXED,
    path UNINDEXED,
    testo,
    tokenize = 'unicode61 remove_diacritics 2'
);
"""

# Indici di colonna (0-based) per snippet(): 4=titolo, 10=testo.
_COL_TESTO = 10

# Pesi BM25 per colonna (uno per ognuna delle 11 colonne del DDL). Titolo e soprattutto
# rubrica pesano più del corpo: in un corpus giuridico l'articolo la cui rubrica coincide
# con la domanda è quasi sempre quello cercato. Misurato su scripts/benchmark_retrieval.py
# (recall@8 da 15/26 a 19/26). Le colonne UNINDEXED hanno peso ininfluente (posto a 0).
#           urn tipo num data  titolo coll art  rubrica vig path testo
_BM25 = "bm25(chunks, 0,0,0,0,  3.0,   0,  1.0, 12.0,   0,   0,  1.0)"

# I 5 codici fondamentali scaricati da Normattiva (scripts/fetch_codici.py, stesso URN). A
# parità di rubrica, civile/penale/procedura civile sono la lettura più probabile di una
# domanda generica; i codici di settore (navigazione, penali militari), pur fondamentali,
# vincono un pareggio di rubrica solo se nessun codice generale ha una rubrica altrettanto
# pertinente. Punteggio BM25 di SQLite: più negativo È più rilevante, quindi qui i bonus
# sono negativi.
_CODICE_GENERALE_BONUS: dict[str, float] = {
    "urn:nir:stato:regio.decreto:1942-03-16;262": -3.0,   # codice civile
    "urn:nir:stato:regio.decreto:1930-10-19;1398": -3.0,  # codice penale
    "urn:nir:stato:regio.decreto:1940-10-28;1443": -2.0,  # codice di procedura civile
}


def _content_tokens(text: str) -> list[str]:
    """Token di contenuto normalizzati: minuscolo, senza accenti, senza stopword italiane."""
    normalized = unicodedata.normalize("NFKD", text or "")
    normalized = "".join(c for c in normalized if not unicodedata.combining(c)).lower()
    return [t for t in _TOKEN_RE.findall(normalized) if t not in _STOPWORDS_IT]


def _rubrica_bonus(rubrica: str, query_tokens: frozenset[str]) -> float:
    """Bonus di punteggio quando la rubrica dell'articolo coincide col nocciolo della domanda.

    BM25 pesa frequenza e lunghezza di colonna, non la coincidenza col nomen iuris cercato:
    una rubrica breve ed esatta ("Furto") perde sistematicamente contro varianti più lunghe
    che ripetono la stessa parola nel corpo ("Furto d'uso...", "Furto militare"). Qui si
    misura invece quanto della rubrica è coperto dalle parole di contenuto della domanda: se
    la rubrica è (quasi) interamente contenuta nella domanda, l'articolo è quasi certamente
    quello cercato, a prescindere da parole generiche aggiuntive nella domanda ("il reato
    di...", "la disciplina del..."). Il verso è opposto della normale sovrapposizione
    domanda-su-rubrica proprio perché le domande sono più libere e prolisse delle rubriche.
    """
    label_tokens = set(_content_tokens(rubrica))
    if not label_tokens or not query_tokens:
        return 0.0
    coverage_label = len(label_tokens & query_tokens) / len(label_tokens)
    if coverage_label >= 0.8:
        return -8.0
    if coverage_label >= 0.5:
        return -3.0
    return 0.0


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(_DDL)


def fts5_available(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_probe USING fts5(x)")
        conn.execute("DROP TABLE IF EXISTS _fts5_probe")
        return True
    except sqlite3.OperationalError:
        return False


def delete_path(conn: sqlite3.Connection, path: str) -> None:
    conn.execute("DELETE FROM chunks WHERE path = ?", (path,))


def insert_act(conn: sqlite3.Connection, parsed: ParsedAct) -> int:
    a = parsed.act
    vigente = "true" if a.vigente else "false"
    rows = [
        (
            a.urn, a.tipo, a.numero, a.data, a.titolo, a.collezione,
            c.articolo or "", c.rubrica or "", vigente, a.path, c.testo,
        )
        for c in parsed.chunks
    ]
    conn.executemany(
        "INSERT INTO chunks "
        "(urn, tipo, numero, data, titolo, collezione, articolo, rubrica, vigente, path, testo) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    return len(rows)


def search(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 8,
    solo_vigenti: bool = True,
    sanitize: bool = True,
    dedup: bool = True,
) -> list[sqlite3.Row]:
    """Ricerca BM25 su testo libero.

    Con `sanitize=True` (default) la `query` passa per `to_match_query`, che la rende
    una espressione MATCH sempre valida; con `sanitize=False` la `query` e' usata cosi'
    com'e' (sintassi MATCH di FTS5 a carico del chiamante). Se dopo la sanificazione non
    resta alcun token, ritorna lista vuota senza interrogare il database.

    Con `dedup=True` (default) i risultati sono deduplicati per (urn, articolo) tenendo
    il primo, cioe' il meglio classificato: il corpus archivia alcuni atti in piu'
    collezioni e senza deduplica lo stesso articolo comparirebbe piu' volte. Per ottenere
    `limit` risultati distinti si sovra-campiona la query sottostante.

    Sul campione sovra-campionato, prima della deduplica, il punteggio BM25 grezzo viene
    corretto con `_rubrica_bonus` e `_CODICE_GENERALE_BONUS` e le righe sono riordinate: il
    bonus premia le rubriche quasi esattamente coincidenti con la domanda e i codici
    fondamentali generali sugli omonimi di settore. La colonna `score` restituita resta il
    BM25 grezzo di FTS5 (metrica trasparente), l'ordinamento invece riflette il punteggio
    corretto. Il sovra-campionamento è ampio (50x) perché la normalizzazione per lunghezza
    di BM25 può relegare l'articolo giusto ben oltre le prime posizioni grezze quando il suo
    testo è lungo (es. "usura" risultava 77° su 472 corrispondenze prima del bonus): un
    campione stretto lo escluderebbe dal ricalcolo prima ancora che il bonus possa agire.
    """
    match = to_match_query(query) if sanitize else query
    if not match:
        return []
    oversample = limit * 50 if dedup else limit
    sql = [
        "SELECT urn, tipo, numero, data, titolo, collezione, articolo, rubrica, vigente, path,",
        f"       snippet(chunks, {_COL_TESTO}, '[', ']', ' … ', 16) AS estratto,",
        f"       {_BM25} AS score",
        "FROM chunks WHERE chunks MATCH ?",
    ]
    params: list[object] = [match]
    if solo_vigenti:
        sql.append("AND vigente = 'true'")
    sql.append("ORDER BY score LIMIT ?")
    params.append(oversample)
    rows = conn.execute("\n".join(sql), params).fetchall()

    query_tokens = frozenset(_content_tokens(query))
    rows = sorted(
        rows,
        key=lambda r: r["score"]
        + _rubrica_bonus(r["rubrica"] or "", query_tokens)
        + _CODICE_GENERALE_BONUS.get(r["urn"], 0.0),
    )
    if not dedup:
        return rows[:limit]

    seen: set[tuple[str, str]] = set()
    out: list[sqlite3.Row] = []
    for r in rows:
        key = (r["urn"], r["articolo"] or "")
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
        if len(out) >= limit:
            break
    return out


def get_act(
    conn: sqlite3.Connection,
    urn: str | None = None,
    path: str | None = None,
    articolo: str | None = None,
) -> list[sqlite3.Row]:
    """Restituisce i chunk di un atto, identificato per `urn` o `path`, in ordine di
    inserimento (preambolo e poi articoli). Con `articolo` filtra il singolo articolo.
    Ritorna lista vuota se l'atto (o l'articolo) non esiste nell'indice.
    """
    if not urn and not path:
        raise ValueError("get_act richiede urn oppure path")
    sql = [
        "SELECT urn, tipo, numero, data, titolo, collezione, articolo, rubrica, vigente, path, testo",
        "FROM chunks WHERE",
        "urn = ?" if urn else "path = ?",
    ]
    params: list[object] = [urn or path]
    if articolo is not None:
        sql.append("AND articolo = ?")
        params.append(articolo)
    sql.append("ORDER BY rowid")
    return conn.execute("\n".join(sql), params).fetchall()


def corpus_stats(conn: sqlite3.Connection) -> tuple[int, int]:
    """Conteggi dell'indice: numero di atti distinti (per path file) e numero di chunk."""
    n_atti = conn.execute("SELECT COUNT(DISTINCT path) FROM chunks").fetchone()[0]
    n_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    return int(n_atti), int(n_chunks)
