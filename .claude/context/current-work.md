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
- [x] affinamento del ranking (non ancora committato): filtro stopword italiane in
      `to_match_query`, `_rubrica_bonus` (corrispondenza rubrica-domanda) e
      `_CODICE_GENERALE_BONUS` (spareggio sui codici generali) in `fts.search`, sovra-campionamento
      a 50x (recall@1 10→13/26, recall@5 15→19/26; vedi domande aperte per il residuo)
- [ ] Fase B: Project "Consulente Legale" + batteria di domande dal vivo in Claude Desktop
- [ ] prova dell'installer su una situazione pulita (Fase C); prova aggiornamento (Fase D)

Stato: prodotto completo e verificato end-to-end in Claude Desktop, con i codici fondamentali,
l'installer e il ranking pesato e affinato (affinamento non ancora committato). Fase A conclusa;
il drift di ranking è stato analizzato a fondo e in parte risolto, col residuo isolato in tre
cause distinte (vedi domande aperte), tutte strutturali al solo BM25. Restano le Fasi B/C/D del
piano di test.

Domande aperte:

- Semantica di "vigente": nel corpus il campo `vigente` è True anche per le abrogate, quindi il
  filtro esclude solo la collezione "Atti normativi abrogati (in originale)". Non garantisce la
  vigenza odierna di un atto su Normattiva: vale il disclaimer. I codici integrati sono scaricati
  alla vigenza odierna ma vanno rinfrescati con `fetch_codici.py`.
- Drift di ranking (AFFINATO, non ancora committato): in `fts.py` aggiunti il filtro delle
  stopword italiane in `to_match_query` (senza, "di"/"nel" da soli abbinavano centinaia di
  migliaia di righe e diluivano il campione), `_rubrica_bonus` (premia le rubriche quasi
  interamente coperte dalle parole di contenuto della domanda, es. "Furto" su "furto") e
  `_CODICE_GENERALE_BONUS` (spareggio sui tre codici generali quando due codici condividono la
  stessa rubrica: "diffamazione" ora risolve l'art. 595 c.p. e non più l'art. 227 dei codici
  penali militari). Il sovra-campionamento di `search` è salito a 50x il limite, perché la
  normalizzazione per lunghezza di BM25 può relegare l'articolo giusto ben oltre la finestra di
  ricalcolo se il suo testo è lungo (es. "usura", art. 644 c.p., era 77° su 472 corrispondenze
  grezze). Misurato su `scripts/benchmark_retrieval.py`: recall@1 10→13/26, recall@5 15→19/26,
  recall@8 invariato a 19/26 ma con risultati molto più in alto in classifica. Il residuo non è
  più un'unica causa generica ma tre isolate e diverse: rubriche nel corpus genuinamente
  scollegate dal contenuto sostanziale dell'articolo (art. 633 c.p.c. sul decreto ingiuntivo ha
  rubrica "Condizioni di ammissibilità", art. 128 codice del consumo sulla garanzia di conformità
  ha rubrica "Ambito di applicazione e definizioni"); variazione di lemma non colta dal matching
  per token esatto ("concorso" nella domanda contro "concorrono" nella rubrica dell'art. 110 c.p.);
  un caso di diluizione estrema oltre ogni sovra-campionamento ragionevole (art. 2087 c.c., 458°
  su quasi 79.000 corrispondenze grezze per "lavoro"/"datore"). Tutte e tre richiedono l'ibrido con
  embedding leggero CPU (ADR-003, Fase 4): nessuna ulteriore leva lessicale su BM25 le risolve. Nel
  prodotto il residuo resta mitigato da conoscenza del modello + `leggi_atto`.
- Trasparenza: il `git submodule add` iniziale resta un passo del manutentore; valutare la
  distribuzione di un indice pre-costruito per saltare il bootstrap pesante al primo uso.

## Riconciliazione

Ultima verifica: 2026-07-02. Codice committato fino a `09b5ec1`; l'affinamento del ranking
descritto sopra (`fts.py`, `scripts/benchmark_retrieval.py`, `tests/test_pipeline.py`, 12 test
verdi) non è ancora committato. Questa scheda è aggiornata in anticipo sul commit: dopo che
l'utente esegue `git add`/`git commit`, un passo di ri-ancoraggio (skill `sync-context`) allinea
`last-verified-commit` al nuovo hash, senza bisogno di riscrivere il contenuto.
