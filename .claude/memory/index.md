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
registrato come submodule), più la collezione supplementare `data/codici-extra` (tracciata, ~5.2 MB)
coi 5 codici fondamentali scaricati da Normattiva. Indice FTS5 in `data/index/legge.sqlite`
(~2.6 GB, gitignored): 287.816 atti, 966.126 chunk. Server MCP verificato sull'indice reale e in
Claude Desktop. I codici civile/penale/procedura civile (prima assenti) ora sono ricercabili
(art. 2043 c.c., 157 c.p., 112 c.p.c.). Limite di Windows sui path lunghi gestito dal codice
(`config.long_path`) e da `core.longpaths`, senza admin.

## Punto di ripresa

Fase 1 `6111cd3`, Fase 2 `f954aaa`, hardening/Fase 3/packaging `bd19b1d`, percorsi lunghi/vigenti/
dedup `88f3f61`, codici fondamentali `f516086`. Non ancora committato: verifica/hardening da Claude
Desktop (fix `info_corpus` via `state.json`, prompt rafforzato solo-legge-it, corpus come clone,
`install.ps1`/`install.cmd`, `.gitignore`), più le schede. Prodotto verificato end-to-end in Claude
Desktop: cita gli artt. 157-161-bis c.p. con URN dal corpus, niente web; `info_corpus` istantaneo.
10 test verdi.

Prossime azioni concrete. Primo: committare questo lotto (escludendo `data/index` e
`data/italia-corpus`), poi rilanciare `sync-context` per ri-ancorare le schede. Secondo (setup
permanente): creare il Project "Consulente Legale" in Claude Desktop con le istruzioni di
`prompts/consulente-legale.md`, così il comportamento solo-legge-it è stabile senza ripeterlo.
Terzo: provare `install.cmd` su una situazione pulita (altra macchina/utente) per validare
l'installazione da zero. Limiti noti: "vigente" esclude solo la collezione abrogate, non garantisce
la vigenza odierna (vale il disclaimer); ranking BM25 su query concettuali variabile, mitigato
dall'uso di `leggi_atto` per l'articolo puntuale (ADR-003, eventuale ibrido futuro).
