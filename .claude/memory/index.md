# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:         main
Commit di riferimento: 6111cd3
Data snapshot:         2026-06-30
```

## Stato di verifica delle schede

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | 6111cd3 | aggiornata; contenuto Fase 2 avanti (codice da committare) |
| design-and-security.md | 6111cd3 | popolata da codice Fase 1+2; contenuto Fase 2 avanti |
| deployment.md | 6111cd3 | popolata (comandi + registrazione Claude Desktop) |
| dev-testing.md | 6111cd3 | popolata (pytest, fixture, 5 test) |
| current-work.md | 6111cd3 | aggiornata (Fase 2 in lavorazione) |
| roadmap.md | 6111cd3 | aggiornata (Fase 1 fatta, Fase 2 attiva) |

## Punto di ripresa

Fase 1 committata in `6111cd3` (parser MD+YAML, indice FTS5, bootstrap, query, test su fixture).
Fase 2 implementata e testata su fixture ma **non ancora committata**: server MCP "legge-it"
(`src/legal_consultant/mcp_server.py`, FastMCP su stdio) con i tool `cerca_normativa`, `leggi_atto`,
`info_corpus`, più `fts.get_act` / `fts.corpus_stats` come layer dati e i relativi test (5 verdi
via `uv run pytest`). Schede di contesto ri-ancorate a `6111cd3` e popolate col contenuto Fase 2.

Il contenuto Fase 2 delle schede è avanti rispetto a `6111cd3`: dopo il commit della Fase 2,
rilanciare `sync-context` per ri-ancorare i `last-verified-commit` al nuovo HEAD.

Prossime azioni concrete, in ordine. Primo: committare la Fase 2 (codice del server + schede),
operazione manuale dell'utente. Secondo: clonare il corpus come **submodule shallow** sotto
`data/italia-corpus` (`git submodule add --depth 1
https://github.com/ahmeabd/italia-corpus.git data/italia-corpus`), poi `uv run python
scripts/bootstrap_index.py` per la prima indicizzazione completa e una query di sanità sul reale
(clone pesante, ~831 MB lato git + storia giornaliera, preferire shallow). Terzo: registrare il
server in `claude_desktop_config.json` e creare il Project "Consulente Legale" con istruzioni +
disclaimer, poi verifica end-to-end in Claude Desktop.
