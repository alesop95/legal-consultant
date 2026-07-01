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

import subprocess
import sys
from pathlib import Path

from legal_consultant.config import CORPUS_PATH, REPO_ROOT

_CORPUS_URL = "https://github.com/ahmeabd/italia-corpus.git"


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=str(REPO_ROOT))


def _corpus_presente(corpus: Path) -> bool:
    return corpus.is_dir() and any(corpus.iterdir())


def main() -> int:
    corpus = Path(CORPUS_PATH)

    print("== 1/3 Corpus ==")
    if _corpus_presente(corpus):
        print(f"Corpus gia' presente in {corpus}, salto il download.")
    else:
        # Clone shallow. -c core.longpaths=true: i nomi-file lunghi del corpus superano
        # il limite di 260 caratteri di Windows; fa usare a git le API estese, senza admin.
        _run(["git", "-c", "core.longpaths=true", "clone", "--depth", "1",
              _CORPUS_URL, str(corpus)])
        # Persiste l'impostazione nel clone, cosi' anche i pull futuri estraggono i path lunghi.
        _run(["git", "-C", str(corpus), "config", "core.longpaths", "true"])

    print("\n== 2/3 Ambiente ==")
    _run(["uv", "sync"])

    print("\n== 3/3 Indice ==")
    _run(["uv", "run", "python", "scripts/bootstrap_index.py"])

    print(
        "\nSetup completato. Il server MCP 'legge-it' e' pronto.\n"
        "Claude Code: apri questo progetto e approva il server in .mcp.json.\n"
        "Claude Desktop: usa install.ps1 oppure aggiungi la voce di deployment.md a\n"
        "claude_desktop_config.json."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
