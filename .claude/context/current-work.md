---
generated-from-commit: PENDING-FIRST-COMMIT
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - src/legal_consultant/ingest/**
  - src/legal_consultant/index/**
  - scripts/bootstrap_index.py
last-verified-commit: PENDING-FIRST-COMMIT
stato: in pianificazione
---

# Lavoro in corso

> La fonte di verità su cosa è fatto resta `memory/index.md` e il work-log, non le spunte di
> questo file. Ogni feature si descrive con lo schema fisso sotto, così il lavoro pendente è
> leggibile senza ricostruire il contesto da capo.

## Feature: Fase 0+1 — Setup repo e pipeline di ingestion/indice FTS5

Cosa fa: predispone il progetto Python e costruisce la prima pipeline che legge `italia-corpus`,
spezza gli atti per articolo e crea l'indice di ricerca BM25 su SQLite FTS5.

File da creare:

```
pyproject.toml                              manifesto dipendenze (uv); include mcp, python-frontmatter
data/italia-corpus/                          git submodule del corpus (self-updating)
src/legal_consultant/ingest/                 parser MD+YAML, chunking per articolo
src/legal_consultant/index/                  build/query SQLite FTS5 (BM25)
scripts/bootstrap_index.py                   prima indicizzazione completa
```

File da modificare:

```
.claude/context/STACK.md                     popolare leggendo il codice reale una volta scritto
```

Definition of done:

- [ ] `italia-corpus` aggiunto come submodule sotto `data/`
- [ ] schema reale del frontmatter YAML ispezionato su atti rappresentativi
- [ ] parser MD+YAML che produce chunk per articolo con metadati (urn, atto, articolo, vigente)
- [ ] indice FTS5 costruito da `bootstrap_index.py`
- [ ] query di test restituiscono gli articoli pertinenti con ranking BM25 sensato

Domande aperte:

- Schema esatto del frontmatter: da verificare sul campo prima di scrivere il parser (ADR-004).
- Tokenizzazione FTS5 per l'italiano: `unicode61` con `remove_diacritics` + stopword e gestione
  delle abbreviazioni giuridiche (art., c.c., d.lgs.) — da tarare in Fase 1.

## Riconciliazione

Ultima verifica: 2026-06-25 al commit PENDING-FIRST-COMMIT (pre-codice, feature in pianificazione).
