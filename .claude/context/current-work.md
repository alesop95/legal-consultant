---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - src/legal_consultant/mcp_server.py
  - src/legal_consultant/index/**
last-verified-commit: 6111cd3
stato: in lavorazione
---

# Lavoro in corso

> La fonte di verità su cosa è fatto resta `memory/index.md` e il work-log, non le spunte di
> questo file. Ogni feature si descrive con lo schema fisso sotto, così il lavoro pendente è
> leggibile senza ricostruire il contesto da capo.

## Feature: Fase 2 — Server MCP "legge-it"

Cosa fa: espone la ricerca normativa locale a Claude Desktop come server MCP su transport stdio,
con tre tool — `cerca_normativa` (ricerca BM25 → estratti citabili), `leggi_atto` (testo integrale
di un atto o di un suo articolo) e `info_corpus` (stato dell'indice). Le descrizioni dei tool
inducono Claude a cercare prima di rispondere e a citare sempre atto e articolo.

File creati:

```
src/legal_consultant/mcp_server.py           FastMCP: cerca_normativa, leggi_atto, info_corpus (stdio)
```

File modificati:

```
src/legal_consultant/index/fts.py            + get_act, + corpus_stats (layer dati dei tool)
pyproject.toml                               + dipendenza mcp>=1.2
tests/test_pipeline.py                       + test get_act e corpus_stats
.claude/context/STACK.md, deployment.md, design-and-security.md, dev-testing.md  contenuto Fase 2
```

Definition of done:

- [x] server `FastMCP("legge-it")` su transport stdio, avviabile con `python -m legal_consultant.mcp_server`
- [x] `cerca_normativa`, `leggi_atto`, `info_corpus` con descrizioni orientate alla citazione
- [x] layer dati `fts.get_act` / `fts.corpus_stats` e degrado con grazia se l'indice manca
- [x] test verdi (5: parser, BM25, vigenti, get_act, corpus_stats) e smoke dei tre tool su fixture
- [ ] registrazione del server in `claude_desktop_config.json` (passo manuale dell'utente)
- [ ] Project "Consulente Legale" in Claude Desktop con istruzioni custom + disclaimer
- [ ] verifica end-to-end in Claude Desktop sul corpus reale (richiede prima il bootstrap)

Stato: codice del server implementato e verificato su indice di fixture (5 test verdi + smoke dei
tre tool). Restano la registrazione in Claude Desktop e la verifica end-to-end, che presuppone il
clone del corpus e la prima indicizzazione completa (passo pesante ancora in sospeso dalla Fase 1).

Domande aperte:

- Sintassi MATCH di FTS5: una `query` con caratteri speciali della sintassi FTS5 (virgolette, `*`,
  `NEAR`) può sollevare un errore SQL invece di trattarli come testo. Da valutare se sanificare la
  query nel tool `cerca_normativa` o documentare il comportamento; misurare sul corpus reale.
- `info_corpus` riporta la data dell'ultima indicizzazione dal mtime dell'indice; la data e il
  commit dell'ultimo aggiornamento del corpus arriveranno con lo `state.json` di Fase 3.

## Riconciliazione

Ultima verifica: 2026-06-30. Fase 1 committata in `6111cd3`; i `last-verified-commit` delle schede
sono stati ri-ancorati da `1e4c79b` a `6111cd3`. Il codice della Fase 2 (server MCP + `get_act` /
`corpus_stats`) è scritto e testato su fixture ma non ancora committato: il contenuto di queste
schede è quindi avanti rispetto a `6111cd3` finché non si committa e si rilancia `sync-context`
per ri-ancorare al nuovo HEAD.
