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
- [x] percorsi lunghi Windows aggirati senza admin (`config.long_path` + `core.longpaths`)
- [x] corpus reale clonato (287.813 file) e indicizzato (287.785 atti, 759.881 chunk, indice 2.4 GB)
- [x] abrogate declassate a non vigenti (collezione) e deduplica per atto+articolo nella ricerca
- [x] verifica server MCP sull'indice reale (es. "licenziamento per giusta causa" → D.Lgs. 23/2015)
- [ ] registrare il corpus come submodule per la riproducibilità del clone (productizzazione)
- [ ] uso end-to-end da chat: Claude Code (approvare `.mcp.json`) e/o Project Claude Desktop
- [ ] casi d'uso specifici concordati con l'utente sul corpus reale

Stato: prodotto completo e funzionante end-to-end sul corpus reale. La ricerca, la lettura e lo
stato girano sull'indice da 2.4 GB; il server MCP è verificato sui dati veri. Restano la
registrazione del submodule per la riproducibilità e l'uso conversazionale da un client.

Domande aperte:

- Semantica di "vigente": nel corpus il campo `vigente` è True anche per le abrogate, quindi il
  filtro esclude solo la collezione "Atti normativi abrogati (in originale)". Non garantisce la
  vigenza odierna di un atto su Normattiva: vale il disclaimer. Da valutare un segnale di vigenza
  più fine se disponibile nel corpus.
- Ranking BM25 su query concettuali: variabile (a volte l'articolo centrale di un codice non emerge
  in cima). Misurare e, se il recall non basta, valutare l'ibrido dense+sparse (ADR-003).
- Trasparenza: il `git submodule add` iniziale resta un passo del manutentore; valutare la
  distribuzione di un indice pre-costruito per saltare il bootstrap pesante al primo uso.

## Riconciliazione

Ultima verifica: 2026-06-30. Hardening, Fase 3, packaging e disclaimer committati in `bd19b1d`.
Non ancora committato: gestione percorsi lunghi Windows (`config.long_path`, `setup.py`),
declassamento delle abrogate nel parser e deduplica in `search`, più queste schede. Il corpus
reale è clonato e l'indice completo costruito; il server è verificato sui dati veri. Dopo il
commit di questo lotto, rilanciare `sync-context` per ri-ancorare al nuovo HEAD.
