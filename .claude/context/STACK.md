---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - src/legal_consultant/**
  - scripts/**
  - pyproject.toml
last-verified-commit: 6111cd3
---

# Stack applicativo

> Documento di recupero più importante: tracciato, perché un collega che clona deve vederlo.
> Aggiornato leggendo il codice reale della Fase 1 (ingest + indice) e della Fase 2 (server MCP).
> Le scelte di fondo sono in `decisions.md` (ADR-002/003/004).

## Stack e runtime

Python >= 3.11 (l'ambiente uv ha materializzato CPython 3.12.13). Gestore pacchetti e ambiente:
`uv` (lockfile `uv.lock`). Build backend: `hatchling`, layout `src/` con package
`legal_consultant`. Dipendenze runtime: `python-frontmatter` (parsing frontmatter YAML, trascina
`PyYAML`) e `mcp` (SDK ufficiale Model Context Protocol, da cui FastMCP per il server e il
transport stdio). Indice di ricerca: **SQLite FTS5** via `sqlite3` di stdlib (nessuna dipendenza
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
UNINDEXED per citazione e filtri), con `insert_act`, `delete_path` (upsert per file), `search`
(BM25 + filtro `solo_vigenti`), `get_act` (chunk di un atto per `urn` o `path`, in ordine, con
filtro per singolo articolo) e `corpus_stats` (conteggio atti distinti e chunk).
`scripts/bootstrap_index.py` percorre il corpus, parsa ogni atto e popola l'indice da zero.
`mcp_server.py` è il server MCP "legge-it": costruisce un `FastMCP` e registra i tre tool
`cerca_normativa` (sopra `fts.search`), `leggi_atto` (sopra `fts.get_act`) e `info_corpus` (sopra
`fts.corpus_stats`), avviandolo su transport stdio per Claude Desktop. La logica dati resta in
`index.fts`; il server è uno strato sottile di wiring più helper puri di formattazione
(`_hit_to_dict`, `_citazione`), così i tool sono verificabili sull'indice di fixture senza il
transport. Ogni tool degrada con grazia quando l'indice non esiste, rimandando al bootstrap.

## Riferimenti a snippet

```
src/legal_consultant/ingest/parser.py:parse_act        parsing atto → metadati + chunk
src/legal_consultant/ingest/parser.py:_split_chunks    chunking per articolo
src/legal_consultant/ingest/parser.py:_ARTICLE_RE      regex intestazione "## Art. N."
src/legal_consultant/index/fts.py:_DDL                 schema FTS5 (tokenizer, colonne)
src/legal_consultant/index/fts.py:search               ricerca BM25 + filtro vigenti
src/legal_consultant/index/fts.py:get_act              chunk di un atto per urn/path (+ articolo)
src/legal_consultant/index/fts.py:corpus_stats         conteggio atti e chunk indicizzati
scripts/bootstrap_index.py:main                        prima indicizzazione completa
src/legal_consultant/mcp_server.py:cerca_normativa     tool MCP: ricerca BM25 → estratti citabili
src/legal_consultant/mcp_server.py:leggi_atto          tool MCP: testo integrale atto/articolo
src/legal_consultant/mcp_server.py:info_corpus         tool MCP: stato dell'indice
```
