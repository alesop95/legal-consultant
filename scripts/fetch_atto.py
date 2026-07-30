"""Scarica un singolo atto da Normattiva data la sua URN e lo indicizza.

Uso:
    uv run python scripts/fetch_atto.py urn:nir:stato:legge:1978-05-22;194
    uv run python scripts/fetch_atto.py urn:nir:stato:legge:2017-12-22;219 --forza

Serve quando manca un atto preciso e non si vuole rilanciare un recupero massivo:
scarica il testo consolidato vigente dalla fonte ufficiale, lo converte nel Markdown con
frontmatter del corpus e reindicizza soltanto quell'atto, lasciando intatto il resto
dell'indice. Se l'atto e' gia' indicizzato non fa nulla, a meno di `--forza`, che lo
riscarica per aggiornarlo a una vigenza piu' recente.

A differenza di `fetch_codici.py`, che e' cablato sui cinque codici fondamentali, questo
comando e' generale: qualunque atto raggiungibile per URN NIR.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from legal_consultant import update
from legal_consultant.config import INDEX_PATH, STATE_PATH, SUPPL_CORPUS_PATH, CORPUS_PATH
from legal_consultant.fonte import recupero
from legal_consultant.fonte.normattiva import Client, NormattivaError
from legal_consultant.index import fts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("urn", help="URN NIR dell'atto, es. urn:nir:stato:legge:1978-05-22;194")
    ap.add_argument("--forza", action="store_true",
                    help="riscarica anche se l'atto è già indicizzato")
    args = ap.parse_args(argv)

    urn = args.urn.strip()
    if not Path(INDEX_PATH).exists():
        print(f"Indice non trovato in {INDEX_PATH}. Esegui prima scripts/bootstrap_index.py.")
        return 1

    try:
        denominazione, anno, numero = recupero.scompone_urn(urn)
    except ValueError as e:
        print(f"URN non valida: {e}")
        return 2

    conn = fts.connect(INDEX_PATH)
    try:
        gia = fts.get_act(conn, urn=urn)
        if gia and not args.forza:
            print(f"Già indicizzato: {urn}")
            print(f"  {gia[0]['tipo']} n. {gia[0]['numero']} del {gia[0]['data']} — "
                  f"{len(gia)} chunk, collezione '{gia[0]['collezione']}'")
            print("  Usa --forza per riscaricarlo alla vigenza odierna.")
            return 0

        print(f"Recupero {denominazione} n. {numero} del {anno} da Normattiva...")
        client = Client()
        try:
            scritti, errori = recupero.recupera_urn(client, urn, SUPPL_CORPUS_PATH)
        except NormattivaError as e:
            print(f"ERRORE: {e}")
            return 3

        for e in errori:
            print(f"  avviso: {e}")
        if not scritti:
            print("Nessun atto scritto: la fonte non ha restituito l'atto richiesto.")
            return 4

        n = update.reindex_paths(conn, SUPPL_CORPUS_PATH, scritti, [])
        righe = fts.get_act(conn, urn=urn)
        articoli = sorted({r["articolo"] for r in righe if r["articolo"]})
        print(f"Indicizzato: {scritti[0]} — {n} chunk, {len(articoli)} articoli.")
        if righe:
            print(f"  {righe[0]['titolo'][:100]}")

        n_atti, n_chunks = fts.corpus_stats(conn)
        commit, data = update.corpus_revision(CORPUS_PATH)
        update.write_state(STATE_PATH, commit, data, n_atti, n_chunks)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
