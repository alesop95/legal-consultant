# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:         main
Commit di riferimento: f7a4da9 (registrazione riconferma dal vivo del ranking, 5/6)
Data snapshot:         2026-07-02
```

## Stato di verifica delle schede

HEAD reale è `f7a4da9` (affinamento del ranking in `995e154`, fix del sovra-campionamento e del
bonus codici generali in `0d0667a`, registrazione della riconferma dal vivo in `f7a4da9`). Tutte
le schede sono ri-ancorate a `f7a4da9`: nessun drift residuo.

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | f7a4da9 | allineata |
| design-and-security.md | f7a4da9 | allineata (strati, update, mitigazioni, path lunghi) |
| deployment.md | f7a4da9 | allineata (installer, setup, registrazione client) |
| dev-testing.md | f7a4da9 | allineata (pytest 12, fixture, benchmark) |
| current-work.md | f7a4da9 | contenuto aggiornato oltre `f7a4da9` (risultati Fase B), commit pendente |
| roadmap.md | f7a4da9 | allineata (benchmark misurato; ibrido come Fase 4) |

## Stato del corpus e dell'indice

Corpus reale clonato in `data/italia-corpus` (287.813 file, fuori da git: clone non ancora
registrato come submodule), più la collezione supplementare `data/codici-extra` (tracciata, ~5.2 MB)
coi 5 codici fondamentali scaricati da Normattiva. Indice FTS5 in `data/index/legge.sqlite`
(~2.6 GB, gitignored): 287.816 atti, 966.126 chunk. Server MCP verificato sull'indice reale e in
Claude Desktop. I codici civile/penale/procedura civile (prima assenti) ora sono ricercabili
(art. 2043 c.c., 157 c.p., 112 c.p.c.). Limite di Windows sui path lunghi gestito dal codice
(`config.long_path`) e da `core.longpaths`, senza admin.

## Punto di ripresa

Codice committato fino a `0d0667a`: prodotto completo e verificato end-to-end in Claude Desktop
(cita artt. 157-161-bis c.p. con URN dal corpus, niente web; `info_corpus` istantaneo), con corpus
reale + codici fondamentali, installer un clic, e il ranking affinato in due passaggi. Primo
(`995e154`): filtro stopword italiane nella query MATCH, `_rubrica_bonus`, `_CODICE_GENERALE_BONUS`,
sovra-campionamento a 50x. Il test dal vivo subito dopo (Sonnet 4.6, ragionamento alto, 6 query con
`limit=1`, screenshot_16.png/screenshot_17.png) ha dato solo 3/6 corrette, non 5/6 come misurato dal
benchmark con `limit=8`: ha scoperto un bug non colto dal benchmark (il sovra-campionamento scalava
su `limit`, crollando a 50 righe con `limit=1`, insufficienti per l'art. 644 c.p. su "usura") e un
bonus codici generali insufficiente a vincere il pareggio "diffamazione" in prima posizione.
Secondo (`0d0667a`): `oversample = max(limit * 50, 400)` e bonus codici generali alzato da -3/-2 a
-6/-4. Ripetuto lo stesso test dal vivo dopo il riavvio di Claude Desktop: 5/6 corrette
(screenshot_01.png), confermato — resta sbagliata solo "risoluzione del contratto per
inadempimento" (residuo noto, non un bug). Risultato finale su `scripts/benchmark_retrieval.py`:
recall@1 10→14/26, recall@5 15→19/26, recall@8 invariato 19/26. Il task di affinamento del ranking
è chiuso. Dettaglio completo in `current-work.md` e nel work-log del 2026-07-02 (tre voci:
affinamento iniziale, fix del test dal vivo, riconferma).

Punto esatto in cui siamo: il drift di ranking di Fase A è stato affinato, corretto e riconfermato
dal vivo. Il residuo è isolato in quattro cause distinte, diagnosticate con query dirette
sull'indice (non solo il benchmark aggregato): rubriche nel corpus scollegate dal contenuto
sostanziale dell'articolo (art. 633 c.p.c., art. 128 codice del consumo), variazione di lemma non
colta dal matching per token esatto ("concorso" vs "concorrono", art. 110 c.p.), diluizione oltre
ogni sovra-campionamento ragionevole (art. 2087 c.c., 458° su quasi 79.000 corrispondenze), e
ambiguità genuina tra norma generale e norme speciali nello stesso codice ("risoluzione del
contratto" → art. 1564 c.c. invece della norma generale art. 1453 c.c.). Tutte e quattro
richiedono l'ibrido con embedding leggero CPU (ADR-003, Fase 4): nessun'altra leva lessicale su
BM25 le risolve senza rischiare nuove regressioni. Non sono bloccanti per l'uso quotidiano.

Prossime azioni, in ordine. Fase B conclusa (8/8, commit `d8ca083`). Raffinate le istruzioni del
Project e il prompt gemello `consulenza_legale` (chiarimento su domande multi-disciplina, citazione
letterale delle disposizioni brevi) e aggiunto un diagramma di flusso as-built a `HANDOFF.md`
(commit `1da975d`). Fase C conclusa: `install.ps1` verificato su questa macchina già attiva (non
vergine), indice ricostruito correttamente (287.816 atti, 966.126 chunk, 418s), altri server MCP
preservati, validazione end-to-end su una domanda di sintesi complessa con citazione letterale
sistematica e dichiarazione corretta dei limiti del corpus. Effetto collaterale noto e non
bloccante: l'installer rimuove `pytest` su una macchina di sviluppo (`uv sync` senza `--extra dev`),
ripristinato manualmente qui. Fase D chiusa: `update_corpus.py` fallito al primo lancio su un limite strutturale del corpus mai
emerso prima (collisione di path che differiscono solo per case, incompatibile con
`core.ignorecase=true` di Windows), corretto in `update.pull()` (fetch + reset --hard invece di
pull --ff-only) e ritestato con successo (1010 atti aggiornati, corpus avanzato a `086a90b8`, 12
test verdi). `fetch_codici.py` ritestato: 5/5 codici riscaricati alla vigenza odierna, nessuna
differenza rispetto ai file tracciati (nessuna modifica legislativa nel periodo, non un difetto).
Con questo l'intero piano di test (Fasi B, C, D) è chiuso. Codice e schede pendenti da committare.
Primo, ora: l'utente committa (`src/legal_consultant/update/__init__.py`, `current-work.md`,
`memory/index.md`, `memory/progress.md`, più i pendenti di Fase C: `HANDOFF.md`,
`prompts/consulente-legale.md`, `src/legal_consultant/mcp_server.py`). Poi, solo se serve: valutare
l'ibrido con embedding (Fase 4, ADR-003) per le tre cause residue di ranking non riverificate dal
vivo (rubrica scollegata art. 633 c.p.c., variazione di lemma art. 110 c.p., diluizione art. 2087
c.c.), isolate ma non bloccanti — nessuna urgenza, il prodotto è completo e verificato end-to-end
su tutte le fasi pianificate. Nota: dopo `git pull` o modifiche, rilanciare `sync-context`. Ogni
modifica a `fts.py`/`mcp_server.py` richiede il riavvio di Claude Desktop (anche dalla tray) per
essere caricata dal server.
