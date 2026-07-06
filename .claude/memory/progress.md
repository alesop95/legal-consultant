# Work-log

> Append-only, in ordine cronologico inverso (la voce più recente in alto). Ogni passo
> significativo di codice e ogni intervento manuale rilevante lascia una voce con data, file
> toccati, motivo e commit di riferimento. Qui confluisce anche il log di riconciliazione dei
> documenti `.docx`, con il nome del documento sorgente e l'esito, così la data di allineamento
> sopravvive a un clone.

## 2026-07-06 — Valutazione di prontezza per il go-live su macchina vergine

Commit di riferimento: `c59778d` (nessun file di codice toccato, solo analisi). Contesto:
l'utente ha chiesto cosa manca prima di un primo test reale su una macchina vergine con Claude
Desktop installato e loggato con un piano Team. Risposta: il progetto è pronto per quel test,
perché è l'unico ramo del flusso di installazione mai esercitato davvero. Tutte le verifiche
precedenti di `install.ps1` (Fase C, e la verifica di robustezza del turno precedente) sono
avvenute su questa macchina di sviluppo con git/uv/Python/Claude Desktop già presenti da prima:
hanno validato solo i rami "già installato, salto" di `Ensure-Git`/`Ensure-Uv`, mai i rami reali
di installazione (`winget install --id Git.Git`, script ufficiale di `uv`). Individuati tre
rischi dichiarati come tali, non osservati: disponibilità/attivazione di `winget` su
un'immagine Windows aziendale, `Refresh-Path` che potrebbe non intercettare un PATH scritto da
un installer MSI in un punto diverso da Machine/User env, e rete dello studio con
firewall/proxy che blocca `github.com` o fa SSL inspection sul clone di ~2 GB del corpus.
Individuata anche una sequenza mai osservata dal vivo: login a Claude Desktop con account Team
seguito dall'installer, dato che sulla macchina di sviluppo Claude Desktop era già configurato
da sessioni precedenti. Due gap minori non bloccanti: licenza di `italia-corpus` verificata ora
come MIT (permissiva, nessun problema per uso professionale) ma non documentata in nessun file
del progetto; `legal-consultant` non ha un proprio file `LICENSE` (irrilevante per uso interno
allo studio, da considerare solo se il repository dovesse circolare oltre lo studio che lo
adotta). Nessuna azione di codice in questo passo: solo la valutazione, registrata su richiesta
esplicita dell'utente prima di procedere al test.

## 2026-07-06 — Nuovi documenti su flusso operativo, architettura a tre livelli e privacy

Commit: `c59778d`. File toccati: `docs/flusso-e-architettura.md` (nuovo),
`docs/mercato-privacy-e-token.md` (nuovo), `CLAUDE.md` (indice dei satelliti tracciati).
Motivo: richiesta esplicita dell'utente di un flusso operativo completo per una postazione di
studio legale, diagrammi a tre livelli di lettura del progetto (operativo, tecnico,
linguistico), un confronto con gli strumenti di AI legale a pagamento e cloud-based, una
ricerca di community/benchmark, e una stima di utilizzo giornaliero in token. Ricerca condotta
con due agenti sequenziali (non in workflow parallelo, su richiesta esplicita dell'utente per
economia di token): il primo sul panorama degli strumenti a pagamento (Harvey, CoCounsel,
Lexis+ AI, vLex, Spellbook, Robin AI, Luminance, TeamSystem/Zucchetti/Wolters Kluwer in Italia)
con modello dati e fonti citate; il secondo su evidenze di community (dev.to, Reddit, Hacker
News) e una tabella di casi giudiziari reali di allucinazione AI con sanzioni fino a 110.000 $
(fonte: database di Damien Charlotin). `docs/flusso-e-architettura.md` include due diagrammi
mermaid nuovi (moduli di codice a livello tecnico, pipeline di parsing/query a livello
linguistico) a complemento, non duplicazione, del diagramma di flusso dati as-built già in
`HANDOFF.md` §4.1. La stima di token in `mercato-privacy-e-token.md` è ancorata a fatti
verificabili nel codice (`snippet()` FTS5 a 16 token, `limit=8` di default in
`cerca_normativa`) invece che a cifre di piano Anthropic non verificabili come attuali nel
tempo.

## 2026-07-06 — Verifica di robustezza dell'installer su macchina reale non vergine

Commit di riferimento: nessuno (verifica, nessun file di codice toccato). Contesto: l'utente ha
scelto di procedere con un test reale su questa macchina di sviluppo invece di attendere il
riavvio per Windows Sandbox, poiché git e uv sono già presenti ("il mio windows è quasi vergine
sotto questo punto di vista... verifichiamo la robustezza del fatto che se trova una cosa
installata non lo rifà"). Due passaggi.

Primo, verifica isolata: estratte le sole definizioni di funzione di `install.ps1` (dot-source
delle righe 1-136, senza eseguire il corpo principale) e lanciate `Ensure-Git`/`Ensure-Uv` a
mano. Confermato che `Get-Command` intercetta git 2.54.0 e uv 0.11.21 già presenti e le funzioni
ritornano subito con "gia' presente", senza invocare `winget` né l'installer di uv.

Secondo, su richiesta esplicita di spingere la verifica end-to-end: lanciato l'intero
`install.ps1` (tutti e 5 gli step nel flusso composto, incluso `Register-AutoUpdate` mai
verificato prima dentro questo flusso, solo isolatamente). Esito, esente da errori (exit 0):
step 1/5 e 2/5 skip confermati anche in composizione; step 3/5, `_corpus_presente` ha rilevato il
clone esistente e saltato il download, `uv sync` ha rimosso `pytest` e le sue dipendenze (stesso
effetto collaterale noto di Fase C, non un difetto nuovo, corretto qui con `uv sync --extra dev`
subito dopo, 12 test verdi), l'indice si è ricostruito da zero per design (`bootstrap_index.py`
non ha logica incrementale, cancella e riscrive sempre): 287.827 atti, 966.304 chunk, 23 errori
noti (caratteri di controllo in alcuni filename storici, stesso conteggio delle esecuzioni
precedenti), 266s; step 4/5, la voce `legge-it` è stata riscritta con backup automatico nel
config della build Store di Claude Desktop (`Claude_pzs8sxrjxfjjc`); step 5/5, l'attività
pianificata `ConsulenteLegale-Aggiornamento` è stata ri-registrata puliata (unregister + register,
nessun duplicato). Risultato: la logica di rilevamento "se trovato, non rifare" è confermata
empiricamente per git, uv e clone del corpus; l'unico passo sempre-rifatto (l'indice) lo è per
scelta di design già nota, non per un difetto di rilevamento. Sostituisce nella sostanza, pur non
essendo una macchina vergine in senso stretto, il test pianificato su Windows Sandbox (riavvio
per abilitare la virtualizzazione ancora sospeso, non più bloccante per procedere).

## 2026-07-06 — Ri-ancoraggio di tre schede stale (sync-context)

Commit di riferimento: `69b154e` (nessun commit nuovo, solo edit delle schede). File toccati:
`.claude/context/STACK.md`, `.claude/context/deployment.md`, `.claude/context/design-and-security.md`.
Motivo: `sync-context` a inizio sessione ha rilevato che le tre schede, ferme a `f7a4da9`, parlavano
ancora del corpus come submodule git e di `update.pull()` come `git pull --ff-only`, entrambi
superati dai commit `c281d37` (fetch + reset --hard per la collisione di case su Windows) e dalla
decisione precedente di trattare il corpus come clone locale ignorato da git, non un submodule.
Corretto il linguaggio nelle tre schede (nessuna riscrittura strutturale) e aggiunta menzione di
`scripts/auto_update.py` in STACK.md e deployment.md, a beneficio della sessione che committerà
quella feature. `last-verified-commit` delle tre schede portato a `69b154e`. `current-work.md` non
toccato in questo passo: il suo contenuto era già aggiornato oltre `f7a4da9` ma con un commit
pendente separato (vedi voce sotto), quindi il suo ri-ancoraggio avverrà dopo quel commit.

## 2026-07-03 — Aggiornamento automatico non presidiato (nuova feature)

Commit: nessuno (pendente). File toccati: `scripts/auto_update.py` (nuovo), `install.ps1`,
`README.md`, `HANDOFF.md`.
Motivo: richiesta esplicita dell'utente, dopo due domande di chiarimento senza risposta a cui ha
poi risposto direttamente: "il progetto... deve sempre aggiornarsi da solo con git rispetto alla
repo del corpus e alle altre fonti", nel quadro del target reale (avvocati/studi legali, zero
competenza tecnica, intervento manuale nullo per quanto possibile). Creato
`scripts/auto_update.py`: orchestra l'aggiornamento del corpus principale (ogni esecuzione) e dei
codici fondamentali (al più settimanale, tracciato in un marcatore locale, per non interrogare
Normattiva e uno strumento di terze parti ogni giorno per contenuti che cambiano raramente),
riusando `update.reindex_paths` anche per la collezione `EXTRA_CORPUS_PATH` (non un repo git: la
funzione è pura, non lo richiede). Ogni fase e' isolata in try/except e loggata su
`data/index/auto_update.log`, non solleva mai verso il chiamante, così un'esecuzione non presidiata
non fallisce vistosamente per un problema di rete transitorio. Aggiunta a `install.ps1` la
funzione `Register-AutoUpdate` (nuovo step 5/5): registra l'attività pianificata di Windows
`ConsulenteLegale-Aggiornamento` (giornaliera alle 6:00, `-StartWhenAvailable`, nessun privilegio
di amministratore, nessuna credenziale salvata: `-LogonType Interactive`), con fallback a un
avviso non bloccante se la registrazione fallisse. Verificato end-to-end su questa macchina, da
utente non amministratore: registrazione riuscita, esecuzione manuale via `Start-ScheduledTask`
con `LastTaskResult: 0`, log corretto su due giri consecutivi (primo: corpus già aggiornato,
codici scaricati e reindicizzati, 7428 chunk; secondo: codici correttamente saltati perché
aggiornati da meno di una settimana). Attività lasciata registrata anche su questa macchina di
sviluppo, uso reale previsto. `README.md` (sezione aggiornamento) e `HANDOFF.md` (diagramma
as-built) aggiornati di conseguenza. 12 test verdi dopo ogni modifica.

## 2026-07-03 — Hardening scatola chiusa in preparazione del test su macchina vergine

Commit: nessuno (pendente). File toccati: `README.md`, `scripts/setup.py`.
Motivo: discusso con l'utente il target reale del prodotto (avvocati e studi legali, zero
conoscenza tecnica, intervento manuale nullo per quanto possibile) e pianificato un test in
Windows Sandbox su macchina vergine (Windows 11 Pro, virtualizzazione presente; feature abilitata
dall'utente ma in attesa del riavvio, quindi il test vero e proprio resta sospeso). Nel frattempo,
tre correzioni concrete emerse dal ragionamento su questo target: `README.md` ora guida chi non
conosce git al download ZIP da GitHub, avvisa del possibile blocco SmartScreen sugli script non
firmati con l'istruzione per sbloccarlo, dà un'aspettativa di durata realistica (15-20 minuti) e un
passo di verifica finale. Trovato e corretto un bug reale in `_corpus_presente` (setup.py): un
controllo di sola non-vuotezza della cartella avrebbe scambiato un clone del corpus interrotto a
metà (connessione caduta durante il primo setup) per uno completo nei rilanci successivi, lasciando
un indice silenziosamente incompleto senza errore; ora verifica `git rev-parse HEAD` e ricrea il
clone se non valido, verificato con un clone finto in una cartella di scratch. Aggiunta anche
un'identità git locale placeholder (mai globale) nel clone del corpus, come rete di sicurezza
difensiva su richiesta esplicita dell'utente, pur non avendo trovato un caso concreto in cui il
flusso attuale (clone HTTPS anonimo pubblico) richieda oggi credenziali. Domanda aperta con
l'utente, non ancora risolta: se in futuro serva anche un canale di aggiornamento via git per il
progetto stesso (non solo per il corpus), da riprendere quando risponde. 12 test verdi dopo ogni
modifica.

## 2026-07-03 — Fase D chiusa: fetch_codici.py verificato, piano di test completo

Commit: nessuno (pendente). File toccati in questa voce: `.claude/context/current-work.md`
(chiusura Fase D, pulizia di due note obsolete: riferimento residuo al submodule git, e
riconciliazione).
Motivo: rilanciato `scripts/fetch_codici.py`, confermato esplicitamente dall'utente prima
dell'esecuzione perché contatta Normattiva e uno strumento di terze parti (`normattiva2md` via
`uvx`). Riscaricati tutti e 5 i codici fondamentali alla vigenza odierna (2026-07-03); `git diff`
non rileva alcuna differenza rispetto ai file già tracciati, segno che questi codici non hanno
subito modifiche legislative dal 30 giugno, non un difetto dello script: conferma che il fetch è
deterministico e riproducibile. Nessun reindex necessario. Con questo si chiude l'intero piano di
test (Fasi B, C, D); resta come backlog non urgente il solo ibrido con embedding (Fase 4,
ADR-003) per le tre cause di ranking isolate in Fase A e non riverificate dal vivo.

## 2026-07-03 — Fase D: fix di update_corpus.py su collisione di case Windows

Commit: nessuno (pendente). File toccati: `src/legal_consultant/update/__init__.py` (`pull()` e
docstring del modulo).
Motivo: primo lancio di `scripts/update_corpus.py` fallito su `git pull --ff-only`, rifiutato per
"modifiche locali" nel clone del corpus. Diagnosi: il corpus contiene, nella stessa revisione,
path che differiscono solo per maiuscole/minuscole (verificato con
`git ls-tree -r --name-only HEAD | tolower | sort | uniq -d`, trovate collisioni reali, es. due
varianti di "...dell'Ente nazionale idrocarburi.md"); su Windows, con `core.ignorecase=true` di
default, il checkout dell'uno sovrascrive fisicamente l'altro sullo stesso file, lasciando sempre
alcune voci "modificate" rispetto all'indice. Confermato empiricamente su richiesta esplicita
dell'utente (comando `git reset --hard HEAD` lanciato dall'utente stesso con `!`, bloccato per me
dal deny di `.claude/settings.json` su reset/rebase): 357 file modificati prima, 357 modificati
(nomi in parte diversi) subito dopo un reset pulito. Non e' un problema di questa sessione ne' un
bug transitorio: e' una proprieta' strutturale del corpus su Windows, che avrebbe fatto fallire
`update_corpus.py` a ogni futuro aggiornamento. Corretta `update.pull()`: da `git pull --ff-only`
a `git fetch --depth 1` + `git reset --hard @{u}`, che scarta sempre le modifiche locali invece di
proteggerle, corretto per un mirror locale di sola lettura mai editato a mano. Corretta anche la
docstring del modulo, che citava ancora erroneamente un submodule git. Ritestato con successo:
`def703b2 -> 086a90b8: 1010 atti aggiornati, 0 rimossi, 21.877 chunk reinseriti`; 12 test verdi;
corpus avanzato al commit del 2026-07-03.

## 2026-07-03 — Fase C: installer verificato su macchina già attiva + raffinamento istruzioni

Commit: `1da975d` (raffinamento istruzioni e diagramma; l'esecuzione dell'installer non tocca
codice). File toccati in questa voce: `.claude/context/current-work.md`.
Motivo: prima del lancio, corretto un refuso non di questa sessione in `prompts/consulente-legale.md`
(backtick mancante, paragrafi ri-scritti su riga unica) e raffinate le istruzioni del Project e il
prompt gemello `consulenza_legale` in `mcp_server.py`: aggiunta la richiesta di chiedere un
chiarimento quando la domanda copre discipline/procedure distinte (formalizza il comportamento
osservato nella domanda 8 di Fase B) e di riportare il testo letterale delle disposizioni brevi tra
virgolette oltre alla sintesi, pensato per uno studio legale che deve poter citare alla lettera.
Aggiunto anche un diagramma di flusso as-built in `HANDOFF.md` (Mermaid, sezione 4.1). Eseguito poi
`install.ps1` su questa macchina, già configurata e con Claude Desktop chiuso per il test: rileva
git/uv presenti, salta il download del corpus, ricostruisce l'indice da zero (287.816 atti, 966.126
chunk, 23 errori noti, 418s contro i 744s storici), preserva gli altri due server MCP nel config di
Claude Desktop con backup automatico, registra `legge-it`. Effetto collaterale noto: `uv sync` senza
`--extra dev` rimuove `pytest` (corretto per l'utente finale; ripristinato qui con
`uv sync --extra dev`, 12 test verdi). Validazione end-to-end dopo il riavvio di Claude Desktop: una
domanda di sintesi complessa (comunione vs separazione dei beni nel matrimonio) ha prodotto una
trattazione con citazione letterale sistematica di ogni articolo (artt. 159-219, 2647 c.c.), tabella
comparativa, sezione operativa "quando conviene ciascun regime", e una dichiarazione esplicita e
corretta del limite del corpus (solo testo legislativo, non giurisprudenza) sul fondo patrimoniale.
Fase C chiusa con esito pienamente positivo; il raffinamento delle istruzioni si conferma efficace
su un caso reale, non solo sulla batteria sintetica di Fase B.

## 2026-07-03 — Fase B conclusa: batteria di domande 8/8 superate

Commit: nessuno (verifica manuale in Claude Desktop, nessun file di codice toccato).
File toccati: `.claude/context/current-work.md` (checklist e narrativa completate).
Motivo: completate le ultime due domande della batteria, sospesa nella sessione precedente per
limite di Claude Desktop. Domanda 7 (`info_corpus`): tabella completa di freschezza (30 giugno
2026, 287.790 atti, 966.126 chunk), scarto corretto rispetto alla data odierna, limiti strutturali
richiamati con continuità dalla risposta precedente sul Reg. UE 2023/988. Domanda 8 (query
generica su una multa): primo turno pone una domanda di chiarimento invece di rispondere a memoria
o cercare sul web (comportamento ragionevole, procedure di ricorso diverse per tipo di sanzione);
al chiarimento cerca e cita correttamente D.Lgs. 285/1992 artt. 203-204 e D.Lgs. 150/2011 art. 7,
con confronto dei due canali di ricorso. Fase B chiusa: 8/8 superate, nessun comportamento fuori
disciplina in tutta la batteria.

## 2026-07-02 — Fase B: Project "Consulente legale" e batteria di domande (6/8)

Commit: nessuno (verifica manuale in Claude Desktop, nessun file di codice toccato).
File toccati: `.claude/context/current-work.md` (definition of done e narrativa dei risultati).
Motivo: creato il Project "Consulente legale" in Claude Desktop con le istruzioni di
`prompts/consulente-legale.md` incollate senza modifiche (verificato su screenshot) e il tool
`legge-it` collegato. Eseguita dal vivo una batteria di otto domande pensata per coprire ambiti
diversi del corpus e la disciplina comportamentale delle istruzioni, non solo il ranking già
chiuso in Fase A. Esito delle 6 completate: tutte superate. Due risultati di rilievo oltre alla
tenuta generale: le istruzioni del Project (prova più formulazioni, usa `leggi_atto` se conosce
l'articolo) hanno risolto in pratica due dei quattro casi critici residui di Fase A senza bisogno
dell'ibrido con embedding (risoluzione del contratto per inadempimento → art. 1453 c.c. corretto;
garanzia di conformità → art. 128 codice del consumo corretto); e sulla domanda sul Reg. UE
2023/988, assente dal corpus, il modello ha dichiarato esplicitamente l'assenza, evitato la
ricerca web e la risposta a memoria, e costruito comunque una risposta operativa onesta sulla
cornice nazionale di raccordo effettivamente presente. Domande 7 (freschezza corpus, già
validata spontaneamente in quasi tutte le risposte) e 8 (query generica) sospese per limite di
sessione di Claude Desktop raggiunto (reset alle 19:00), da completare alla ripresa.

## 2026-07-02 — Ri-ancoraggio delle schede a f7a4da9, avvio Fase B

Commit: `f7a4da9` (registrazione riconferma dal vivo, già presente in HEAD a inizio sessione).
File toccati: `.claude/context/STACK.md`, `design-and-security.md`, `deployment.md`,
`dev-testing.md`, `current-work.md`, `roadmap.md` (solo bump `last-verified-commit` a `f7a4da9`,
nessuna riscrittura di contenuto), `.claude/memory/index.md` (commit di riferimento, tabella di
stato, punto di ripresa).
Motivo: `sync-context` a inizio sessione ha rilevato che il commit `f7a4da9`, descritto
dall'ultima voce come "pendente", era in realtà già in HEAD; il solo drift residuo era il
puntatore `last-verified-commit` delle sei schede, ancora fermo a `889f843`/`0d0667a`. Nessun file
di codice coperto dalle schede è cambiato oltre quanto già descritto nel contenuto (`fts.py` per il
ranking, già narrato). Confermato con l'utente prima di scrivere. Chiude la formalità di
ri-ancoraggio pianificata come primo passo prima della Fase B; segue l'avvio della Fase B (Project
"Consulente Legale" in Claude Desktop + batteria di domande).

## 2026-07-02 — Riconferma dal vivo in Claude Desktop dopo il fix

Commit: nessuno (verifica, nessun file di codice toccato)
File toccati: nessuno.
Motivo: ripetuto in Claude Desktop (Sonnet 4.6, ragionamento alto), dopo il riavvio dell'app e il
commit `0d0667a`, lo stesso identico prompt di verifica sulle 6 query con `limit=1`
(screenshot_01.png). Esito: 5/6 corrette (furto, omicidio, usura, diffamazione, truffa), come
previsto dalla verifica diretta via `fts.search` della voce precedente. L'unico errore, "risoluzione
del contratto per inadempimento" → art. 1564 c.c. invece di 1453, è il residuo noto (ambiguità
norma generale/norme speciali nello stesso codice); il modello lo ha diagnosticato correttamente da
sé in chat come limite del ranking lessicale, senza che gli fosse stato detto. Chiude il ciclo
affinamento-test-fix-riconferma iniziato con la richiesta di affinare il motore di ricerca.

## 2026-07-02 — Fix del test dal vivo: sovra-campionamento legato a `limit`, bonus codici generali insufficiente

Commit: 0d0667a
File toccati: `src/legal_consultant/index/fts.py` (`search`: `oversample = max(limit * 50, 400)`
invece di `limit * 50`; `_CODICE_GENERALE_BONUS` da -3/-2 a -6/-4 su civile/penale/proc. civile).
Motivo: test dal vivo in Claude Desktop (Sonnet 4.6, ragionamento alto) col prompt di verifica
sulle 6 query del benchmark, con `limit=1` per isolare il primo risultato (screenshot_16.png,
screenshot_17.png). Esito: 3/6 corrette, non 5/6 come misurato dal benchmark con `limit=8`. Causa:
il sovra-campionamento scalava linearmente su `limit` (`limit * 50`), quindi con `limit=1` la
finestra di ricalcolo crollava a 50 righe grezze, troppo poco per recuperare l'art. 644 c.p.
("usura", 77° grezzo) prima che il bonus potesse agire; corretto con un minimo fisso di 400,
indipendente da quanti risultati il chiamante vuole alla fine. Trovata anche una seconda causa
distinta: anche a campione capiente, "diffamazione" restava in prima posizione l'art. 227 dei
codici penali militari, perché lo scarto di BM25 grezzo tra 227 e 595 (~4.6 punti, per occorrenze
di "reato" nel corpo dell'art. 227) superava il bonus codici generali di -3; alzato a -6 per
civile/penale, -4 per procedura civile. Rimisurato su `scripts/benchmark_retrieval.py`: recall@1
10→14/26 (da 13), invariati recall@5 19/26 e recall@8 19/26; verificato anche con `fts.search(...,
limit=1)` diretto sulle stesse 6 query di Claude Desktop: 5/6 corrette (solo "risoluzione del
contratto per inadempimento" resta sbagliata, ambiguità nota tra norma generale e speciali dello
stesso codice). Riscontro dal vivo in Claude Desktop non ancora ripetuto dopo il fix. Lezione
operativa: il benchmark con `limit=8` non intercetta bug legati a `limit` piccoli; da qui in avanti
vale la pena misurare anche a `limit=1` quando si cambia la logica di sovra-campionamento. `uv run
pytest` → 12 verdi.

## 2026-07-02 — Affinamento del ranking del retrieval (stopword, bonus rubrica, bonus codici generali)

Commit: 995e154
File toccati: `src/legal_consultant/index/fts.py` (`to_match_query` filtra le stopword italiane;
nuove `_content_tokens`, `_rubrica_bonus`, `_CODICE_GENERALE_BONUS`; `search` ricalcola il
punteggio su un campione sovra-campionato a 50x il `limit` e riordina prima della deduplica);
`scripts/benchmark_retrieval.py` (colonna "+bonus" che passa per `fts.search` reale);
`tests/test_pipeline.py` (+2 test: filtro stopword, `_rubrica_bonus`). Aggiornate le schede
`current-work.md` e `STACK.md`.
Motivo: primo task aperto della sessione precedente, il drift di ranking di Fase A. Diagnosticato
con query dirette sull'indice reale (non solo il benchmark aggregato): la query MATCH includeva le
stopword, quindi "concorso di persone nel reato" abbinava 455.831 righe solo per "di"/"nel"; BM25
penalizza le rubriche brevi ed esatte a favore di varianti più lunghe che ripetono la stessa parola
nel corpo, e non distingue un codice generale da un suo omonimo di settore. Tre correttivi, ognuno
verificato empiricamente col benchmark prima di tenerlo: filtro stopword nella query MATCH;
`_rubrica_bonus` calibrato per magnitudine (i primi tentativi a -22/-9 causavano regressioni su
query di diritto civile dove più articoli condividono rubriche brevi legittimamente simili, es.
"Risoluzione del contratto" ricorre in più norme oltre all'art. 1453 c.c.; assestato a -8/-3);
sovra-campionamento alzato da 5x a 50x perché il bonus non può salvare un articolo già escluso dal
campione grezzo (l'art. 644 c.p. per "usura" era 77° su 472 corrispondenze). Risultato: recall@1
10→13/26, recall@5 15→19/26, recall@8 invariato 19/26 ma con risultati molto più in alto in
classifica. Isolate con query dirette le tre cause del residuo (non più un'unica "drift" generico):
rubriche scollegate dal contenuto sostanziale (art. 633 c.p.c., art. 128 codice del consumo),
variazione di lemma non colta dal matching per token esatto (art. 110 c.p., "concorso" vs
"concorrono"), diluizione oltre ogni sovra-campionamento ragionevole (art. 2087 c.c., 458° su
quasi 79.000 corrispondenze). Tutte e tre indicano l'ibrido con embedding leggero CPU (ADR-003,
Fase 4) come prossima leva, non un ulteriore intervento lessicale su BM25. `uv run pytest` → 12
verdi.

## 2026-07-01 — Ri-ancoraggio schede a 889f843 e chiusura sessione

Commit: (schede/memoria da committare)
File toccati: frontmatter di tutte le schede `.claude/context/*.md` (`last-verified-commit` →
`889f843`), `.claude/memory/index.md` (commit di riferimento, tabella, punto di ripresa),
`_notes/RESUME-PROMPT.md` (privato, riscritto sullo stato attuale). Motivo: dopo il commit
`889f843` eseguito il ri-ancoraggio (skill `sync-context`, passo post-commit). Le schede ora
coincidono con HEAD, nessun drift documentale. Registrato lo stato di chiusura: Fase A conclusa,
resta aperto il drift di ranking del retrieval come primo task della prossima sessione.

## 2026-07-01 — Benchmark del retrieval e pesatura BM25 di rubrica/titolo + README operativo

Commit: (non ancora committato)
File toccati: `scripts/benchmark_retrieval.py` (nuovo: 26 domande reali con articolo atteso,
recall@1/5/8, default vs pesato); `src/legal_consultant/index/fts.py` (`search` ora usa
`bm25` con pesi per colonna, `_BM25`); `README.md` (installazione e uso: installer un clic,
setup veloce, Project permanente, aggiornamento, limiti).
Motivo: Fase A del piano di test. Misurata la qualità del retrieval sull'indice reale: la
ricerca lessicale sul primo risultato spesso non è l'articolo cardine. Pesare rubrica (x12) e
titolo (x3) rispetto al corpo migliora nettamente e senza reindicizzare (recall@8 15/26 → 19/26,
recall@5 13 → 15): licenziamento, risoluzione, diffamazione, furto, recesso consumatore salgono.
Pesatura adottata in `fts.search`. Resta un tetto lessicale (~27% dei concetti non emerge in
top-8, es. usura, danno ambientale, doveri verso i figli) colmabile solo con ricerca ibrida
semantica (ADR-003); nel prodotto è mitigato dal modello che identifica il numero e usa
`leggi_atto`. `uv run pytest` → 10 verdi.

## 2026-07-01 — Verifica end-to-end in Claude Desktop, fix info_corpus, installer, corpus come clone

Commit: (non ancora committato)
File toccati: `src/legal_consultant/mcp_server.py` (`info_corpus` legge da `state.json`, niente
conteggi/git a runtime; prompt `consulenza_legale` rafforzato: solo legge-it, mai web, usa
`leggi_atto` per l'articolo puntuale); `scripts/bootstrap_index.py` (scrive `state.json` a fine
indicizzazione); `src/legal_consultant/update/__init__.py` (timeout su git in `_git`, except allargato
a `SubprocessError`); `scripts/setup.py` (corpus come clone locale, non più submodule); `.gitignore`
(`data/italia-corpus/` ignorato); `prompts/consulente-legale.md` (istruzioni rafforzate); nuovi
`install.ps1` e `install.cmd`.
Motivo: prima prova in Claude Desktop (Sonnet 5) — senza le istruzioni del Project il modello
ignorava legge-it e cercava sul web; con il prompt esplicito "solo legge-it, no web" ha invece
chiamato `cerca_normativa` + `leggi_atto` e citato gli artt. 157-161-bis c.p. con URN dal corpus,
niente web. Emerso un timeout: `info_corpus` faceva `COUNT` sull'indice da 2.6 GB e in Claude
Desktop (cache fredda) superava i 4 minuti; risolto leggendo le statistiche precalcolate da
`state.json` scritto dal bootstrap. Aggiunto timeout a git per sicurezza. Deciso il passaggio del
corpus da submodule a clone locale ignorato (git pull per l'aggiornamento: sempre l'ultima versione).
Costruito l'installer "un clic" (`install.cmd` → `install.ps1`): installa git/uv se mancano,
configura `core.longpaths`, esegue `setup.py`, registra legge-it in Claude Desktop, senza admin.
Verifica: dopo riavvio dell'app, risposta completa sulla prescrizione dal corpus + `info_corpus`
istantaneo (screenshot). `uv run pytest` → 10 verdi.

## 2026-06-30 — Integrazione codici fondamentali da Normattiva (civile, penale, ecc.)

Commit: (non ancora committato)
File toccati: `src/legal_consultant/ingest/parser.py` (regex articolo estesa: cattura rubrica
anche tra parentesi `### Art. N. (Rubrica)` oltre che col trattino, retro-compatibile);
`src/legal_consultant/config.py` (+ `EXTRA_CORPUS_PATH`); `scripts/fetch_codici.py` (nuovo);
`scripts/bootstrap_index.py` (indicizza anche la collezione supplementare); `tests/test_pipeline.py`
(+ caso rubrica tra parentesi); `data/codici-extra/Codici/*.md` (5 codici scaricati, ~5.2 MB).
Aggiornate le schede pertinenti e `memory/index.md`.
Motivo: chiusura della lacuna emersa dal test in Claude Desktop. I vecchi codici emanati con Regio
Decreto (civile, penale, procedura civile, navigazione, penali militari) in italia-corpus c'erano
solo come decreto di approvazione, senza articolato. PoC su `normattiva2md` (onData, MIT) validato:
il codice civile scaricato da Normattiva (pubblico dominio) ha 3282 articoli, ma con rubrica tra
parentesi che il regex non catturava (352/3282 → 3282/3282 dopo l'estensione). Scritto
`fetch_codici.py` che scarica i 5 codici da Normattiva via `uvx normattiva2md`, ne riscrive il
frontmatter nello schema del progetto e li salva in `data/codici-extra` (tracciato, fuori dal
submodule). Re-index dell'intero corpus + supplemento: 287.816 atti, 966.126 chunk, 306s. Verifica
end-to-end: art. 2043 c.c., art. 157 c.p., art. 112 c.p.c. ora presenti e ricercabili dal nostro
indice; `cerca_normativa("risarcimento del danno per fatto illecito")` → art. 2043 c.c. `uv run
pytest` → 10 verdi. Aggiornamento del supplemento: rilanciare `fetch_codici.py` + reindex.

## 2026-06-30 — Corpus reale indicizzato end-to-end + percorsi lunghi Windows + fix vigenti/dedup

Commit: (codice non ancora committato; indice e corpus sono fuori da git)
File toccati: `src/legal_consultant/config.py` (+ `long_path`); `src/legal_consultant/ingest/parser.py`
(open via `long_path`; `vigente` declassato a False per la collezione delle abrogate);
`src/legal_consultant/index/fts.py` (+ `dedup` per (urn, articolo) in `search`);
`src/legal_consultant/update/__init__.py` (`is_file` via `long_path`); `scripts/setup.py`
(`core.longpaths` automatico); schede `STACK.md`, `deployment.md`, `design-and-security.md`.
Motivo: portato il sistema su tutto il corpus reale, end-to-end, su Windows. Limite MAX_PATH (260
char) aggirato in modo trasparente, senza admin: git estrae con `core.longpaths`, Python apre con
prefisso `\\?\` via `config.long_path` (verificato leggendo un atto con path da 276 char). Riusati i
330 MB gia' scaricati: `git -C data/italia-corpus reset --hard` ha completato l'estrazione (287.813
file). `bootstrap_index.py` sull'intero corpus: 287.811 atti, 759.881 chunk, 23 errori (caratteri di
controllo, loggati), 744s, indice 2.4 GB. Due problemi di qualita' emersi dal test reale e corretti:
nel corpus il campo `vigente` e' True anche per le abrogate, quindi si declassa l'intera collezione
"Atti normativi abrogati (in originale)" (123.828 atti esclusi dai vigenti, restano 163.957);
deduplica per atto+articolo perche' il corpus archivia alcuni atti in piu' collezioni. `uv run
pytest` → 9 verdi; smoke dei tool MCP sull'indice reale corretto (es. "licenziamento per giusta
causa" → D.Lgs. 23/2015 art. 3). Limite noto: "vigente" qui significa "non nella collezione delle
abrogate", non "in vigore oggi" su Normattiva; ranking BM25 su query concettuali variabile (ADR-003).

## 2026-06-30 — Hardening, Fase 3, packaging trasparente e disclaimer (su fixture)

Commit: bd19b1d
File toccati: `src/legal_consultant/index/fts.py` (+ `to_match_query`, `search` con `sanitize`);
`src/legal_consultant/update/__init__.py` (nuovo: `corpus_revision`, `pull`, `changed_files`,
`reindex_paths`, `read_state`/`write_state`); `src/legal_consultant/mcp_server.py` (`info_corpus`
con freschezza + disclaimer; prompt MCP `consulenza_legale`); `scripts/update_corpus.py` (nuovo);
`scripts/setup.py` (nuovo); `.mcp.json` (nuovo, registrazione Claude Code); `prompts/consulente-legale.md`
(nuovo); `tests/test_pipeline.py` (+4 test). Aggiornate le schede `STACK.md`, `current-work.md`,
`deployment.md`, `design-and-security.md`, `dev-testing.md`, `roadmap.md` e `memory/index.md`.
Motivo: completato lo sviluppo del prodotto su decisione dell'utente (target Claude Code +
Desktop; scope: hardening, packaging, Fase 3, disclaimer). Hardening: la ricerca sanifica l'input
libero in una query MATCH sempre valida. Fase 3: aggiornamento incrementale del corpus via git
diff + reindex per path, con stato persistito letto da `info_corpus`. Packaging: registrazione
versionata in `.mcp.json`, setup a un comando, istruzioni e disclaimer esposti anche come prompt
MCP. `uv run pytest` → 9 test verdi; smoke di tool e prompt su fixture ok; avvio stdio pulito.
Corpus ancora non clonato: verifica end-to-end e casi d'uso rinviati al bootstrap reale.

## 2026-06-30 — Fase 2: server MCP "legge-it" (su fixture)

Commit: f954aaa
File toccati: `src/legal_consultant/mcp_server.py` (nuovo); `src/legal_consultant/index/fts.py`
(+ `get_act`, + `corpus_stats`; `search` ora include `vigente` nel SELECT); `pyproject.toml`
(+ dipendenza `mcp>=1.2`); `uv.lock`; `tests/test_pipeline.py` (+ test `get_act` e `corpus_stats`).
Aggiornate e ri-ancorate a `6111cd3` le schede `STACK.md`, `current-work.md`, `deployment.md`,
`design-and-security.md`, `dev-testing.md`, `roadmap.md`; aggiornati `memory/index.md` e questo
work-log.
Motivo: implementata la Fase 2. Server `FastMCP("legge-it")` su transport stdio con tre tool —
`cerca_normativa` (sopra `fts.search`), `leggi_atto` (sopra `fts.get_act`), `info_corpus` (sopra
`fts.corpus_stats`) — con descrizioni orientate alla citazione e degrado con grazia se l'indice
manca. Logica dati in `index.fts`, server sottile con helper puri di formattazione. `uv sync
--extra dev` ok; `uv run pytest` → 5 test verdi; smoke dei tre tool su indice di fixture corretto;
avvio `python -m legal_consultant.mcp_server` su stdio pulito. Corpus ancora non clonato e server
non ancora registrato in Claude Desktop.

## 2026-06-25 — Fase 1: pipeline ingest + indice FTS5 (su fixture)

Commit: 6111cd3
File toccati: `pyproject.toml`; `src/legal_consultant/` (`__init__`, `config.py`, `ingest/parser.py`,
`index/fts.py` + `__init__`); `scripts/bootstrap_index.py`; `tests/test_pipeline.py` e
`tests/fixtures/Codici/` (2 atti reali). Aggiornate le schede `STACK.md` e `current-work.md`.
Motivo: implementato il nucleo della Fase 1. Ispezionato lo schema reale del frontmatter YAML via
API GitHub (`tipo/numero/data/titolo/urn/codice_redazionale/vigente`) e la struttura del corpo
(articoli `## Art. N.` con rubrica, commi, preambolo). Scritto il parser (chunking per articolo) e
l'indice SQLite FTS5 (BM25, tokenizer `unicode61 remove_diacritics 2`, filtro vigenti). `uv sync`
ok; `uv run pytest` → 3 test verdi (parser + ricerca BM25 su atti reali). Corpus NON ancora
clonato (clone shallow del submodule rimandato per dimensione: ~831 MB lato git + storia
giornaliera). Esito: pipeline validata su fixture, pronta per il bootstrap sul corpus reale.

## 2026-06-25 — Primo ancoraggio delle schede al commit iniziale

Commit: 1e4c79b
File toccati: tutte le schede di `context/` (STACK, design-and-security, deployment, dev-testing,
current-work, roadmap) e `memory/index.md`.
Motivo: eseguita la skill `sync-context` (Passo 0) dopo il primo commit. Sostituito il segnaposto
`PENDING-FIRST-COMMIT` con l'hash di HEAD (`1e4c79b`) in `generated-from-commit` e
`last-verified-commit` di ogni scheda, e nel commit di riferimento dello snapshot. Da qui il
drift futuro si misura normalmente rispetto a HEAD.

## 2026-06-25 — Inizializzazione del sistema di progetto

Commit: 1e4c79b
File toccati: anatomia di `.claude` (PROJECT-SYSTEM.md, rules/, skills/, templates/ importati dal
bundle; settings.json, memory/, context/ istanziati), `CLAUDE.md`, `CLAUDE.local.md`,
`.gitignore` (merge dello snippet). git inizializzato (branch `main`), identità locale
github-personal (alesop95), remoto `git@github-personal:alesop95/legal-consultant.git` (verificato
vuoto via ls-remote). Schede strutturali create con solo frontmatter; `roadmap.md`,
`current-work.md` e `decisions.md` seminate con le decisioni confermate.
Motivo: installazione del sistema portabile di contesto, documentazione e version control
descritto in `.claude/PROJECT-SYSTEM.md`. Auto-memory nativa lasciata disattivata
(`autoMemoryEnabled: false`). MCP di sviluppo (code-context) rimandato.

## 2026-06-25 — Handoff iniziale e scelte di architettura (pre-sistema)

Commit: 1e4c79b
File toccati: `HANDOFF.md`, `README.md`, `.env.example`.
Motivo: ricerca su italia-corpus e strumenti, e definizione dell'architettura confermata con
l'utente (vedi ADR-002/003/004): server MCP locale + Claude Desktop, retrieval BM25 senza GPU,
corpus solo italiano via submodule self-updating.
