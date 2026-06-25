---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - src/legal_consultant/ingest/**
  - src/legal_consultant/index/**
  - scripts/bootstrap_index.py
last-verified-commit: 1e4c79b
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

- [x] schema reale del frontmatter YAML ispezionato su atti rappresentativi (via API GitHub)
- [x] scaffolding Python (uv, layout src/, pyproject) e toolchain verificata (Python 3.13/uv)
- [x] parser MD+YAML che produce chunk per articolo con metadati (urn, atto, articolo, vigente)
- [x] indice FTS5 (build/upsert/search BM25 + filtro vigenti) e `bootstrap_index.py` scritti
- [x] test end-to-end su 2 atti reali (fixture): parser + ricerca BM25 verdi (`uv run pytest`)
- [ ] `italia-corpus` aggiunto come submodule shallow sotto `data/` (passo pesante, da fare)
- [ ] `bootstrap_index.py` eseguito sull'intero corpus e query di sanità sul reale

Stato: nucleo della pipeline implementato e testato su fixture; manca il clone del corpus e la
prima indicizzazione completa.

Domande aperte:

- Tokenizzazione FTS5 per l'italiano: `unicode61 remove_diacritics 2` scelto; stopword e gestione
  delle abbreviazioni giuridiche (art., c.c., d.lgs.) da valutare misurando sul corpus reale.
- Robustezza del parser su tutte le collezioni (numerazione articoli "N-bis", allegati, note):
  da validare sul reale dopo il bootstrap; il regex `_ARTICLE_RE` copre i casi visti finora.

## Riconciliazione

Ultima verifica: 2026-06-25. Codice della Fase 1 scritto e testato su fixture; le schede sono
avanti rispetto a `last-verified-commit` (1e4c79b) finché non si committa e si rilancia
`sync-context`.
