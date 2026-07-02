# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:         main
Commit di riferimento: 995e154 (codice); fix del test dal vivo non ancora committato
Data snapshot:         2026-07-02
```

## Stato di verifica delle schede

HEAD reale è `995e154` (il primo affinamento del ranking, committato dall'utente col messaggio
proposto in sessione). Questa scheda e STACK.md e current-work.md hanno però contenuto aggiornato
oltre `995e154`, per descrivere il fix di un bug scoperto dal test dal vivo subito dopo quel commit
(vedi `fts.py`, non ancora committato): nessun drift, solo un secondo commit pendente.

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | 889f843 | contenuto aggiornato oltre `995e154` (fix bug limit=1 + bonus), commit pendente |
| design-and-security.md | 889f843 | allineata (strati, update, mitigazioni, path lunghi) |
| deployment.md | 889f843 | allineata (installer, setup, registrazione client) |
| dev-testing.md | 889f843 | allineata (pytest 12, fixture, benchmark) |
| current-work.md | 889f843 | contenuto aggiornato oltre `995e154` (residuo in 4 cause), commit pendente |
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

Codice committato fino a `995e154`: prodotto completo e verificato end-to-end in Claude Desktop
(cita artt. 157-161-bis c.p. con URN dal corpus, niente web; `info_corpus` istantaneo), con corpus
reale + codici fondamentali, installer un clic, e il primo affinamento del ranking (filtro stopword
italiane nella query MATCH, `_rubrica_bonus`, `_CODICE_GENERALE_BONUS`, sovra-campionamento a 50x)
committato in `995e154`. Subito dopo quel commit, il test dal vivo in Claude Desktop (Sonnet 4.6,
ragionamento alto, 6 query con `limit=1`, screenshot) ha dato 3/6 corrette, non 5/6 come misurato
dal benchmark con `limit=8`: ha scoperto un bug non colto dal benchmark (il sovra-campionamento
scalava su `limit`, crollando a 50 righe con `limit=1`, insufficienti per l'art. 644 c.p. su
"usura") e un bonus codici generali insufficiente a vincere il pareggio "diffamazione" in prima
posizione. Entrambi corretti nella stessa sessione, non ancora committati: `oversample = max(limit
* 50, 400)` e bonus codici generali alzato da -3/-2 a -6/-4. Risultato finale su
`scripts/benchmark_retrieval.py`: recall@1 10→14/26, recall@5 15→19/26, recall@8 invariato 19/26;
con `limit=1` esatto (come nel test dal vivo) 5/6 corrette via `fts.search` diretto. Riscontro dal
vivo in Claude Desktop non ancora ripetuto dopo il fix. Dettaglio completo in `current-work.md` e
nel work-log del 2026-07-02 (due voci: affinamento iniziale committato, poi fix del test dal vivo
pendente).

Punto esatto in cui siamo: il drift di ranking di Fase A è stato affinato e il residuo isolato in
quattro cause distinte, diagnosticate con query dirette sull'indice (non solo il benchmark
aggregato): rubriche nel corpus scollegate dal contenuto sostanziale dell'articolo (art. 633
c.p.c., art. 128 codice del consumo), variazione di lemma non colta dal matching per token esatto
("concorso" vs "concorrono", art. 110 c.p.), diluizione oltre ogni sovra-campionamento ragionevole
(art. 2087 c.c., 458° su quasi 79.000 corrispondenze), e ambiguità genuina tra norma generale e
norme speciali nello stesso codice ("risoluzione del contratto" → art. 1564 c.c. invece della
norma generale art. 1453 c.c.). Tutte e quattro richiedono l'ibrido con embedding leggero CPU
(ADR-003, Fase 4): nessun'altra leva lessicale su BM25 le risolve senza rischiare nuove
regressioni.

Prossime azioni, in ordine. Primo: ripetere il test dal vivo in Claude Desktop (stesso prompt, 6
query) dopo il riavvio dell'app, per confermare 5/6 anche a caldo, non solo da `fts.search` diretto.
Poi l'utente committa il fix del test dal vivo (`fts.py` + le 4 schede toccate in questa seconda
tornata; vedi comandi git dati in sessione) e si esegue un rapido ri-ancoraggio delle schede al
nuovo hash. Poi (Fase B): creare il Project
"Consulente Legale" in Claude Desktop con le istruzioni di
`prompts/consulente-legale.md` e provare dal vivo la batteria di domande, verificando anche a
occhio il miglioramento del ranking. Terzo (Fasi C/D): provare `install.cmd` su una macchina/utente
pulito; provare `update_corpus.py` (aggiornamento incrementale). Quarto, solo se serve ancora dopo
la Fase B: valutare l'ibrido con embedding (Fase 4, ADR-003) per le tre cause residue. Nota: dopo
`git pull` o modifiche, rilanciare `sync-context`. Ogni modifica a `fts.py`/`mcp_server.py` richiede
il riavvio di Claude Desktop (anche dalla tray) per essere caricata dal server.
