---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - src/legal_consultant/mcp_server.py
  - src/legal_consultant/index/**
  - src/legal_consultant/update/**
  - scripts/setup.py
  - scripts/update_corpus.py
  - .mcp.json
  - prompts/**
last-verified-commit: f954aaa
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
- [x] hardening: `fts.to_match_query` sanifica l'input libero (nessun errore MATCH); test dedicati
- [x] Fase 3: package `update` (revisione, diff, reindex incrementale, stato) + `scripts/update_corpus.py`
- [x] `info_corpus` riporta freschezza del corpus (state.json o git del submodule) e disclaimer
- [x] packaging: `.mcp.json` (Claude Code) + `scripts/setup.py` (setup a un comando) + prompt MCP
- [x] disclaimer e istruzioni: `prompts/consulente-legale.md` e prompt `consulenza_legale`
- [x] test verdi (9 totali) e smoke dei tre tool + prompt su fixture
- [ ] `git submodule add` del corpus (passo manuale del manutentore) e prima indicizzazione completa
- [ ] verifica end-to-end in Claude Code e Claude Desktop sul corpus reale
- [ ] Project "Consulente Legale" in Claude Desktop con le istruzioni di `prompts/consulente-legale.md`

Stato: sviluppo del prodotto completato e verificato su indice di fixture (9 test verdi + smoke di
tool e prompt). Restano i passi che richiedono il corpus reale: l'aggiunta del submodule e la prima
indicizzazione, poi la verifica end-to-end nei due client e i casi d'uso specifici.

Domande aperte:

- Semantica della ricerca: `to_match_query` unisce i token in OR e lascia il ranking a BM25; da
  misurare sul corpus reale se per query lunghe convenga una soglia di copertura dei termini o un
  AND parziale, per non diluire la precisione.
- Trasparenza per l'utente non tecnico: il `git submodule add` iniziale resta un passo del
  manutentore (non automatizzabile senza una git write); valutare se distribuire un indice
  pre-costruito per saltare il bootstrap pesante al primo uso.

## Riconciliazione

Ultima verifica: 2026-06-30. Fase 2 committata in `f954aaa`. Sopra di essa è stato scritto, e non
ancora committato, il resto dello sviluppo del prodotto: hardening della ricerca, Fase 3
(package `update` + `update_corpus.py`), packaging (`.mcp.json`, `setup.py`, prompt) e disclaimer
(`prompts/consulente-legale.md`). Il contenuto di queste schede è quindi avanti rispetto a
`f954aaa`: dopo il commit, rilanciare `sync-context` per ri-ancorare al nuovo HEAD.
