---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths: []
last-verified-commit: 1e4c79b
---

# Roadmap

> Direzione e priorità del progetto. Tracciata. Non è il work-log: qui sta dove si va, non cosa è
> già stato fatto. Il dettaglio per fasi e i rischi sono in `HANDOFF.md`.

## Direzione

Un consulente legale locale, sempre aggiornato sul diritto italiano, esposto come server MCP
("legge-it") interrogato da Claude Desktop, con ricerca normativa BM25 interamente locale e
citazioni verificabili.

## Priorità

1. Fase 0+1 — Setup repo e pipeline di ingestion/indice FTS5 (feature attiva). È il fondamento:
   senza indice non c'è ricerca.
2. Fase 2 — Server MCP "legge-it" (`cerca_normativa`, `leggi_atto`, `info_corpus`), registrazione
   in Claude Desktop e Project con istruzioni + disclaimer. Prima cosa da validare: che il piano
   Team consenta server MCP locali (ADR-002).
3. Fase 3 — Aggiornamento automatico (git pull + reindex incrementale via git diff, schedulato).
4. Fase 4+ — Backlog: ricerca ibrida con embedding leggero CPU se il recall lessicale non basta;
   diritto UE (EUR-Lex); anonimizzazione opzionale pre-invio.

## Idee e ipotesi da verificare

- Recall del solo BM25 su query concettuali: da misurare; se insufficiente, ibrido (ADR-003).
- Disponibilità di server MCP locali sul piano Team senza restrizioni amministrative (ADR-002).
- Schema reale del frontmatter YAML del corpus (ADR-004).
