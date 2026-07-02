# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:         main
Commit di riferimento: 09b5ec1 (codice); affinamento ranking non ancora committato
Data snapshot:         2026-07-02
```

## Stato di verifica delle schede

Tutte le schede committate sono ri-ancorate a HEAD (`09b5ec1`, che coincide con `889f843` per il
codice). STACK.md e current-work.md hanno contenuto aggiornato in anticipo sul prossimo commit,
per descrivere l'affinamento del ranking già scritto su disco ma non ancora committato (vedi
`fts.py`): nessun drift, solo un commit pendente.

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | 889f843 | contenuto aggiornato (ranking: stopword + bonus rubrica/codici generali), commit pendente |
| design-and-security.md | 889f843 | allineata (strati, update, mitigazioni, path lunghi) |
| deployment.md | 889f843 | allineata (installer, setup, registrazione client) |
| dev-testing.md | 889f843 | allineata (pytest 12, fixture, benchmark) |
| current-work.md | 889f843 | contenuto aggiornato (affinamento ranking, residuo in 3 cause), commit pendente |
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

Codice committato fino a `09b5ec1`: prodotto completo e verificato end-to-end in Claude Desktop
(cita artt. 157-161-bis c.p. con URN dal corpus, niente web; `info_corpus` istantaneo), con corpus
reale + codici fondamentali, installer un clic, e ranking BM25 pesato su rubrica/titolo (Fase A del
piano di test conclusa, recall@8 19/26). Da committare: l'affinamento del ranking di questa
sessione (`fts.py`, `benchmark_retrieval.py`, `tests/test_pipeline.py`, 12 test verdi) — filtro
stopword italiane nella query MATCH, `_rubrica_bonus` (corrispondenza rubrica-domanda),
`_CODICE_GENERALE_BONUS` (spareggio sui codici generali), sovra-campionamento a 50x. Risultato:
recall@1 10→13/26, recall@5 15→19/26, recall@8 invariato 19/26 ma con risultati molto più in alto
in classifica. Dettaglio completo in `current-work.md` e nel work-log del 2026-07-02.

Punto esatto in cui siamo: il drift di ranking di Fase A è stato affinato e il residuo isolato in
tre cause distinte, diagnosticate con query dirette sull'indice (non solo il benchmark aggregato):
rubriche nel corpus scollegate dal contenuto sostanziale dell'articolo (art. 633 c.p.c., art. 128
codice del consumo), variazione di lemma non colta dal matching per token esatto ("concorso" vs
"concorrono", art. 110 c.p.), e diluizione oltre ogni sovra-campionamento ragionevole (art. 2087
c.c., 458° su quasi 79.000 corrispondenze). Tutte e tre richiedono l'ibrido con embedding leggero
CPU (ADR-003, Fase 4): nessun'altra leva lessicale su BM25 le risolve.

Prossime azioni, in ordine. Primo: l'utente committa l'affinamento del ranking (vedi comandi git in
fondo a questa sessione) e poi si esegue un rapido ri-ancoraggio delle schede al nuovo hash. Secondo
(Fase B): creare il Project "Consulente Legale" in Claude Desktop con le istruzioni di
`prompts/consulente-legale.md` e provare dal vivo la batteria di domande, verificando anche a
occhio il miglioramento del ranking. Terzo (Fasi C/D): provare `install.cmd` su una macchina/utente
pulito; provare `update_corpus.py` (aggiornamento incrementale). Quarto, solo se serve ancora dopo
la Fase B: valutare l'ibrido con embedding (Fase 4, ADR-003) per le tre cause residue. Nota: dopo
`git pull` o modifiche, rilanciare `sync-context`. Ogni modifica a `fts.py`/`mcp_server.py` richiede
il riavvio di Claude Desktop (anche dalla tray) per essere caricata dal server.
