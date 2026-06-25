# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:         main
Commit di riferimento: PENDING-FIRST-COMMIT
Data snapshot:         2026-06-25
```

## Stato di verifica delle schede

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | PENDING-FIRST-COMMIT | da popolare (nessun codice) |
| design-and-security.md | PENDING-FIRST-COMMIT | da popolare (nessun codice) |
| deployment.md | PENDING-FIRST-COMMIT | da popolare (nessun codice) |
| dev-testing.md | PENDING-FIRST-COMMIT | da popolare (nessun codice) |
| current-work.md | PENDING-FIRST-COMMIT | seminata (Fase 0+1 in pianificazione) |
| roadmap.md | PENDING-FIRST-COMMIT | seminata (direzione confermata) |

## Punto di ripresa

Sistema di progetto inizializzato (anatomia `.claude`, git con identità github-personal, remoto
vuoto). Prossima azione concreta: dopo il primo commit, eseguire la skill `sync-context` per
sostituire i `PENDING-FIRST-COMMIT` con l'hash di HEAD. Poi avviare la Fase 0+1 del prodotto:
aggiungere `italia-corpus` come git submodule sotto `data/`, ispezionare lo schema reale del
frontmatter YAML di alcuni atti, e scrivere il parser MD+YAML prima della prima indicizzazione
FTS5.
