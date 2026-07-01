"""Scarica da Normattiva i codici fondamentali mancanti e li salva nella collezione
supplementare locale, con il frontmatter nello schema del progetto.

Uso:
    uv run python scripts/fetch_codici.py

I vecchi codici emanati con Regio Decreto (civile, penale, procedura civile,
navigazione, penali militari) in italia-corpus sono presenti solo come decreto di
approvazione, senza l'articolato. Qui se ne scarica il testo integrale e vigente dalla
fonte ufficiale Normattiva (pubblico dominio, art. 5 L. 633/1941) tramite il convertitore
`normattiva2md` (MIT), eseguito con `uvx` senza aggiungerlo alle dipendenze del prodotto.
L'output va in `EXTRA_CORPUS_PATH` ed è indicizzato dal bootstrap insieme al submodule.

Strumento per il manutentore: i file generati si committano, così l'utente finale li ha
senza dover rifare il download.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import frontmatter

from legal_consultant.config import EXTRA_CORPUS_PATH

# Metadati ufficiali (presi dai decreti di approvazione del corpus) più l'URN con cui
# Normattiva risolve il testo consolidato vigente.
CODICI = [
    {"slug": "codice-civile", "tipo": "REGIO DECRETO", "numero": "262",
     "data": "1942-03-16", "titolo": "Codice civile. (042U0262)",
     "urn": "urn:nir:stato:regio.decreto:1942-03-16;262", "cr": "042U0262"},
    {"slug": "codice-penale", "tipo": "REGIO DECRETO", "numero": "1398",
     "data": "1930-10-19", "titolo": "Codice penale. (030U1398)",
     "urn": "urn:nir:stato:regio.decreto:1930-10-19;1398", "cr": "030U1398"},
    {"slug": "codice-procedura-civile", "tipo": "REGIO DECRETO", "numero": "1443",
     "data": "1940-10-28", "titolo": "Codice di procedura civile. (040U1443)",
     "urn": "urn:nir:stato:regio.decreto:1940-10-28;1443", "cr": "040U1443"},
    {"slug": "codice-navigazione", "tipo": "REGIO DECRETO", "numero": "327",
     "data": "1942-03-30", "titolo": "Codice della navigazione. (042U0327)",
     "urn": "urn:nir:stato:regio.decreto:1942-03-30;327", "cr": "042U0327"},
    {"slug": "codici-penali-militari", "tipo": "REGIO DECRETO", "numero": "303",
     "data": "1941-02-20", "titolo": "Codici penali militari di pace e di guerra (041U0303)",
     "urn": "urn:nir:stato:regio.decreto:1941-02-20;303", "cr": "041U0303"},
]


def _url(urn: str) -> str:
    return f"https://www.normattiva.it/uri-res/N2Ls?{urn}"


def _frontmatter(c: dict) -> str:
    return (
        "---\n"
        f"tipo: {c['tipo']}\n"
        f"numero: {c['numero']}\n"
        f"data: {c['data']}\n"
        f"titolo: \"{c['titolo']}\"\n"
        f"urn: {c['urn']}\n"
        f"codice_redazionale: {c['cr']}\n"
        "vigente: true\n"
        "---\n"
    )


def main() -> int:
    outdir = Path(EXTRA_CORPUS_PATH) / "Codici"
    outdir.mkdir(parents=True, exist_ok=True)
    errori = 0
    for c in CODICI:
        print(f"== {c['titolo']} ==")
        try:
            with tempfile.TemporaryDirectory() as td:
                raw = Path(td) / "raw.md"
                subprocess.run(
                    ["uvx", "normattiva2md", _url(c["urn"]), str(raw)],
                    check=True,
                )
                body = frontmatter.load(str(raw)).content
        except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            errori += 1
            print(f"  ERRORE: download/conversione fallita: {e}")
            continue
        dest = outdir / f"{c['slug']}.md"
        dest.write_text(_frontmatter(c) + "\n" + body, encoding="utf-8")
        print(f"  salvato {dest.name} ({len(body)} caratteri)")
    print(f"Fatto: {len(CODICI) - errori}/{len(CODICI)} codici scaricati in {outdir}.")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
