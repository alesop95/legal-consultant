---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - tests/**
last-verified-commit: f7a4da9
---

# Test di sviluppo

> Aggiornato leggendo la suite reale. La checklist operativa locale dei test manuali vive invece
> in `_notes/TEST-CHECKLIST.md`, ignorata da git.

## Test runner e comandi

Framework `pytest`, dichiarato in `optional-dependencies.dev` di `pyproject.toml`. Si esegue con
`uv run pytest` dalla radice, dopo `uv sync --extra dev` (il `sync` senza extra non materializza
pytest). I test vivono in `tests/test_pipeline.py` e girano interamente in memoria, senza toccare
l'indice su disco né richiedere il corpus.

## Rotte e dati mockati

Le fixture sono due atti reali sotto `tests/fixtures/Codici/` (`giustizia_contabile.md`,
`penale_approvazione.md`), scelti perché rappresentativi della struttura del corpus (frontmatter
YAML, articoli `## Art. N.` con rubrica, preambolo). L'helper `_build_index` costruisce un indice
FTS5 su `:memory:` parsando le fixture, e fa `skip` se il build di SQLite non ha FTS5. La suite
copre dieci casi: parsing del frontmatter e chunking, chunking multilivello dei codici (articoli a
`## Art.` e `### Art.`, rubrica dopo trattino o tra parentesi, intestazioni strutturali ignorate),
ricerca BM25 pertinente, filtro `solo_vigenti`, lettura di un atto per `urn` con filtro articolo
(`get_act`), conteggi (`corpus_stats`), sanificazione della query (`to_match_query`), robustezza
della ricerca su input malformato (non solleva), reindicizzazione incrementale
(`update.reindex_paths`: cancella e reinserisce un atto) e round-trip dello stato
(`update.read_state`/`write_state`, con `tmp_path`). I tool e il prompt del
server MCP si verificano con uno smoke manuale che costruisce un indice temporaneo, punta
`INDEX_PATH` su di esso e invoca i tre tool; non è ancora nella suite automatica. Le funzioni git
del package `update` (`corpus_revision`, `changed_files`, `pull`) richiedono un repo reale e si
validano sul corpus dopo il bootstrap.

## Hook e controlli di qualità

Nessun hook di pre-commit né lint/type-check configurati al momento. Il controllo prima del commit
è `uv run pytest` verde.
