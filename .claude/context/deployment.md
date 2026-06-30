---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - scripts/**
  - src/legal_consultant/mcp_server.py
  - .mcp.json
last-verified-commit: f954aaa
---

# Deployment

> Commit, push e deploy restano operazioni manuali dell'utente. Il "deployment" qui è interamente
> locale: il server MCP gira sulla macchina e si registra in `claude_desktop_config.json`
> (configurazione a livello account, fuori dal repository). L'aggiornamento del corpus sarà uno
> script schedulato (Windows Task Scheduler), previsto in Fase 3.

## Livelli

Un solo livello: locale su desktop Windows. Nessun ambiente cloud, nessuna CI. Il corpus vive come
submodule sotto `data/italia-corpus`, l'indice SQLite FTS5 sotto `data/index/legge.sqlite` (path da
`config.py`, override via `.env`). Claude Desktop avvia il server come sottoprocesso su stdio e ne
consuma i tool; la chat passa per l'abbonamento Team, il resto non lascia la macchina.

## Comandi

Setup a un comando per l'utente finale, dopo aver clonato il repo: `uv run python scripts/setup.py`
inizializza il submodule del corpus in shallow, sincronizza l'ambiente e costruisce l'indice.
L'aggiunta iniziale del submodule (`git submodule add`) resta un passo manuale del manutentore,
eseguito una volta, perché modifica `.gitmodules`. I singoli passi a mano: `uv sync --extra dev`
per ambiente e strumenti di test; `uv run python scripts/bootstrap_index.py` per ricostruire
l'indice da zero; `uv run python scripts/query.py "<query>" [limit]` per la sanità sull'indice;
`uv run python -m legal_consultant.mcp_server` per avviare il server a mano in diagnosi (resta in
ascolto su stdio; in uso normale è il client a lanciarlo).

Aggiornamento del corpus (Fase 3): `uv run python scripts/update_corpus.py` fa il pull del
submodule, reindicizza i soli atti cambiati via `git diff` e salva lo stato in `state.json`. Si
schedula con Windows Task Scheduler (esecuzione giornaliera del comando nella cartella del
progetto) per tenere la legge aggiornata senza intervento.

## Registrazione nel client

Claude Code: la registrazione è versionata in `.mcp.json` in radice. Chi apre il progetto in Claude
Code vede il server `legge-it` proposto e lo approva una volta; il comando (`uv run python -m
legal_consultant.mcp_server`) gira con working directory sul progetto, quindi è portabile fra
macchine senza percorsi assoluti.

Claude Desktop: si aggiunge una voce alla sezione `mcpServers` del `claude_desktop_config.json`
dell'account, con il percorso assoluto del progetto.

```json
"legge-it": {
  "command": "uv",
  "args": ["--directory", "E:\\legal-consultant", "run", "python", "-m", "legal_consultant.mcp_server"]
}
```

Se il processo del client non trova `uv` sul PATH, si sostituisce `"uv"` con il percorso assoluto
dell'eseguibile. Per Claude Desktop si crea poi un Project "Consulente Legale" incollando le
istruzioni di `prompts/consulente-legale.md` (che includono il disclaimer); su Claude Code le
stesse istruzioni sono esposte dal server come prompt MCP `consulenza_legale`.

## Variabili d'ambiente e segreti

Percorsi in `.env` (`CORPUS_PATH`, `INDEX_PATH`, `STATE_PATH`), con default relativi alla radice
risolti da `config.py`. Nessuna chiave API è richiesta dal prodotto: il ragionamento è in Claude
Desktop. I valori non si committano mai.
