---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - src/legal_consultant/**
  - scripts/**
  - pyproject.toml
last-verified-commit: f954aaa
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

`config.py` risolve i percorsi locali (CORPUS_PATH, EXTRA_CORPUS_PATH, INDEX_PATH, STATE_PATH) da
ambiente/.env con default relativi alla radice, ed espone `long_path`, che su Windows antepone il prefisso
extended-length `\\?\` ai path assoluti: il corpus italiano ha nomi di file che superano il limite
di 260 caratteri (MAX_PATH) e senza questo accorgimento non sarebbero leggibili: l'helper aggira il
limite senza modifiche al registro né privilegi di amministratore. `ingest/parser.py` lo usa per
aprire ogni atto. `ingest/parser.py` legge un atto `.md`: separa il frontmatter YAML
(metadati dell'atto) e spezza il corpo in chunk a granularità di articolo, riconoscendo le
intestazioni `## Art. N.` con rubrica opzionale; produce `ParsedAct(act, chunks)`. `index/fts.py`
costruisce e interroga la tabella virtuale FTS5 `chunks` (colonne testuali indicizzate, metadati
UNINDEXED per citazione e filtri), con `insert_act`, `delete_path` (upsert per file), `search`
(BM25 + filtro `solo_vigenti`), `get_act` (chunk di un atto per `urn` o `path`, in ordine, con
filtro per singolo articolo) e `corpus_stats` (conteggio atti distinti e chunk).
`scripts/bootstrap_index.py` percorre il corpus, parsa ogni atto e popola l'indice da zero.
`mcp_server.py` è il server MCP "legge-it": costruisce un `FastMCP` e registra i tre tool
`cerca_normativa` (sopra `fts.search`), `leggi_atto` (sopra `fts.get_act`) e `info_corpus` (sopra
`fts.corpus_stats` più la freschezza del corpus), e il prompt `consulenza_legale` con le istruzioni
e il disclaimer; gira su transport stdio. La logica dati resta in `index.fts`; il server è uno
strato sottile di wiring più helper puri di formattazione (`_hit_to_dict`, `_citazione`), così i
tool sono verificabili sull'indice di fixture senza il transport. Ogni tool degrada con grazia
quando l'indice non esiste, rimandando al bootstrap. La ricerca è robusta a input libero: `search`
passa la query per `fts.to_match_query`, che estrae i soli token e li cita come termini letterali
in OR, così un testo non tecnico non può produrre una query MATCH invalida.

Il package `update` gestisce l'aggiornamento incrementale (Fase 3): `corpus_revision` legge commit
e data dell'HEAD del corpus, `pull` fa il fast-forward del submodule, `changed_files` calcola via
`git diff` i `.md` aggiunti/modificati/cancellati fra due revisioni, `reindex_paths` ritocca
nell'indice i soli atti cambiati (upsert per path), e `read_state`/`write_state` persistono lo
stato in `data/index/state.json` (commit, data, conteggi, timestamp del reindex). `scripts/setup.py`
è il setup a un comando per l'utente finale (init submodule shallow, `uv sync`, bootstrap);
`scripts/update_corpus.py` è l'aggiornamento schedulabile; `scripts/fetch_codici.py` scarica da
Normattiva (via `normattiva2md`) i codici fondamentali il cui articolato manca in italia-corpus
(civile, penale, procedura civile, navigazione, penali militari) e li salva in `EXTRA_CORPUS_PATH`
(`data/codici-extra`, tracciato), che il bootstrap indicizza insieme al submodule. Il parser
riconosce gli articoli a 2-4 cancelletti con rubrica sia dopo il trattino (italia-corpus) sia tra
parentesi (Normattiva). La registrazione in Claude Code è
versionata in `.mcp.json` in radice; per Claude Desktop si usa la voce in `deployment.md`.

## Riferimenti a snippet

```
src/legal_consultant/ingest/parser.py:parse_act        parsing atto → metadati + chunk
src/legal_consultant/ingest/parser.py:_split_chunks    chunking per articolo
src/legal_consultant/ingest/parser.py:_ARTICLE_RE      regex intestazione "## Art. N."
src/legal_consultant/index/fts.py:_DDL                 schema FTS5 (tokenizer, colonne)
src/legal_consultant/index/fts.py:search               ricerca BM25 + filtro vigenti + sanitize
src/legal_consultant/index/fts.py:to_match_query       testo libero → query MATCH sicura
src/legal_consultant/index/fts.py:get_act              chunk di un atto per urn/path (+ articolo)
src/legal_consultant/index/fts.py:corpus_stats         conteggio atti e chunk indicizzati
scripts/bootstrap_index.py:main                        prima indicizzazione completa
src/legal_consultant/mcp_server.py:cerca_normativa     tool MCP: ricerca BM25 → estratti citabili
src/legal_consultant/mcp_server.py:leggi_atto          tool MCP: testo integrale atto/articolo
src/legal_consultant/mcp_server.py:info_corpus         tool MCP: stato e freschezza + disclaimer
src/legal_consultant/mcp_server.py:consulenza_legale   prompt MCP: istruzioni + disclaimer
src/legal_consultant/update/__init__.py:reindex_paths  reindicizzazione incrementale per path
src/legal_consultant/update/__init__.py:changed_files  git diff → atti cambiati/cancellati
scripts/update_corpus.py:main                          pull + reindex incrementale (schedulabile)
scripts/setup.py:main                                  setup a un comando per l'utente finale
```
