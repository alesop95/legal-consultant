---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - tests/**
last-verified-commit: 6111cd3
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
copre cinque casi: parsing del frontmatter e chunking per articolo, ricerca BM25 che trova l'atto
pertinente, filtro `solo_vigenti`, lettura di un atto per `urn` con filtro per articolo
(`get_act`) e conteggi dell'indice (`corpus_stats`). I tool del server MCP si verificano con uno
smoke manuale che costruisce un indice temporaneo, punta `INDEX_PATH` su di esso e invoca i tre
tool; non è ancora nella suite automatica.

## Hook e controlli di qualità

Nessun hook di pre-commit né lint/type-check configurati al momento. Il controllo prima del commit
è `uv run pytest` verde.
