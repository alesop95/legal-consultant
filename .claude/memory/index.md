# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:         main
Commit di riferimento: 889f843
Data snapshot:         2026-07-01
```

## Stato di verifica delle schede

Tutte le schede sono ri-ancorate a HEAD (`889f843`) e il contenuto coincide: nessun drift
documentale. L'unico drift aperto è di ranking (retrieval), tracciato in `current-work.md`.

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | 889f843 | allineata (Fase 1-3, packaging, codici, ranking pesato) |
| design-and-security.md | 889f843 | allineata (strati, update, mitigazioni, path lunghi) |
| deployment.md | 889f843 | allineata (installer, setup, registrazione client) |
| dev-testing.md | 889f843 | allineata (pytest 10, fixture, benchmark) |
| current-work.md | 889f843 | allineata (Fase A conclusa; drift ranking aperto) |
| roadmap.md | 889f843 | allineata (benchmark misurato; ibrido come Fase 4) |

## Stato del corpus e dell'indice

Corpus reale clonato in `data/italia-corpus` (287.813 file, fuori da git: clone non ancora
registrato come submodule), più la collezione supplementare `data/codici-extra` (tracciata, ~5.2 MB)
coi 5 codici fondamentali scaricati da Normattiva. Indice FTS5 in `data/index/legge.sqlite`
(~2.6 GB, gitignored): 287.816 atti, 966.126 chunk. Server MCP verificato sull'indice reale e in
Claude Desktop. I codici civile/penale/procedura civile (prima assenti) ora sono ricercabili
(art. 2043 c.c., 157 c.p., 112 c.p.c.). Limite di Windows sui path lunghi gestito dal codice
(`config.long_path`) e da `core.longpaths`, senza admin.

## Punto di ripresa

Tutto committato fino a `889f843` (HEAD): prodotto completo e verificato end-to-end in Claude
Desktop (cita artt. 157-161-bis c.p. con URN dal corpus, niente web; `info_corpus` istantaneo),
con corpus reale + codici fondamentali, installer un clic, e ranking BM25 pesato su rubrica/titolo
(Fase A del piano di test conclusa, recall@8 19/26). 10 test verdi. Schede ri-ancorate a `889f843`.

Punto esatto in cui siamo: Fase A del piano di test conclusa con esito accettabile, MA resta un
drift di ranking da risolvere (dettaglio nelle domande aperte di `current-work.md`): concetti non
presenti nella rubrica non emergono, e rubriche omonime tra codici fanno vincere quello sbagliato
(es. "diffamazione" → art. 227 codici penali militari invece di 595 c.p.).

Prossime azioni, in ordine. Primo: risolvere il drift di ranking — leve candidate: preferire i
codici generali (civile/penale) sui speciali a parità di rubrica; affinare i pesi BM25; in ultima
istanza ibrido con embedding leggero CPU (ADR-003, Fase 4). Rimisurare con
`scripts/benchmark_retrieval.py`. Secondo (Fase B): creare il Project "Consulente Legale" in Claude
Desktop con le istruzioni di `prompts/consulente-legale.md` e provare dal vivo la batteria di
domande. Terzo (Fasi C/D): provare `install.cmd` su una macchina/utente pulito; provare
`update_corpus.py` (aggiornamento incrementale). Nota: dopo `git pull` o modifiche, rilanciare
`sync-context`. La pesatura BM25 richiede il riavvio di Claude Desktop per essere caricata dal server.
