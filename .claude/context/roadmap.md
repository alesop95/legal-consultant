---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths: []
last-verified-commit: 6111cd3
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
2. Fase 2 — Server MCP "legge-it" (`cerca_normativa`, `leggi_atto`, `info_corpus`). Codice del
   server fatto e testato su fixture (feature attiva, da committare). Restano la registrazione in
   Claude Desktop e il Project con istruzioni + disclaimer. La validazione che il piano Team
   consenta server MCP locali (ADR-002) si considera risolta in positivo: la stessa macchina usa
   già il server MCP locale `obsidian-vaults` in Claude Desktop.
3. Fase 3 — Aggiornamento automatico (git pull + reindex incrementale via git diff, schedulato).
4. Fase 4+ — Backlog: ricerca ibrida con embedding leggero CPU se il recall lessicale non basta;
   diritto UE (EUR-Lex); anonimizzazione opzionale pre-invio.

## Idee e ipotesi da verificare

- Recall del solo BM25 su query concettuali: da misurare; se insufficiente, ibrido (ADR-003).
- Schema reale del frontmatter YAML del corpus (ADR-004): confermato su atti reali in Fase 1.
- Disponibilità di server MCP locali sul piano Team (ADR-002): confermata di fatto dall'uso di
  `obsidian-vaults` sulla stessa installazione di Claude Desktop.
