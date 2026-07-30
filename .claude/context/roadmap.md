---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths: []
last-verified-commit: f7a4da9
---

# Roadmap

> Direzione e priorità del progetto. Tracciata. Non è il work-log: qui sta dove si va, non cosa è
> già stato fatto. Il dettaglio per fasi e i rischi sono in `HANDOFF.md`.

## Direzione

Un consulente legale locale, sempre aggiornato sul diritto italiano, esposto come server MCP
("legge-it") interrogato da Claude Desktop, con ricerca normativa BM25 interamente locale e
citazioni verificabili.

## Priorità

1. Fase 0+1 — Setup repo e pipeline di ingestion/indice FTS5 (fatta, committata in `6111cd3`;
   testata su fixture). Resta il clone del corpus e la prima indicizzazione completa.
2. Fase 2 — Server MCP "legge-it" (`cerca_normativa`, `leggi_atto`, `info_corpus`). Fatta e testata
   su fixture, con hardening della ricerca e prompt MCP delle istruzioni. ADR-002 (server MCP
   locali sul piano Team) risolto in positivo: la stessa macchina usa già `obsidian-vaults`.
3. Fase 3 — Aggiornamento automatico (fetch + reset incrementale). Codice fatto e validato sul
   corpus reale (Fase D): un limite strutturale del corpus su Windows (collisione di path per
   case) ha richiesto di sostituire `git pull --ff-only` con fetch + reset --hard in
   `update.pull()`. Resta solo, se utile, schedulare l'esecuzione con Task Scheduler.
4. Packaging trasparente — registrazione versionata in `.mcp.json` (Claude Code), setup a un
   comando (`scripts/setup.py`), istruzioni e disclaimer (`prompts/consulente-legale.md` + prompt
   MCP). Fatto e verificato end-to-end nei due client sul corpus reale (Fase B/C), incluso il
   riavvio dell'installer su una macchina già configurata.
5. Completezza del corpus — fatta come macchina, in convergenza come dato. Il corpus di terze
   parti non contiene la legge ordinaria, il decreto-legge vigente e la Costituzione, perché
   rispecchia il catalogo delle collezioni preconfezionate di Normattiva (misura e diagnosi in
   `docs/audit-completezza-corpus.md`, ADR-005). Recupero dall'API Open Data ufficiale
   (`scripts/fetch_normattiva.py`), recupero puntuale per URN (`scripts/fetch_atto.py`) e
   controllo che fallisce dicendo cosa manca (`scripts/check_completezza.py`), integrati
   nell'installer e nell'attività pianificata. Il popolamento storico converge in alcuni giorni
   di esecuzioni a budget.
6. Fase 4+ — Backlog: ricerca ibrida con embedding leggero CPU se il recall lessicale non basta;
   diritto UE (EUR-Lex); anonimizzazione opzionale pre-invio; indice pre-costruito distribuibile
   per saltare il bootstrap pesante al primo uso (attenzione: se si adottassero gli open data
   della Corte costituzionale, la loro licenza CC BY-SA renderebbe l'indice un'opera derivata
   con obblighi di attribuzione e licenza compatibile, vedi ADR-006).

## Idee e ipotesi da verificare

- Recall del solo BM25 su query concettuali: misurato con `scripts/benchmark_retrieval.py`
  (26 domande). Con la pesatura di rubrica/titolo, recall@8 = 19/26; ~27% dei concetti non
  emerge perché la parola non è nella rubrica. Prossimo lever di qualità: ricerca ibrida con
  embedding leggero CPU (ADR-003), da valutare come Fase 4.
- Il benchmark non copre le classi recuperate da Normattiva: le sue 26 domande puntano tutte su
  codici e testi unici, quindi misura la non-regressione (invariata: recall@1 14/26, recall@5 e
  recall@8 19/26 prima e dopo) e non il guadagno, e non esercita i nuovi concorrenti che
  migliaia di leggi introducono nel ranking. Estenderlo con domande sulle leggi ordinarie è la
  verifica che manca, dichiarata come tale invece di essere data per fatta.
- Giurisprudenza: analisi di fattibilità fatta (`docs/giurisprudenza-fattibilita.md`, ADR-006).
  Se si procederà, solo Corte costituzionale, tabella e tool distinti, e il guadagno atteso è la
  congiunzione deterministica norma-giurisprudenza sui riferimenti strutturati, non la ricerca
  full-text. Cassazione esclusa per divieto scritto del titolare, non per scelta di perimetro.
- Schema reale del frontmatter YAML del corpus (ADR-004): confermato su atti reali in Fase 1.
- Disponibilità di server MCP locali sul piano Team (ADR-002): confermata di fatto dall'uso di
  `obsidian-vaults` sulla stessa installazione di Claude Desktop.
