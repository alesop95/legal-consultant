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
last-verified-commit: f7a4da9
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
- [x] affinamento del ranking (committato in `995e154`): filtro stopword italiane in
      `to_match_query`, `_rubrica_bonus` (corrispondenza rubrica-domanda) e
      `_CODICE_GENERALE_BONUS` (spareggio sui codici generali) in `fts.search`, sovra-campionamento
      a 50x (recall@1 10→13/26, recall@5 15→19/26; vedi domande aperte per il residuo)
- [x] fix del test dal vivo (committato in `0d0667a`): il test in Claude Desktop (screenshot, 6
      query con `limit=1`) aveva dato solo 3/6 corrette, scoprendo un bug non colto dal benchmark
      (`limit=8`): il sovra-campionamento scalava su `limit`, e con `limit=1` (usato da Claude
      Desktop per isolare il primo risultato) la finestra di ricalcolo crollava a sole 50 righe;
      corretto con un minimo fisso di 400. Bonus codici generali alzato da -3/-2 a -6/-4 per
      risolvere anche "diffamazione" in prima posizione, non solo in top-8. Ripetuto lo stesso test
      dal vivo in Claude Desktop dopo il riavvio (Sonnet 4.6, ragionamento alto, screenshot_01.png):
      5/6 corrette, confermato. L'unico errore (query 6, "risoluzione del contratto per
      inadempimento" → art. 1564 invece di 1453 c.c.) è il residuo noto, non un nuovo bug; il
      modello stesso lo ha diagnosticato correttamente in chat come limite del ranking lessicale su
      quella formulazione.
- [x] Fase B, Project creato: "Consulente legale" in Claude Desktop (Sonnet 4.6, ragionamento
      alto), istruzioni incollate da `prompts/consulente-legale.md` (verificate su screenshot,
      testo e disclaimer coincidenti), tool `legge-it` collegato e confermato in uso ("Usata
      integrazione legge-it" su ogni risposta)
- [x] Fase B, batteria di domande dal vivo: 8/8 completate, tutte superate (dettaglio sotto)
- [ ] prova dell'installer su una situazione pulita (Fase C); prova aggiornamento (Fase D)

Stato: prodotto completo e verificato end-to-end in Claude Desktop, con i codici fondamentali,
l'installer e il ranking pesato, affinato e corretto (`995e154`, `0d0667a`), riconfermato dal vivo
in Claude Desktop dopo il fix (5/6, screenshot_01.png). Fase A conclusa; il drift di ranking è
stato analizzato a fondo e risolto per quanto possibile su base lessicale, col residuo isolato in
quattro cause distinte (vedi domande aperte), tutte strutturali al solo BM25. Fase B conclusa (vedi
sotto). Restano le Fasi C/D del piano di test.

Fase B — risultati della batteria di domande (2026-07-02/03, 8/8 completate, tutte superate). Project
"Consulente legale" creato in Claude Desktop con le istruzioni di `prompts/consulente-legale.md`
incollate senza modifiche (verificato su screenshot: testo e disclaimer coincidenti) e il tool
`legge-it` collegato e confermato in uso su ogni domanda ("Usata integrazione legge-it").

1. Prescrizione dell'omicidio: cita art. 157 c.p. con URN e distingue correttamente le tre
   fattispecie (art. 575 doloso semplice 24 anni, artt. 576-577 co.1 aggravato con ergastolo
   imprescrittibile, art. 577 co.2 aggravato con reclusione 24-30 anni), disclaimer regolare.
2. Risoluzione del contratto per inadempimento: risolve il caso critico noto di Fase A (l'articolo
   generale art. 1453 c.c. contro le norme speciali con rubrica letterale "Risoluzione del
   contratto"). Le istruzioni del Project (prova più formulazioni, usa `leggi_atto` se conosce
   l'articolo) hanno compensato in pratica il residuo di ranking: risposta corretta e completa sui
   quattro meccanismi (art. 1453 giudiziale, 1454 diffida, 1456 clausola risolutiva, 1457 termine
   essenziale).
3. Licenziamento per giusta causa: cita art. 2119 c.c., D.Lgs. 23/2015 art. 3, D.Lgs. 104/2022 art.
   14 sull'onere della prova; segnala esplicitamente che la L. 604/1966, pur pertinente, "non
   risulta indicizzata nel corpus locale" invece di rispondere a memoria o cercarla altrove.
4. Garanzia di conformità nella vendita di beni di consumo: risolve l'altro caso critico noto di
   Fase A (rubrica dell'art. 128 codice del consumo scollegata dal contenuto). Trattazione completa
   e corretta di tutto l'impianto (artt. 129, 130, 133, 134, 135-bis/ter/quater).
5. Termini per la querela: art. 124 c.p. (3 mesi) più le deroghe speciali verificate nel corpus
   (art. 609-septies 12 mesi, art. 612-bis 6 mesi); dichiara esplicitamente che oltre queste il
   corpus non garantisce completezza e rimanda a Normattiva.
6. Domanda su norma probabilmente assente (Reg. UE 2023/988 sulla tracciabilità): comportamento
   esemplare, il più significativo della batteria. Prova l'URN diretto, verifica l'assenza di
   risultati, dichiara che il testo del regolamento non è indicizzato, e costruisce comunque una
   risposta operativa onesta sulla cornice nazionale di raccordo che il corpus contiene davvero
   (D.Lgs. 78/2026, Codice del consumo modificato), senza mai cercare sul web né rispondere a
   memoria sul contenuto del regolamento stesso.

7. Freschezza del corpus (`info_corpus`): chiama esplicitamente "Info corpus" e restituisce una
   tabella completa (aggiornamento 30 giugno 2026, ultima indicizzazione, 287.790 atti, 966.126
   chunk, hash del commit), calcola correttamente lo scarto rispetto alla data odierna (~3 giorni)
   e riepiloga in modo trasparente i limiti strutturali del corpus richiamando coerentemente la
   risposta precedente sul Reg. UE 2023/988 (continuità conversazionale nella stessa chat).
8. Domanda generica/ambigua ("ho ricevuto una multa che ritengo ingiusta, cosa posso fare?"): primo
   turno, il modello non risponde a memoria né cerca sul web, ma pone una domanda di chiarimento
   sul tipo di multa (Codice della Strada, altra sanzione amministrativa, tributaria), perché le
   procedure di ricorso sono radicalmente diverse — comportamento da consulente reale, anche se non
   conclusivo sull'uso di `cerca_normativa`. Al chiarimento ("eccesso di velocità, verbale del
   Codice della Strada") cerca e cita correttamente D.Lgs. 285/1992 artt. 203-204 e D.Lgs. 150/2011
   art. 7, con confronto strutturato dei due canali di ricorso (Prefetto/Giudice di Pace) e
   consiglio operativo motivato.

Fase B conclusa: 8/8 domande superate. Nessun comportamento fuori disciplina (niente risposte a
memoria non dichiarate, niente ricerca web, disclaimer sempre presente e corretto); due dei quattro
casi critici residui di Fase A risolti in pratica dalle istruzioni del Project senza l'ibrido con
embedding.

Domande aperte:

- Semantica di "vigente": nel corpus il campo `vigente` è True anche per le abrogate, quindi il
  filtro esclude solo la collezione "Atti normativi abrogati (in originale)". Non garantisce la
  vigenza odierna di un atto su Normattiva: vale il disclaimer. I codici integrati sono scaricati
  alla vigenza odierna ma vanno rinfrescati con `fetch_codici.py`.
- Drift di ranking (AFFINATO E VERIFICATO DAL VIVO, `995e154` + `0d0667a`): in `fts.py` aggiunti il filtro delle
  stopword italiane in `to_match_query` (senza, "di"/"nel" da soli abbinavano centinaia di
  migliaia di righe e diluivano il campione), `_rubrica_bonus` (premia le rubriche quasi
  interamente coperte dalle parole di contenuto della domanda, es. "Furto" su "furto") e
  `_CODICE_GENERALE_BONUS` (spareggio sui tre codici generali quando due codici condividono la
  stessa rubrica: "diffamazione" ora risolve l'art. 595 c.p. e non più l'art. 227 dei codici
  penali militari, bonus a -6/-4 dopo che -3/-2 non bastava a rompere il pareggio in prima
  posizione). Il sovra-campionamento di `search` è salito a 50x il limite con un minimo fisso di
  400, perché la normalizzazione per lunghezza di BM25 può relegare l'articolo giusto ben oltre la
  finestra di ricalcolo se il suo testo è lungo (es. "usura", art. 644 c.p., era 77° su 472
  corrispondenze grezze) e perché un `limit` piccolo (Claude Desktop chiama con `limit=1` per
  isolare il primo risultato) non deve restringere la finestra di ricalcolo. Misurato su
  `scripts/benchmark_retrieval.py`: recall@1 10→14/26, recall@5 15→19/26, recall@8 invariato a
  19/26 ma con risultati molto più in alto in classifica; confermato dal vivo in Claude Desktop
  (Sonnet 4.6, ragionamento alto) sulle stesse 6 query in due passaggi: 3/6 corrette prima del fix
  del sovra-campionamento (screenshot_16.png, screenshot_17.png), 5/6 dopo (screenshot_01.png). Il
  residuo non è più un'unica causa generica ma quattro isolate e diverse: rubriche nel corpus
  genuinamente
  scollegate dal contenuto sostanziale dell'articolo (art. 633 c.p.c. sul decreto ingiuntivo ha
  rubrica "Condizioni di ammissibilità", art. 128 codice del consumo sulla garanzia di conformità
  ha rubrica "Ambito di applicazione e definizioni"); variazione di lemma non colta dal matching
  per token esatto ("concorso" nella domanda contro "concorrono" nella rubrica dell'art. 110 c.p.);
  un caso di diluizione estrema oltre ogni sovra-campionamento ragionevole (art. 2087 c.c., 458°
  su quasi 79.000 corrispondenze grezze per "lavoro"/"datore"); e un'ambiguità genuina tra norma
  generale e norme speciali nello stesso codice ("risoluzione del contratto per inadempimento" →
  art. 1564 c.c., su una vendita a consegne ripartite, invece dell'art. 1453 c.c., la norma
  generale: la sua rubrica usa il sinonimo tecnico "Risolubilità" mentre più norme speciali dello
  stesso codice si intitolano letteralmente "Risoluzione del contratto", vincendo il matching
  lessicale). Tutte e quattro richiedono l'ibrido con embedding leggero CPU (ADR-003, Fase 4):
  nessuna ulteriore leva lessicale su BM25 le risolve senza rischiare nuove regressioni (un bonus
  più aggressivo su "Risoluzione del contratto" premierebbe di nuovo le norme speciali). Nel
  prodotto il residuo resta mitigato da conoscenza del modello + `leggi_atto`.
- Trasparenza: il `git submodule add` iniziale resta un passo del manutentore; valutare la
  distribuzione di un indice pre-costruito per saltare il bootstrap pesante al primo uso.

## Riconciliazione

Ultima verifica: 2026-07-02. Codice committato fino a `0d0667a` (affinamento del ranking in
`995e154`, fix del test dal vivo in `0d0667a`), confermato dal vivo in Claude Desktop dopo il
riavvio (5/6, screenshot_01.png). Questa scheda è aggiornata oltre l'ultimo commit solo per
registrare l'esito della conferma dal vivo: un passo di ri-ancoraggio (skill `sync-context`)
allineerà `last-verified-commit` a `0d0667a` al prossimo commit di questa scheda.
