# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:         main
Commit di riferimento: 1e4c79b
Data snapshot:         2026-06-25
```

## Stato di verifica delle schede

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | 1e4c79b | aggiornata (scheletro, nessun codice) |
| design-and-security.md | 1e4c79b | aggiornata (scheletro, nessun codice) |
| deployment.md | 1e4c79b | aggiornata (scheletro, nessun codice) |
| dev-testing.md | 1e4c79b | aggiornata (scheletro, nessun codice) |
| current-work.md | 1e4c79b | aggiornata (Fase 0+1 in pianificazione) |
| roadmap.md | 1e4c79b | aggiornata (direzione confermata) |

## Punto di ripresa

Fase 1 implementata e testata su fixture: parser MD+YAML (chunking per articolo) + indice SQLite
FTS5 (BM25, filtro vigenti) in `src/legal_consultant/`, con `scripts/bootstrap_index.py` e
`tests/` (3 test verdi via `uv run pytest`). `STACK.md` popolata dal codice reale.

Modifiche di Fase 1 **non ancora committate**: dopo il commit, rilanciare `sync-context` per
ri-ancorare `last-verified-commit` a HEAD (le schede sono ora avanti rispetto a `1e4c79b`).

Prossima azione concreta: clonare il corpus come **submodule shallow** sotto `data/italia-corpus`
(`git submodule add --depth 1 https://github.com/ahmeabd/italia-corpus.git data/italia-corpus`),
poi `uv run python scripts/bootstrap_index.py` per la prima indicizzazione completa e una query
di sanità sul reale. Nota: il clone è pesante (~831 MB lato git + storia giornaliera) — preferire
shallow.
