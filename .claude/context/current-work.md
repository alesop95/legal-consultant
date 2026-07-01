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
last-verified-commit: 889f843
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
- [x] registrati in Claude Desktop (claude_desktop_config.json) e verificato end-to-end via screenshot
- [x] codici fondamentali (civile, penale, proc. civile, navigazione, penali militari) integrati da
      Normattiva via `fetch_codici.py` in `data/codici-extra`; art. 2043 c.c./157 c.p./112 c.p.c. trovati
- [x] prova end-to-end in Claude Desktop (Sonnet 5): con prompt "solo legge-it, no web" cita gli
      artt. 157-161-bis c.p. con URN dal corpus; `info_corpus` reso istantaneo (legge da state.json)
- [x] corpus come clone locale ignorato (non submodule), aggiornabile con `git pull`
- [x] installer "un clic" (`install.cmd`/`install.ps1`): git+uv se mancano, longpaths, setup, registrazione
- [x] Fase A benchmark retrieval (`scripts/benchmark_retrieval.py`) + pesatura BM25 rubrica/titolo
      adottata (recall@8 15/26 → 19/26)
- [ ] risolvere il drift di ranking residuo (vedi domande aperte): concetti non nella rubrica e
      rubriche omonime tra codici (es. "diffamazione" → art. 227 c.p. militari invece di 595 c.p.)
- [ ] Fase B: Project "Consulente Legale" + batteria di domande dal vivo in Claude Desktop
- [ ] prova dell'installer su una situazione pulita (Fase C); prova aggiornamento (Fase D)

Stato: prodotto completo e verificato end-to-end in Claude Desktop, con i codici fondamentali,
l'installer e il ranking pesato. Fase A conclusa con risultato accettabile ma con un drift di
ranking residuo da risolvere. Restano le Fasi B/C/D del piano di test.

Domande aperte:

- Semantica di "vigente": nel corpus il campo `vigente` è True anche per le abrogate, quindi il
  filtro esclude solo la collezione "Atti normativi abrogati (in originale)". Non garantisce la
  vigenza odierna di un atto su Normattiva: vale il disclaimer. I codici integrati sono scaricati
  alla vigenza odierna ma vanno rinfrescati con `fetch_codici.py`.
- Drift di ranking (DA RISOLVERE, Fase A accettabile ma non ottimale): misurato con
  `scripts/benchmark_retrieval.py`. Con la pesatura rubrica/titolo recall@8 = 19/26. Due residui:
  (a) concetti la cui parola non è nella rubrica non emergono (usura, danno ambientale, doveri
  verso i figli); (b) rubriche omonime tra codici fanno vincere quello sbagliato (es. "diffamazione"
  → art. 227 codici penali militari invece di 595 c.p.). Leve candidate: preferire i codici generali
  (civile/penale) su quelli speciali a parità di rubrica; affinare i pesi; in ultima istanza ibrido
  con embedding leggero CPU (ADR-003, Fase 4). Nel prodotto è mitigato da conoscenza + `leggi_atto`.
- Trasparenza: il `git submodule add` iniziale resta un passo del manutentore; valutare la
  distribuzione di un indice pre-costruito per saltare il bootstrap pesante al primo uso.

## Riconciliazione

Ultima verifica: 2026-07-01. Tutto committato fino a `889f843` (ranking pesato, README, installer,
fix info_corpus, corpus come clone) e schede ri-ancorate a `889f843`: contenuto allineato a HEAD,
nessun drift documentale. Aperto solo il drift di ranking (vedi domande aperte), da risolvere.
