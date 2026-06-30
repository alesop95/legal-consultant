# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:         main
Commit di riferimento: f954aaa
Data snapshot:         2026-06-30
```

## Stato di verifica delle schede

Nota: le schede sono ri-ancorate a `f954aaa`, ma il loro contenuto descrive anche lo sviluppo
non ancora committato (hardening, Fase 3, packaging, disclaimer): è avanti rispetto a HEAD finché
non si committa e si rilancia `sync-context`.

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | f954aaa | aggiornata (Fase 1+2+3+packaging); contenuto avanti, da committare |
| design-and-security.md | f954aaa | popolata (strati, update, mitigazione query); avanti |
| deployment.md | f954aaa | popolata (setup, update_corpus, registrazione Claude Code/Desktop); avanti |
| dev-testing.md | f954aaa | popolata (pytest, fixture, 9 test); avanti |
| current-work.md | f954aaa | aggiornata (prodotto completo su fixture); avanti |
| roadmap.md | f954aaa | aggiornata (Fase 3 e packaging fatti a codice); avanti |

## Punto di ripresa

Fase 1 committata in `6111cd3`. Fase 2 committata in `f954aaa` (server MCP "legge-it"). Sopra di
essa, scritto e testato su fixture ma **non ancora committato**, il resto dello sviluppo del
prodotto: hardening della ricerca (`fts.to_match_query` + `search` sanitize), Fase 3 (package
`update` + `scripts/update_corpus.py`), packaging trasparente (`.mcp.json` per Claude Code,
`scripts/setup.py`, prompt MCP), disclaimer e istruzioni (`prompts/consulente-legale.md` + prompt
`consulenza_legale`). Suite a 9 test verdi (`uv run pytest`); smoke di tool e prompt ok; stdio
pulito.

Prossime azioni concrete, in ordine. Primo: committare lo sviluppo qui sopra (codice + schede), poi
rilanciare `sync-context` per ri-ancorare a HEAD. Secondo: aggiungere il corpus come **submodule
shallow** — passo manuale del manutentore, `git submodule add --depth 1
https://github.com/ahmeabd/italia-corpus.git data/italia-corpus` — e lanciare `uv run python
scripts/setup.py` (o `bootstrap_index.py`) per la prima indicizzazione completa (clone pesante,
~831 MB, preferire shallow). Terzo: verifica end-to-end in Claude Code (`.mcp.json`) e Claude
Desktop, poi i casi d'uso specifici di test concordati con l'utente.
