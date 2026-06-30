---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - scripts/**
  - src/legal_consultant/mcp_server.py
last-verified-commit: 6111cd3
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

Ambiente: `uv sync --extra dev` materializza runtime e strumenti di test. Prima indicizzazione del
corpus, dopo aver aggiunto il submodule: `uv run python scripts/bootstrap_index.py` (ricostruisce
l'indice da zero). Sanità manuale sull'indice: `uv run python scripts/query.py "<query>" [limit]`.
Avvio del server MCP a mano, per diagnosi: `uv run python -m legal_consultant.mcp_server` (resta in
ascolto su stdio; in uso normale è Claude Desktop a lanciarlo). L'aggiornamento incrementale
(`update_corpus.py`, pull + reindex) è di Fase 3 e non esiste ancora.

## Registrazione in Claude Desktop

Si aggiunge una voce alla sezione `mcpServers` del `claude_desktop_config.json` dell'account. Il
comando avvia il server nella cartella del progetto tramite `uv`.

```json
"legge-it": {
  "command": "uv",
  "args": ["--directory", "E:\\legal-consultant", "run", "python", "-m", "legal_consultant.mcp_server"]
}
```

Se il processo di Claude Desktop non trova `uv` sul PATH, si sostituisce `"uv"` con il percorso
assoluto dell'eseguibile. Dopo la registrazione si crea un Project "Consulente Legale" con
istruzioni custom (usa sempre i tool `legge-it`, cita atto e articolo con l'URN, dichiara quando
l'informazione non è nel corpus, includi il disclaimer), come da HANDOFF sezione 5.4.

## Variabili d'ambiente e segreti

Percorsi in `.env` (`CORPUS_PATH`, `INDEX_PATH`, `STATE_PATH`), con default relativi alla radice
risolti da `config.py`. Nessuna chiave API è richiesta dal prodotto: il ragionamento è in Claude
Desktop. I valori non si committano mai.
