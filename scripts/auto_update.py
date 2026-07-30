"""Aggiornamento automatico non presidiato: corpus principale e codici fondamentali.

Uso:
    uv run python scripts/auto_update.py

Pensato per essere lanciato da un'attivita' pianificata di Windows (registrata da
`install.ps1`), senza che l'utente debba mai lanciarlo o guardarlo. Logga l'esito su file
invece che a schermo e non solleva mai: un errore di rete o una fonte irraggiungibile non
deve far fallire l'attivita' pianificata ne' mostrare popup, il giro successivo ritenta da
solo. Ogni fase (corpus, codici) e' indipendente: se una fallisce, l'altra procede comunque.

Il corpus principale si aggiorna a ogni lancio (pensato per un trigger giornaliero). I
codici fondamentali cambiano molto raramente (sono i grandi codici storici, non le leggi
ordinarie) e il loro rinfresco chiama un servizio esterno (Normattiva) e uno strumento di
terze parti: per non interrogarli inutilmente ogni giorno, si aggiornano al piu' una volta
alla settimana, tracciato in un marcatore locale.
"""

from __future__ import annotations

import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

from legal_consultant import update
from legal_consultant.config import CORPUS_PATH, EXTRA_CORPUS_PATH, INDEX_PATH, REPO_ROOT, STATE_PATH
from legal_consultant.index import fts

LOG_PATH = Path(REPO_ROOT) / "data" / "index" / "auto_update.log"
_CODICI_MARKER = Path(REPO_ROOT) / "data" / "index" / "last_codici_fetch.txt"
_CODICI_INTERVAL_DAYS = 7
# Minuti concessi a ogni giro per il recupero storico delle classi mancanti. Tenuto basso
# perche' l'attivita' e' pianificata di notte ma la macchina di uno studio legale puo'
# essere accesa e in uso: si preferisce convergere in qualche giorno senza mai occupare la
# rete per ore di seguito.
_SUPPL_BUDGET_MINUTI = 30


def _log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()}  {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _refresh_state() -> None:
    """Ricalcola e salva atti/chunk correnti, usando commit/data del corpus principale."""
    commit, date = update.corpus_revision(CORPUS_PATH)
    conn = fts.connect(INDEX_PATH)
    try:
        n_atti, n_chunks = fts.corpus_stats(conn)
    finally:
        conn.close()
    update.write_state(STATE_PATH, commit, date, n_atti, n_chunks)


def _update_corpus() -> None:
    corpus = Path(CORPUS_PATH)
    if not corpus.is_dir() or not Path(INDEX_PATH).exists():
        _log("corpus/indice non ancora pronti (primo setup non completato?), salto.")
        return
    old_commit, _ = update.corpus_revision(corpus)
    if old_commit is None:
        _log("corpus non e' un repository git valido, salto l'aggiornamento incrementale.")
        return
    update.pull(corpus)
    new_commit, _ = update.corpus_revision(corpus)
    if new_commit == old_commit:
        _log(f"corpus gia' aggiornato (commit {old_commit[:8]}).")
        return
    conn = fts.connect(INDEX_PATH)
    try:
        changed, deleted = update.changed_files(corpus, old_commit, new_commit)
        n = update.reindex_paths(conn, corpus, changed, deleted)
    finally:
        conn.close()
    _log(f"corpus {old_commit[:8]} -> {new_commit[:8]}: {len(changed)} atti aggiornati, "
         f"{len(deleted)} rimossi, {n} chunk reinseriti.")


def _should_fetch_codici() -> bool:
    if not _CODICI_MARKER.exists():
        return True
    try:
        last = datetime.fromisoformat(_CODICI_MARKER.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return True
    return datetime.now(timezone.utc) - last >= timedelta(days=_CODICI_INTERVAL_DAYS)


def _update_codici() -> None:
    if not Path(INDEX_PATH).exists():
        _log("indice non ancora pronto, salto l'aggiornamento dei codici fondamentali.")
        return
    if not _should_fetch_codici():
        _log("codici fondamentali gia' rinfrescati di recente (< 7 giorni), salto.")
        return

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import fetch_codici  # script gemello in scripts/, non un pacchetto

    rc = fetch_codici.main()
    _log(f"fetch_codici.py completato (codice di uscita {rc}).")

    rel_paths = [f"Codici/{c['slug']}.md" for c in fetch_codici.CODICI]
    conn = fts.connect(INDEX_PATH)
    try:
        n = update.reindex_paths(conn, EXTRA_CORPUS_PATH, rel_paths, [])
    finally:
        conn.close()
    _log(f"codici fondamentali reindicizzati: {n} chunk.")

    _CODICI_MARKER.parent.mkdir(parents=True, exist_ok=True)
    _CODICI_MARKER.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")


def _update_suppl() -> None:
    """Rinfresca la collezione supplementare recuperata da Normattiva.

    Si limita all'anno corrente e al precedente, che è dove compaiono gli atti nuovi:
    sono due richieste di export invece di centosessanta, quindi si può fare ogni giorno
    senza pesare sulla fonte. Il recupero storico completo si lancia a mano una volta con
    `scripts/fetch_normattiva.py` senza `--da`.
    """
    if not Path(INDEX_PATH).exists():
        _log("indice non ancora pronto, salto il rinfresco della collezione supplementare.")
        return

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import fetch_normattiva  # script gemello in scripts/, non un pacchetto

    anno_da = datetime.now(timezone.utc).year - 1
    rc = fetch_normattiva.main(["--da", str(anno_da)])
    _log(f"fetch_normattiva.py --da {anno_da} completato (codice di uscita {rc}).")

    # Recupero storico a budget: il primo popolamento completo richiede ore e l'installer
    # ne fa solo una parte, quindi ogni giro ne completa un altro pezzo finche' non resta
    # nulla. Quando le lacune sono chiuse questa chiamata costa solo l'enumerazione.
    rc = fetch_normattiva.main(["--minuti", str(_SUPPL_BUDGET_MINUTI)])
    _log(f"recupero storico a budget completato (codice di uscita {rc}).")


def _controllo_completezza() -> None:
    """Registra nel log l'esito del controllo di completezza.

    Non corregge e non fallisce: serve perché una regressione della copertura resti
    scritta da qualche parte invece di restare invisibile, che è esattamente il difetto
    da cui è nata questa parte del progetto.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_completezza

    rc = check_completezza.main(["--quiet"])
    if rc == 0:
        _log("controllo di completezza: corpus completo.")
    elif rc == 1:
        _log("ATTENZIONE, controllo di completezza: il corpus ha lacune. "
             "Lancia `uv run python scripts/check_completezza.py` per il dettaglio.")
    else:
        _log("controllo di completezza non eseguibile in questo giro.")


def main() -> int:
    _log("=== avvio aggiornamento automatico ===")
    for fase, fn in (
        ("corpus", _update_corpus),
        ("codici", _update_codici),
        ("supplementare", _update_suppl),
        ("completezza", _controllo_completezza),
    ):
        try:
            fn()
        except Exception:  # noqa: BLE001 - non deve mai far fallire l'attivita' pianificata
            _log(f"ERRORE nella fase '{fase}':\n{traceback.format_exc()}")
    try:
        _refresh_state()
    except Exception:  # noqa: BLE001
        _log(f"ERRORE nel salvataggio dello stato finale:\n{traceback.format_exc()}")
    _log("=== fine aggiornamento automatico ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
