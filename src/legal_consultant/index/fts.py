"""Indice full-text BM25 su SQLite FTS5.

Una sola tabella virtuale `chunks`: le colonne testuali (titolo, articolo, rubrica,
testo) sono indicizzate, i metadati sono UNINDEXED ma memorizzati per la citazione e
i filtri. Il ranking è BM25 nativo di FTS5. L'aggiornamento incrementale per file si
fa cancellando le righe con quel `path` e reinserendole.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from ..ingest.parser import ParsedAct

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
) -> list[sqlite3.Row]:
    """Ricerca BM25. `query` usa la sintassi MATCH di FTS5 (testo libero ammesso)."""
    sql = [
        "SELECT urn, tipo, numero, data, titolo, collezione, articolo, rubrica, vigente, path,",
        f"       snippet(chunks, {_COL_TESTO}, '[', ']', ' … ', 16) AS estratto,",
        "       bm25(chunks) AS score",
        "FROM chunks WHERE chunks MATCH ?",
    ]
    params: list[object] = [query]
    if solo_vigenti:
        sql.append("AND vigente = 'true'")
    sql.append("ORDER BY score LIMIT ?")
    params.append(limit)
    return conn.execute("\n".join(sql), params).fetchall()


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
