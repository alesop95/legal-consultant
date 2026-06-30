"""Setup a un comando del consulente legale, dopo aver clonato il repo.

Uso:
    uv run python scripts/setup.py

Tre passi: scarica il corpus (inizializza il submodule git in shallow), sincronizza
l'ambiente con uv, costruisce l'indice di ricerca. Al termine il server MCP e' pronto;
la registrazione nel client (Claude Code o Claude Desktop) e' descritta in
`.claude/context/deployment.md`.

Pensato per essere l'unico comando che un utente non tecnico deve lanciare. Non esegue
operazioni git che modificano la storia del repo: l'aggiunta iniziale del submodule
(`git submodule add`) resta un passo del manutentore, qui si assume gia' presente in
`.gitmodules`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from legal_consultant.config import CORPUS_PATH, REPO_ROOT


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=str(REPO_ROOT))


def _corpus_presente(corpus: Path) -> bool:
    return corpus.is_dir() and any(corpus.iterdir())


def main() -> int:
    corpus = Path(CORPUS_PATH)
    gitmodules = REPO_ROOT / ".gitmodules"

    print("== 1/3 Corpus ==")
    if _corpus_presente(corpus):
        print(f"Corpus gia' presente in {corpus}, salto il download.")
    elif gitmodules.is_file():
        _run(["git", "submodule", "update", "--init", "--depth", "1", "data/italia-corpus"])
    else:
        print(
            "Corpus non configurato come submodule (.gitmodules assente). Il manutentore "
            "deve eseguirlo una volta:\n"
            "  git submodule add --depth 1 "
            "https://github.com/ahmeabd/italia-corpus.git data/italia-corpus"
        )
        return 1

    print("\n== 2/3 Ambiente ==")
    _run(["uv", "sync"])

    print("\n== 3/3 Indice ==")
    _run(["uv", "run", "python", "scripts/bootstrap_index.py"])

    print(
        "\nSetup completato. Il server MCP 'legge-it' e' pronto.\n"
        "Claude Code: apri questo progetto e approva il server in .mcp.json.\n"
        "Claude Desktop: aggiungi la voce di deployment.md a claude_desktop_config.json."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
