---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - scripts/**
last-verified-commit: 1e4c79b
---

# Deployment

> Popolare leggendo la configurazione reale di infrastruttura e CI. Commit, push e deploy restano
> operazioni manuali dell'utente.
>
> Stato: scheletro. Il "deployment" qui è locale: il server MCP gira sulla macchina e si registra
> in `claude_desktop_config.json` (configurazione a livello account, fuori dal repository).
> L'aggiornamento del corpus è uno script schedulato (Windows Task Scheduler). Da popolare in
> Fase 2/3.

## Livelli

<locale-desktop; nessun ambiente cloud — da dettagliare>

## Comandi

<bootstrap_index.py per la prima indicizzazione; update_corpus.py per pull+reindex; avvio del
server MCP — da popolare leggendo gli script reali>

## Variabili d'ambiente e segreti

<percorsi in .env (CORPUS_PATH, INDEX_PATH, STATE_PATH); nessuna chiave API richiesta dal
prodotto — il ragionamento è in Claude Desktop. I valori non si committano mai.>
