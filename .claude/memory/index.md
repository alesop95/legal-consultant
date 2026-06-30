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

## Stato del corpus e dell'indice

Corpus reale clonato in `data/italia-corpus` (287.813 file, fuori da git: clone non ancora
registrato come submodule). Indice FTS5 reale in `data/index/legge.sqlite` (2.4 GB, gitignored):
287.785 atti, 759.881 chunk; 163.957 atti vigenti dopo l'esclusione della collezione delle
abrogate. Server MCP verificato sull'indice reale. Limite di Windows sui path lunghi gestito dal
codice (`config.long_path`) e da `core.longpaths`, senza admin.

## Punto di ripresa

Fase 1 in `6111cd3`, Fase 2 in `f954aaa`, hardening/Fase 3/packaging/disclaimer in `bd19b1d`.
Non ancora committato (questa sessione): gestione percorsi lunghi Windows (`config.long_path`,
`setup.py` con `core.longpaths`), declassamento delle abrogate a non vigenti nel parser, deduplica
in `search`, più aggiornamenti delle schede. Il corpus reale è clonato e l'indice completo è
costruito (vedi sezione sopra); server MCP verificato sull'indice reale; 9 test verdi.

Prossime azioni concrete, in ordine. Primo: committare il codice di questa sessione (percorsi
lunghi, vigenti, dedup) e le schede, escludendo `data/`, poi rilanciare `sync-context`. Secondo
(productizzazione): registrare il corpus come submodule per la riproducibilità del clone — il
clone esistente in `data/italia-corpus` è funzionante ma non registrato; `git submodule add` va
fatto con `-c core.longpaths=true`. Terzo: usare il consulente da chat — aprire il progetto in una
nuova sessione di Claude Code e approvare il server di `.mcp.json`, oppure registrarlo in Claude
Desktop, poi i casi d'uso concordati con l'utente. Limite noto da comunicare: "vigente" qui esclude
solo la collezione delle abrogate, non garantisce la vigenza odierna su Normattiva (vale il
disclaimer); ranking BM25 su query concettuali da valutare (ADR-003, eventuale ibrido).
