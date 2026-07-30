"""Setup a un comando del consulente legale, dopo aver clonato il repo.

Uso:
    uv run python scripts/setup.py

Tre passi: scarica il corpus (clone shallow di italia-corpus), sincronizza l'ambiente con
uv, costruisce l'indice di ricerca. Al termine il server MCP e' pronto; la registrazione
nel client (Claude Code o Claude Desktop) e' descritta in `.claude/context/deployment.md`.

Il corpus e' un clone locale ignorato da git, non un submodule: cosi' resta sempre
all'ultima versione e si aggiorna con `git pull` (scripts/update_corpus.py). Il testo dei
codici fondamentali e' gia' versionato nel repo (data/codici-extra), quindi non va scaricato.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from legal_consultant.config import CORPUS_PATH, REPO_ROOT

_CORPUS_URL = "https://github.com/ahmeabd/italia-corpus.git"


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=str(REPO_ROOT))


def _corpus_presente(corpus: Path) -> bool:
    """True solo se esiste un clone completo e valido, non una cartella qualunque.

    Un controllo di sola non-vuotezza accetterebbe anche un clone interrotto a meta'
    (per esempio da una connessione caduta durante il primo setup): la cartella
    esisterebbe gia' con dentro un `.git` parziale, un rilancio salterebbe il download
    pensando che il corpus sia pronto, e il bootstrap indicizzerebbe pochissimi file
    senza un errore chiaro. `git rev-parse HEAD` riesce solo su un repository con
    almeno un commit effettivamente estratto.
    """
    if not corpus.is_dir() or not any(corpus.iterdir()):
        return False
    try:
        subprocess.run(
            ["git", "-C", str(corpus), "rev-parse", "HEAD"],
            check=True, capture_output=True, cwd=str(REPO_ROOT),
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False
    return True


def main() -> int:
    corpus = Path(CORPUS_PATH)

    print("== 1/3 Corpus ==")
    if _corpus_presente(corpus):
        print(f"Corpus gia' presente in {corpus}, salto il download.")
    else:
        if corpus.is_dir() and any(corpus.iterdir()):
            print(f"Trovato un clone incompleto o corrotto in {corpus}, lo rimuovo e riprovo.")
            shutil.rmtree(corpus)
        # Clone shallow. -c core.longpaths=true: i nomi-file lunghi del corpus superano
        # il limite di 260 caratteri di Windows; fa usare a git le API estese, senza admin.
        _run(["git", "-c", "core.longpaths=true", "clone", "--depth", "1",
              _CORPUS_URL, str(corpus)])
        # Persiste l'impostazione nel clone, cosi' anche i pull futuri estraggono i path lunghi.
        _run(["git", "-C", str(corpus), "config", "core.longpaths", "true"])
        # Identita' locale placeholder, scoped al solo clone del corpus (mai --global):
        # il clone e' di sola lettura e non fa mai un commit, ma alcune versioni di git
        # rifiutano operazioni non banali senza un'identita' configurata. Un utente non
        # tecnico non avrebbe modo di rispondere a una richiesta di credenziali: meglio
        # non lasciare la possibilita' che si presenti. Non tocca l'identita' globale
        # dell'utente, ne' richiede un vero account.
        _run(["git", "-C", str(corpus), "config", "user.name", "legal-consultant-bot"])
        _run(["git", "-C", str(corpus), "config", "user.email", "legal-consultant@localhost"])

    print("\n== 2/4 Ambiente ==")
    _run(["uv", "sync"])

    print("\n== 3/4 Indice ==")
    _run(["uv", "run", "python", "scripts/bootstrap_index.py"])

    # Le classi di atti che il corpus di terze parti non contiene (leggi ordinarie,
    # decreti-legge vigenti, Costituzione: vedi docs/audit-completezza-corpus.md) si
    # recuperano dalla fonte ufficiale. Il recupero storico completo dura ore, quindi qui
    # se ne fa una parte a budget e il resto lo completa l'attivita' pianificata nei giorni
    # successivi: l'alternativa sarebbe un installer che sembra bloccato per mezza giornata.
    # Il recupero parte dagli anni recenti, che sono quelli che si consultano di piu'.
    print("\n== 4/4 Classi di atti mancanti dal corpus di terze parti ==")
    print("Recupero da Normattiva, a partire dagli anni recenti (circa 20 minuti).")
    print("Il resto viene completato dall'aggiornamento automatico nei giorni successivi.")
    _run(["uv", "run", "python", "scripts/fetch_normattiva.py",
          "--da", "1980", "--minuti", "20"])

    print(
        "\nSetup completato. Il server MCP 'legge-it' e' pronto.\n"
        "Claude Code: apri questo progetto e approva il server in .mcp.json.\n"
        "Claude Desktop: usa install.ps1 oppure aggiungi la voce di deployment.md a\n"
        "claude_desktop_config.json."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
