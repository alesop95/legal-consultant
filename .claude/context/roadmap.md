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
3. Fase 3 — Aggiornamento automatico (git pull + reindex incrementale via git diff). Codice fatto
   (package `update` + `scripts/update_corpus.py`); resta da schedulare con Task Scheduler e da
   validare sul corpus reale.
4. Packaging trasparente — registrazione versionata in `.mcp.json` (Claude Code), setup a un
   comando (`scripts/setup.py`), istruzioni e disclaimer (`prompts/consulente-legale.md` + prompt
   MCP). Fatto a livello di codice; resta la verifica end-to-end nei due client sul corpus reale.
5. Fase 4+ — Backlog: ricerca ibrida con embedding leggero CPU se il recall lessicale non basta;
   diritto UE (EUR-Lex); anonimizzazione opzionale pre-invio; indice pre-costruito distribuibile
   per saltare il bootstrap pesante al primo uso.

## Idee e ipotesi da verificare

- Recall del solo BM25 su query concettuali: misurato con `scripts/benchmark_retrieval.py`
  (26 domande). Con la pesatura di rubrica/titolo, recall@8 = 19/26; ~27% dei concetti non
  emerge perché la parola non è nella rubrica. Prossimo lever di qualità: ricerca ibrida con
  embedding leggero CPU (ADR-003), da valutare come Fase 4.
- Schema reale del frontmatter YAML del corpus (ADR-004): confermato su atti reali in Fase 1.
- Disponibilità di server MCP locali sul piano Team (ADR-002): confermata di fatto dall'uso di
  `obsidian-vaults` sulla stessa installazione di Claude Desktop.
