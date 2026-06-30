"""Server MCP "legge-it": espone la ricerca normativa locale a Claude Desktop.

Tre strumenti, su transport stdio (l'unico che Claude Desktop usa per i server
locali). La ricerca e la lettura girano sull'indice SQLite FTS5 costruito da
`scripts/bootstrap_index.py`; nessun token API viene consumato qui, il ragionamento
resta a Claude Desktop. Le descrizioni dei tool sono scritte per indurre Claude a
chiamare `cerca_normativa` prima di rispondere e a citare sempre atto e articolo.

Avvio (come da voce in claude_desktop_config.json):
    uv run python -m legal_consultant.mcp_server
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .config import INDEX_PATH
from .index import fts

mcp = FastMCP("legge-it")


# --- Helper puri (testabili senza il transport MCP) -------------------------

def _citazione(row: sqlite3.Row) -> str:
    """Stringa di citazione compatta dell'atto: 'TIPO n. NUMERO del DATA'."""
    parti = [p for p in (row["tipo"], f"n. {row['numero']}" if row["numero"] else "") if p]
    testa = " ".join(parti).strip()
    return f"{testa} del {row['data']}" if row["data"] else testa


def _hit_to_dict(row: sqlite3.Row) -> dict:
    """Una riga di `search` nel formato di output di `cerca_normativa`."""
    return {
        "urn": row["urn"],
        "atto": row["titolo"],
        "citazione": _citazione(row),
        "articolo": row["articolo"] or None,
        "rubrica": row["rubrica"] or None,
        "estratto": row["estratto"],
        "vigente": row["vigente"] == "true",
        "path": row["path"],
        "score": round(float(row["score"]), 3),
    }


def _index_missing_msg() -> dict:
    return {
        "errore": "indice non disponibile",
        "dettaglio": (
            f"Nessun indice in {INDEX_PATH}. Esegui prima "
            "`uv run python scripts/bootstrap_index.py` dopo aver clonato il corpus."
        ),
    }


# --- Strumenti MCP ----------------------------------------------------------

@mcp.tool()
def cerca_normativa(query: str, solo_vigenti: bool = True, limit: int = 8) -> list[dict]:
    """Cerca nella legislazione italiana e restituisce gli estratti normativi piu
    pertinenti (ranking BM25). USA SEMPRE questo strumento prima di rispondere a una
    domanda di diritto italiano: non rispondere a memoria. Ogni risultato porta `urn`,
    `atto`, `articolo` e un `estratto`: cita sempre atto e articolo nella risposta.

    query: testo libero (concetti, parole chiave). solo_vigenti: se True esclude gli
    atti abrogati. limit: numero massimo di estratti (default 8).
    """
    if not INDEX_PATH.exists():
        return [_index_missing_msg()]
    conn = fts.connect(INDEX_PATH)
    try:
        rows = fts.search(conn, query, limit=limit, solo_vigenti=solo_vigenti)
    finally:
        conn.close()
    return [_hit_to_dict(r) for r in rows]


@mcp.tool()
def leggi_atto(urn: str = "", path: str = "", articolo: str = "") -> dict:
    """Legge il testo integrale di un atto, o di un suo singolo articolo, dall'indice.
    Identifica l'atto per `urn` (preferito, lo restituisce `cerca_normativa`) oppure per
    `path`. Con `articolo` valorizzato restituisce solo quell'articolo. Usalo per leggere
    il testo completo dopo che `cerca_normativa` ha individuato l'atto rilevante.
    """
    if not INDEX_PATH.exists():
        return _index_missing_msg()
    if not urn and not path:
        return {"errore": "richiesto urn oppure path"}
    conn = fts.connect(INDEX_PATH)
    try:
        rows = fts.get_act(
            conn, urn=urn or None, path=path or None, articolo=articolo or None
        )
    finally:
        conn.close()
    if not rows:
        return {"errore": "atto o articolo non trovato nell'indice",
                "urn": urn or None, "path": path or None, "articolo": articolo or None}

    head = rows[0]
    articoli = [
        {"articolo": r["articolo"] or None, "rubrica": r["rubrica"] or None, "testo": r["testo"]}
        for r in rows
    ]
    return {
        "urn": head["urn"],
        "atto": head["titolo"],
        "citazione": _citazione(head),
        "vigente": head["vigente"] == "true",
        "collezione": head["collezione"],
        "path": head["path"],
        "articoli": articoli,
    }


@mcp.tool()
def info_corpus() -> dict:
    """Stato del corpus indicizzato: numero di atti e di chunk, e data dell'ultima
    indicizzazione. Usalo per dire all'utente quanto e' aggiornata e ampia la base
    normativa su cui si fonda la risposta.
    """
    if not INDEX_PATH.exists():
        return _index_missing_msg()
    conn = fts.connect(INDEX_PATH)
    try:
        n_atti, n_chunks = fts.corpus_stats(conn)
    finally:
        conn.close()
    mtime = datetime.fromtimestamp(Path(INDEX_PATH).stat().st_mtime, tz=timezone.utc)
    return {
        "atti_indicizzati": n_atti,
        "chunk_indicizzati": n_chunks,
        "ultima_indicizzazione_utc": mtime.isoformat(timespec="seconds"),
        "indice": str(INDEX_PATH),
        "nota": "Aggiornamento incrementale schedulato: previsto in Fase 3 (non ancora attivo).",
    }


def main() -> None:
    mcp.run()  # transport stdio di default


if __name__ == "__main__":
    main()
