---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - scripts/**
  - src/legal_consultant/mcp_server.py
  - .mcp.json
last-verified-commit: bae3b34
---

# Deployment

> Commit, push e deploy restano operazioni manuali dell'utente. Il "deployment" qui è interamente locale: il server MCP gira sulla macchina e si registra in `claude_desktop_config.json` (configurazione a livello account, fuori dal repository). L'aggiornamento del corpus sarà uno script schedulato (Windows Task Scheduler), previsto in Fase 3.

## Livelli

Un solo livello: locale su desktop Windows. Nessun ambiente cloud, nessuna CI. Il corpus vive come clone locale ignorato da git (non un submodule) sotto `data/italia-corpus`, l'indice SQLite FTS5 sotto `data/index/legge.sqlite` (path da `config.py`, override via `.env`). Claude Desktop avvia il server come sottoprocesso su stdio e ne consuma i tool; la chat passa per l'abbonamento Team, il resto non lascia la macchina.

## Comandi

Setup a un comando per l'utente finale, dopo aver scaricato il progetto (anche senza git, via Download ZIP da GitHub): `uv run python scripts/setup.py` clona il corpus in shallow, sincronizza l'ambiente e costruisce l'indice. Verifica con `git rev-parse HEAD` che un clone preesistente sia davvero completo, rimuovendo e rifacendo quelli interrotti a metà, e configura un'identità git placeholder scoped al solo clone del corpus (mai globale), rete di sicurezza contro un'eventuale richiesta di credenziali su un clone HTTPS anonimo di sola lettura. Su Windows gestisce da sé i nomi-file lunghi del corpus (oltre 260 caratteri): clona con `core.longpaths=true` e lo persiste nel clone, senza chiedere privilegi di amministratore né modifiche al registro. I singoli passi a mano: `uv sync --extra dev` per ambiente e strumenti di test; `uv run python scripts/bootstrap_index.py` per ricostruire l'indice da zero; `uv run python scripts/query.py "<query>" [limit]` per la sanità sull'indice; `uv run python -m legal_consultant.mcp_server` per avviare il server a mano in diagnosi (resta in ascolto su stdio; in uso normale è il client a lanciarlo).

Codici fondamentali: `uv run python scripts/fetch_codici.py` scarica da Normattiva (via `uvx normattiva2md`) il testo integrale di codice civile, penale, procedura civile, navigazione e penali militari, assenti come articolato in italia-corpus, e li salva in `data/codici-extra` (tracciato, indicizzato dal bootstrap). Si rilancia per aggiornarli, seguito da un reindex.

Aggiornamento del corpus (Fase 3): `uv run python scripts/update_corpus.py` allinea il clone locale del corpus all'ultimo commit del remoto con `fetch --depth 1` + `reset --hard @{u}` (non un `pull --ff-only`, che fallirebbe sempre per via di path del corpus che collidono per maiuscole/minuscole su un filesystem case-insensitive), reindicizza i soli atti cambiati via `git diff` e salva lo stato in `state.json`. `scripts/auto_update.py` orchestra la stessa logica senza presidio (corpus ad ogni giro, `fetch_codici.py` al più una volta alla settimana), registrato da `install.ps1` come attività pianificata di Windows (`ConsulenteLegale-Aggiornamento`, giornaliera alle 6:00, senza privilegi di amministratore) con fallback a un avviso non bloccante se la registrazione fallisse.

## Registrazione nel client

Claude Code: la registrazione è versionata in `.mcp.json` in radice. Chi apre il progetto in Claude Code vede il server `legge-it` proposto e lo approva una volta; il comando (`uv run python -m legal_consultant.mcp_server`) gira con working directory sul progetto, quindi è portabile fra macchine senza percorsi assoluti.

Claude Desktop: si aggiunge una voce alla sezione `mcpServers` del `claude_desktop_config.json` dell'account, con il percorso assoluto del progetto.

```json
"legge-it": {
  "command": "uv",
  "args": ["--directory", "E:\\legal-consultant", "run", "python", "-m", "legal_consultant.mcp_server"]
}
```

Se il processo del client non trova `uv` sul PATH, si sostituisce `"uv"` con il percorso assoluto dell'eseguibile. Per Claude Desktop si crea poi un Project "Consulente Legale" incollando le istruzioni di `prompts/consulente-legale.md` (che includono il disclaimer); su Claude Code le stesse istruzioni sono esposte dal server come prompt MCP `consulenza_legale`.

## Variabili d'ambiente e segreti

Percorsi in `.env` (`CORPUS_PATH`, `INDEX_PATH`, `STATE_PATH`), con default relativi alla radice risolti da `config.py`. Nessuna chiave API è richiesta dal prodotto: il ragionamento è in Claude Desktop. I valori non si committano mai.
