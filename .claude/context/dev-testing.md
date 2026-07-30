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
pytest). I test vivono in `tests/test_pipeline.py` e `tests/test_fonte.py`, sono 30 in tutto, e
girano interamente in memoria o su `tmp_path`, senza toccare l'indice su disco, senza richiedere il
corpus e senza fare rete.

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

`tests/test_fonte.py` copre il recupero dalla fonte ufficiale con diciotto casi, e la scelta di
fondo è che nessuno di essi faccia rete: la conversione è pura, e del client si verificano solo le
parti pure. La fixture è un export reale dell'API di Normattiva,
`tests/fixtures-akn/legge-2026-101.akn.xml`, tenuto in una cartella separata da `tests/fixtures/`
perché quest'ultima viene indicizzata per intero dagli altri test e un XML vi comparirebbe come
rumore. I casi coprono l'estrazione dei metadati, la regola per cui numero e data si prendono dalla
URN e non dai tag del documento, lo scarto delle date impossibili che la fonte dichiara sugli atti
non numerati, la leggibilità del Markdown prodotto da parte del parser del progetto, la
conservazione dei numeri di comma, l'esclusione del contenuto delle note, il quoting del titolo nel
frontmatter, i due rami dell'euristica che ricostruisce la rubrica (promozione quando il capoverso
anonimo è seguito da commi, e non promozione quando è l'unico contenuto, che è il caso reale della
Costituzione), gli allegati come unità citabili distinte, la scomposizione della URN, la selezione
di una sola versione per atto dentro l'archivio, il comportamento della lista bianca in entrambi i
versi, la segnalazione senza eccezione di un XML non valido, e una verifica di filiera che porta
l'XML della fonte fino a un risultato di ricerca. Sono deliberatamente inclusi i test dei tre
difetti trovati durante lo sviluppo, così che una regressione su di essi si veda subito.

## Hook e controlli di qualità

Nessun hook di pre-commit né lint/type-check configurati al momento. Il controllo prima del commit
è `uv run pytest` verde.
