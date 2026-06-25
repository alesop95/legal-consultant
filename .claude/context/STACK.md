---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - src/legal_consultant/**
  - scripts/**
  - pyproject.toml
last-verified-commit: 1e4c79b
---

# Stack applicativo

> Documento di recupero più importante: tracciato, perché un collega che clona deve vederlo.
> Aggiornato leggendo il codice reale della Fase 1 (ingest + indice). Le scelte di fondo sono in
> `decisions.md` (ADR-002/003/004).

## Stack e runtime

Python >= 3.11 (l'ambiente uv ha materializzato CPython 3.12.13). Gestore pacchetti e ambiente:
`uv` (lockfile `uv.lock`). Build backend: `hatchling`, layout `src/` con package
`legal_consultant`. Dipendenze runtime: `python-frontmatter` (parsing frontmatter YAML, trascina
`PyYAML`). Indice di ricerca: **SQLite FTS5** via `sqlite3` di stdlib (nessuna dipendenza
esterna), tokenizer `unicode61 remove_diacritics 2`, ranking **BM25** nativo. Test: `pytest`.

## Alternative deliberatamente escluse

Embedding semantici e vector DB (BGE-M3, LanceDB/Qdrant) esclusi per l'MVP: nessuna GPU
disponibile e prima indicizzazione troppo onerosa su CPU (ADR-003). La ricerca ibrida
dense+sparse resta in backlog, da introdurre solo se il recall del solo BM25 risulta
insufficiente. Diritto UE (EUR-Lex) fuori ambito (ADR-004).

## Flussi di codice e ruolo architetturale dei file

`config.py` risolve i percorsi locali (CORPUS_PATH, INDEX_PATH, STATE_PATH) da ambiente/.env con
default relativi alla radice. `ingest/parser.py` legge un atto `.md`: separa il frontmatter YAML
(metadati dell'atto) e spezza il corpo in chunk a granularità di articolo, riconoscendo le
intestazioni `## Art. N.` con rubrica opzionale; produce `ParsedAct(act, chunks)`. `index/fts.py`
costruisce e interroga la tabella virtuale FTS5 `chunks` (colonne testuali indicizzate, metadati
UNINDEXED per citazione e filtri), con `insert_act`, `delete_path` (upsert per file) e `search`
(BM25 + filtro `solo_vigenti`). `scripts/bootstrap_index.py` percorre il corpus, parsa ogni atto e
popola l'indice da zero. Il server MCP "legge-it" (Fase 2) consumerà `index.fts.search`.

## Riferimenti a snippet

```
src/legal_consultant/ingest/parser.py:parse_act        parsing atto → metadati + chunk
src/legal_consultant/ingest/parser.py:_split_chunks    chunking per articolo
src/legal_consultant/ingest/parser.py:_ARTICLE_RE      regex intestazione "## Art. N."
src/legal_consultant/index/fts.py:_DDL                 schema FTS5 (tokenizer, colonne)
src/legal_consultant/index/fts.py:search               ricerca BM25 + filtro vigenti
scripts/bootstrap_index.py:main                        prima indicizzazione completa
```
