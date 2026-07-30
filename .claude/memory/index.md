# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:         main
Commit di riferimento: bae3b34 (feature auto-update + ri-ancoraggio schede, confermato committato
                        e pushato, verificato su git log e origin/main)
Data snapshot:         2026-07-06
```

## Stato di verifica delle schede

HEAD reale è `f7a4da9` (affinamento del ranking in `995e154`, fix del sovra-campionamento e del
bonus codici generali in `0d0667a`, registrazione della riconferma dal vivo in `f7a4da9`). Tutte
le schede sono ri-ancorate a `f7a4da9`: nessun drift residuo.

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | bae3b34 | allineata (corpus clone non submodule, `update.pull` fetch+reset, auto_update.py) |
| design-and-security.md | 69b154e | allineata (clone non submodule, fetch+reset per collisioni di case) |
| deployment.md | bae3b34 | allineata (setup.py hardened, auto_update.py, clone non submodule) |
| dev-testing.md | f7a4da9 | allineata (pytest 12, fixture, benchmark) |
| current-work.md | bae3b34 | allineata (Fasi C/D, hardening, auto-update, verifica robustezza installer) |
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
Con questo l'intero piano di test originario (Fasi B, C, D) è chiuso.

Nuovo fronte aperto su richiesta dell'utente: il target reale del prodotto sono avvocati e studi
legali senza alcuna competenza tecnica, quindi Fase C va approfondita con un test vero su macchina
vergine (non solo su questa macchina già configurata) e il pacchetto va reso a intervento manuale
nullo per quanto possibile. Windows Sandbox scelto come ambiente di test (Windows 11 Pro,
virtualizzazione presente); l'utente ha lanciato `Enable-WindowsOptionalFeature` ma il riavvio
richiesto è sospeso, quindi il test vero e proprio non è ancora partito. Nel frattempo, hardening
già fatto: `README.md` (guida al download ZIP senza git, avviso SmartScreen, aspettativa di durata,
passo di verifica finale); bug reale corretto in `scripts/setup.py::_corpus_presente` (un clone del
corpus interrotto a metà veniva scambiato per completo nei rilanci, ora verifica
`git rev-parse HEAD`); identità git locale placeholder aggiunta nel clone del corpus come rete di
sicurezza su richiesta esplicita dell'utente. Domanda aperta, senza risposta dall'utente finora: se
serva anche un canale di aggiornamento via git per il progetto legal-consultant stesso, non solo
per il corpus (proposta di chiarimento fatta due volte, senza risposta).

Chiarito il punto sull'account/canale git: l'utente intendeva l'aggiornamento automatico e
ricorrente dei dati (corpus + codici fondamentali), non un canale di distribuzione del progetto
stesso. Implementato: nuovo `scripts/auto_update.py` (corpus a ogni giro, codici al più
settimanale) registrato da `install.ps1` come attività pianificata di Windows
(`ConsulenteLegale-Aggiornamento`, giornaliera alle 6:00, senza privilegi di amministratore),
verificato end-to-end su questa macchina (registrazione, esecuzione manuale con
`LastTaskResult: 0`, log corretto su due giri). `README.md` e `HANDOFF.md` aggiornati.

Codice e schede pendenti da committare: `src/legal_consultant/update/__init__.py`, `README.md`,
`scripts/setup.py`, `scripts/auto_update.py` (nuovo), `install.ps1`, `HANDOFF.md`,
`current-work.md`, `roadmap.md`, `memory/index.md`, `memory/progress.md`, più i pendenti residui
di Fase C (`prompts/consulente-legale.md`, `src/legal_consultant/mcp_server.py`). Anche
`.git/modules` locale da 419 MB (residuo del vecchio submodule del corpus, mai pulito, solo su
questa macchina) segnalato ma non ancora ripulito, in attesa di conferma dell'utente.

Sessione del 2026-07-06: `sync-context` ha rilevato tre schede stale (STACK.md, deployment.md,
design-and-security.md, ferme a `f7a4da9` e ancora sul linguaggio "submodule"/`pull --ff-only`
superato dai commit `c281d37`/decisione clone-non-submodule); ri-ancorate a `69b154e` con delta
edit chirurgici, nessuna riscrittura strutturale. Rilevato anche un blocco di modifiche estraneo
in `.claude/templates/` (refresh dello scaffold di sistema da un meccanismo di sync a livello di
account, non legato al prodotto): committato a parte (`057d8f6`). L'utente ha poi scelto di non
attendere il riavvio per Windows Sandbox e di verificare la robustezza dell'installer
("se trova una cosa installata non lo rifà") direttamente su questa macchina di sviluppo, dove
git/uv sono già presenti: verifica isolata di `Ensure-Git`/`Ensure-Uv` (skip confermato, nessuna
chiamata a winget/installer uv) e poi l'intero `install.ps1` end-to-end, con esito positivo su
tutti e 5 gli step (dettaglio in `progress.md` e in `current-work.md`). Sostituisce nella
sostanza, pur non essendo una macchina vergine in senso stretto, il test Fase C su macchina
pulita rimasto sospeso.

Anomalia della sessione, risolta: il primo tentativo di commit della feature di aggiornamento
automatico, segnalato dall'utente come già fatto, non era in realtà mai avvenuto (assente da
`git log`/`git reflog`, solo il commit del template `057d8f6` era reale). Fatto ripetere: i
comandi sono stati ridati e l'esito verificato con `git log` e confrontato con `origin/main` prima
di considerarlo chiuso (`bae3b34`, working tree pulito, push confermato allineato al remoto).

Tutte le schede sono ri-ancorate a `bae3b34` (design-and-security.md resta valida a `69b154e`,
nessun file delle sue covers-paths è cambiato dopo): nessun drift residuo. Dopo, in commit
`c59778d`: due nuovi documenti tracciati sotto `docs/` (`flusso-e-architettura.md` con i tre
diagrammi di livello operativo/tecnico/linguistico, `mercato-privacy-e-token.md` con il
confronto di mercato, le evidenze di community/casi di allucinazione e la stima di token),
indicizzati in `CLAUDE.md`.

Punto di ripresa esatto: l'utente ha chiesto una valutazione di prontezza per il go-live su una
macchina vergine con Claude Desktop installato e loggato con un piano Team, e la risposta è
positiva con riserva d'osservazione, non un rinvio. Il progetto è pronto per quel test perché è
l'unico ramo del flusso di installazione mai esercitato davvero: tutte le verifiche precedenti di
`install.ps1` sono avvenute su questa macchina di sviluppo con git/uv/Python/Claude Desktop già
presenti, validando solo i rami di skip di `Ensure-Git`/`Ensure-Uv`, mai l'installazione reale
(`winget install --id Git.Git`, script ufficiale di `uv`). Tre rischi dichiarati ma non
osservati, da tenere d'occhio durante il test: disponibilità/attivazione di `winget` su
un'immagine Windows aziendale; `Refresh-Path` che potrebbe non intercettare un PATH scritto da
un installer MSI fuori da Machine/User env; rete dello studio con firewall/proxy che blocca
`github.com` o fa SSL inspection sul clone di ~2 GB del corpus. Consigliato di installare/loggare
Claude Desktop con l'account Team per primo e aprirlo almeno una volta prima di lanciare
`install.cmd`, per dare a `Find-ClaudeConfig` un file di configurazione già esistente da trovare
invece che da creare da zero (sequenza mai osservata dal vivo finora). Due gap minori non
bloccanti, aperti per una sessione futura se si vuole chiuderli: licenza di `italia-corpus`
verificata come MIT (permissiva, nessun problema) ma non documentata in nessun file del
progetto; `legal-consultant` non ha un proprio file `LICENSE` (irrilevante per uso interno allo
studio, da considerare solo se il repository dovesse circolare oltre lo studio che lo adotta).
Dettaglio completo in `current-work.md` e nel work-log del 2026-07-06.

Primo, alla ripresa: eseguire il test di go-live sulla macchina vergine seguendo la sequenza
sopra, osservando in particolare l'esito reale (non di skip) di `Ensure-Git`/`Ensure-Uv`.
Infine, solo se serve: valutare l'ibrido con embedding (Fase 4, ADR-003) per le tre cause residue
di ranking non riverificate dal vivo (rubrica scollegata art. 633 c.p.c., variazione di lemma
art. 110 c.p., diluizione art. 2087 c.c.), isolate ma non bloccanti. Nota: dopo `git pull` o
modifiche, rilanciare `sync-context`. Ogni modifica a `fts.py`/`mcp_server.py` richiede il
riavvio di Claude Desktop (anche dalla tray) per essere caricata dal server.

## Sessione del 2026-07-29/30 — completezza del corpus

Incarico esterno portato dall'utente in due file di desktop, scritti dal progetto tesi che aveva
scoperto dall'esterno l'assenza della L. 194/1978. Chiesto di misurare il difetto, diagnosticarlo e
renderlo non più silenzioso, non di aggiungere tre leggi.

Audit (`docs/audit-completezza-corpus.md`): il corpus non contiene la legge ordinaria, il
decreto-legge vigente e la Costituzione, perché rispecchia il catalogo delle 23 collezioni
preconfezionate di Normattiva e in quel catalogo la legge ordinaria non figura. Mancavano 9.313
leggi non abrogate su 13.730 (67,8%, di cui 2.755 modificate e vigenti), 1.584 decreti-legge non
abrogati su 1.636 (96,8%) e l'unico atto della tipologia COSTITUZIONE. I 287.805 atti dichiarati
sono file: gli atti distinti per URN sono 190.594. Corretta un'aspettativa dell'incarico: il codice
di procedura penale c'è, perché è il DPR 447/1988.

Correzione (ADR-005, `docs/completamento-corpus.md`): recupero dall'API Open Data ufficiale di
Normattiva, scoperta durante l'audit e non prevista dall'incarico, con export massivo asincrono in
Akoma Ntoso invece dello scraping per singolo atto. Nuovo package `src/legal_consultant/fonte/`,
nuovi script `fetch_normattiva.py`, `fetch_atto.py` e `check_completezza.py`, nuova radice
`data/normattiva-suppl` (ignorata da git), una sola regola aggiunta al parser condiviso (`## Allegato
I` apre un chunk, perché le 18 disposizioni transitorie della Costituzione vivono negli allegati).
30 test verdi. Recall di non-regressione invariato: 14/26, 19/26, 19/26 prima e dopo.

Giurisprudenza (ADR-006, `docs/giurisprudenza-fattibilita.md`): analisi soltanto, nessun codice. Se
si procederà, solo Corte costituzionale dagli open data ufficiali, tabella e tool distinti. Sulla
Cassazione non c'è un rischio da soppesare ma un divieto scritto che nomina la riproduzione su
supporto elettronico e il trattamento mediante sistemi di intelligenza artificiale.

Validazione non provocata, la più significativa: l'attività pianificata di Windows già registrata su
questa macchina ha eseguito da sola, la notte del 30 luglio alle 04:00 UTC, le fasi nuove nell'ordine
previsto e ha scritto nel proprio registro che il corpus ha ancora lacune, indicando il comando per
il dettaglio. Il percorso non presidiato funziona senza che nessuno lo tocchi.

Limite operativo accertato e non superabile lato progetto: il filtro di protezione della fonte impone
un tetto durevole per client sulla rotta di interrogazione dello stato di un export. Dopo un'attività
sostenuta risponde 409 per decine di minuti, mentre ricerca ed export continuano a rispondere. Un
recupero massivo va quindi distribuito su più giorni, e il codice lo riconosce: dopo otto rifiuti
consecutivi interrompe il giro dichiarando che non è un errore del progetto. Alla chiusura della
sessione sono recuperati la Costituzione (139 articoli + 18 allegati), la L. 194/1978, la L. 219/2017
e circa novecento atti fra leggi e decreti-legge, partendo dai più recenti.

Punto di ripresa, in ordine. Primo: committare il lavoro, che è tutto pendente (vedi la voce di
work-log per l'elenco dei file). Secondo: lasciare convergere il popolamento con l'attività
pianificata e controllare l'avanzamento con `uv run python scripts/check_completezza.py`, che alla
chiusura della sessione riporta 18 atti sentinella ancora assenti fra cui L. 184/1983, L. 833/1978,
L. 40/2004, L. 405/1975 e L. 24/2017. Terzo: quando le materie di interesse sono coperte, fare in
Claude Desktop la verifica che finora manca, cioè una domanda di chat completa su una legge ordinaria,
perché fin qui la L. 194/1978 è stata verificata attraverso il tool di ricerca e non in
conversazione. Quarto, opzionale: estendere `scripts/benchmark_retrieval.py` con domande sulle classi
recuperate, dato che le 26 attuali puntano tutte su codici e misurano la non-regressione e non il
guadagno. Quinto, se l'utente lo vuole: aprire a monte la segnalazione della lacuna, il cui testo è
pronto in `_notes/` e la cui pubblicazione è un'azione verso l'esterno che spetta a lui.
