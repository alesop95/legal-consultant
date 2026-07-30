# Completamento del corpus: scelta, architettura, comandi

> Documento di progetto, tracciato. Racconta come si è deciso di colmare le lacune misurate
> in `docs/audit-completezza-corpus.md`, perché fra le strade possibili si è scelta questa,
> come è fatta la macchina che la realizza e come si verifica che il corpus sia completo.
> Redatto il 2026-07-30, contestualmente all'implementazione.

## 1. Le strade possibili, e perché la scelta non è quella che sembrava

L'incarico ne prevedeva due: contribuire la correzione a monte nel repository dello script
che genera il corpus, oppure aggiungere qui un ingestore autonomo che copra le classi
mancanti. L'audit ne ha rivelata una terza, che nessuna delle due contemplava, e che cambia
il quadro: Normattiva pubblica da dicembre 2024 un'API[^1] Open Data documentata, con
specifica OpenAPI, che espone sia la ricerca avanzata per tipologia sia un export massivo
in Akoma Ntoso[^2], e risponde senza credenziali.

La correzione a monte è stata scartata come percorso critico, non come idea. La ragione
tecnica è che il difetto non è un errore dello script: lo script è un mirror fedele del
catalogo delle collezioni preconfezionate di Normattiva, e quel catalogo non contiene la
legge ordinaria. Correggerlo a monte non significa sistemare un baco ma riscrivere il modo
in cui il corpus viene generato, passando dalle collezioni preconfezionate alla ricerca per
tipologia. La ragione pratica è che quel repository non ha mai processato una pull request
in tutta la sua storia, non tocca codice da cinque settimane, il job di sincronizzazione è
fermo da undici giorni e due segnalazioni di terzi sono senza risposta da settimane. Mettere
la completezza del prodotto in dipendenza da quei tempi sarebbe stato imprudente.

La seconda strada, l'ingestore autonomo a valle, è quella adottata, ma non nella forma
ipotizzata dall'incarico. L'ipotesi era di raschiare l'export per singolo atto del sito, con
la sessione a cookie condivisi che la tesi aveva già risolto: due richieste HTTP per atto,
che sulle circa undicimila lacune misurate avrebbero significato ventiduemila richieste alla
fonte. L'export massivo dell'API fa la stessa cosa in poche decine di richieste, restituisce
lo stesso XML strutturato, ed è la via che la fonte stessa documenta per lo scarico
massivo. Non usarla, avendola trovata, sarebbe stato sbagliato sia per efficienza sia per
rispetto della fonte.

Resta sensata, come atto di igiene verso un dataset pubblico che molti usano, una
segnalazione a monte che documenti la lacuna: non è stata aperta, perché pubblicare una issue
su un repository di terzi è un'azione verso l'esterno che spetta a chi possiede il progetto,
e il testo è pronto in `_notes/` per quando si decida di farlo.

## 2. Cosa fa il codice

Il perno è che gli atti recuperati entrano nell'indice dalla stessa porta di tutti gli
altri. Non esiste un secondo percorso di ingestione: l'export XML della fonte viene
convertito nello stesso Markdown con frontmatter YAML che il corpus principale già usa, e da
lì lo leggono il parser, l'indicizzatore e la ricerca senza sapere da dove venga. Questo è
anche il motivo per cui il modulo di conversione emette le intestazioni di articolo nella
forma `### Art. N. (Rubrica)`, che è quella già presente in `data/codici-extra`: introdurre
una terza convenzione avrebbe significato toccare il parser condiviso per un caso
particolare.

```
src/legal_consultant/fonte/
├── normattiva.py    client dell'API Open Data: tipologiche, ricerca avanzata, export asincrono
├── akn.py           conversione Akoma Ntoso -> Markdown con frontmatter del corpus
└── recupero.py      scrittura nella collezione locale, lotti, liste bianche
```

Il client dell'API usa soltanto `urllib` della libreria standard, coerentemente con un
progetto che non ha dipendenze di rete, e non invia alcuna email: il flusso asincrono la
prevede come parametro opzionale, e non usarla significa che nessun dato personale lascia la
macchina.

La collocazione dei file è imposta da un vincolo preciso. Il corpus principale in
`data/italia-corpus` è un clone di un repository terzo che viene riallineato con `fetch` più
`reset --hard` a ogni aggiornamento, quindi qualunque file scritto lì verrebbe distrutto
senza preavviso. Il materiale recuperato vive perciò in una radice separata,
`data/normattiva-suppl`, sul modello di `data/codici-extra`, e l'indicizzatore itera su
tutte le radici invece di conoscerne i nomi uno per uno. A differenza di `codici-extra`, che
è piccola e tracciata, questa collezione è voluminosa e resta fuori da git: si ricostruisce
dalla fonte, non si spedisce nel repository.

### Tre decisioni di conversione che non sono ovvie

Le note sono escluse dal testo indicizzato. Normattiva annida dentro il corpo dell'articolo,
in elementi di nota, il testo integrale delle norme richiamate: l'art. 1 della L. 219/2017 si
porterebbe dietro gli artt. 2, 13 e 32 della Costituzione. In un indice a granularità di
articolo quel testo è rumore che sposta il ranking verso l'articolo sbagliato, e comparirebbe
anche due volte per via dell'annidamento. Il rinvio resta leggibile nel testo dell'articolo;
il testo della norma richiamata si trova cercando quella norma.

I numeri di comma sono preservati come prefisso di riga. Senza, il testo di un articolo
diventa una sequenza di capoversi anonimi e la citazione puntuale di un comma non è più
possibile, che in un prodotto il cui valore è la citazione verificabile è una perdita grossa
per un guadagno nullo.

La rubrica viene talvolta ricostruita, sotto condizioni strette. Normattiva emette a volte
un elemento di rubrica vuoto e colloca la rubrica come primo capoverso non numerato
dell'articolo. Ignorarlo significherebbe indicizzare l'articolo senza rubrica, e la rubrica
è la colonna che pesa dodici volte il corpo nel ranking, quindi la perdita si pagherebbe in
recall su tutte le domande formulate col nomen iuris. La promozione avviene solo se la
rubrica esplicita è assente, il capoverso non è numerato, è più corto di 250 caratteri, non
termina con un punto, ed è seguito da altro contenuto nello stesso articolo. Le ultime due
condizioni sono state aggiunte dopo un caso reale che le ha rese necessarie: negli articoli
della Costituzione il testo dell'articolo È l'unico capoverso non numerato, e senza quelle
condizioni l'art. 139 finiva indicizzato con la sua unica frase promossa a rubrica e il corpo
vuoto. Le condizioni sono state verificate su un anno intero di leggi: dei 295 articoli con
rubrica esplicita nessuno ha un capoverso iniziale anonimo, e dei 42 candidati validi tutti
hanno altro contenuto dopo di sé e nessuno termina con un punto, mentre nella Costituzione
vale l'opposto in entrambi i casi.

### Gli allegati, e la sola modifica al parser condiviso

Normattiva colloca negli allegati contenuti che sono parte integrante dell'atto: le diciotto
disposizioni transitorie e finali della Costituzione stanno tutte lì, fuori dal corpo.
Ignorarle avrebbe ricreato a valle esattamente il difetto del corpus a monte, che perde il
contenuto quando questo sta in un allegato. Farle invece finire in coda all'ultimo articolo
avrebbe prodotto una citazione falsa, perché sarebbero state attribuite all'art. 139.

Il parser condiviso è stato quindi esteso di una sola regola: una intestazione `## Allegato
I` apre un chunk proprio, come fa una intestazione di articolo, e l'unità citabile che ne
risulta si chiama `Allegato I`, che è come la fonte stessa la nomina. Il numero è
obbligatorio, così una intestazione di sola rassegna come `## Allegati`, che compare nei
codici, continua a restare testo e non crea chunk spuri. Con questa regola la Costituzione
entra nell'indice come 139 articoli più 18 allegati, cioè 157 unità citabili.

### La lista bianca, che è un requisito di correttezza

L'export di un periodo restituisce tutti gli atti di quella tipologia in quel periodo,
comprese le norme abrogate, mentre il frontmatter scritto da questo codice dichiara `vigente:
true`. Senza filtro, una legge abrogata entrerebbe nell'indice come vigente, che è un errore
peggiore della sua assenza. Si scrive quindi solo ciò che compare nella lista bianca degli
atti enumerati presso la fonte nelle sole classi non abrogate. La coincidenza fra le URN[^3]
dell'enumerazione e quelle degli XML è stata verificata, non assunta.

## 3. Perché pochi export grandi invece di molti piccoli

La prima versione chiedeva un export per anno. Misurata, si è rivelata lenta per una ragione
che non si sarebbe indovinata: il costo di un export è dominato dall'attesa di elaborazione
presso la fonte, non dal numero di atti, e davanti al gateway c'è un WAF[^4] che risponde 409
alla rotta di interrogazione dello stato quando le richieste sono ravvicinate. Interrogare
ogni due secondi produce 409 per oltre due minuti di fila senza mai vedere l'export, che era
invece già pronto. Interrogare meno spesso è quindi più veloce, non più lento, ed è anche il
comportamento corretto verso la fonte.

Ne seguono due scelte. Il polling parte da venticinque secondi e cresce fino a novanta, e il
409 è trattato come un "non ancora pronto" e non come un errore. E le lacune vengono
raggruppate in lotti contigui per data di emanazione, usando i filtri di intervallo dell'API:
un lotto che copre più anni costa la stessa attesa di un lotto per un anno solo, quindi
conviene chiedere lotti grandi. I lotti sono ordinati dal più recente al più antico, così che
se il tempo finisce ciò che è già stato recuperato sia la parte di normativa che si consulta
di più.

La dimensione del lotto è però tarata su misura e non su intuito, perché "grande" ha un
limite. Un lotto da quattrocento atti si completa in pochi minuti; uno da milleduecento non
è arrivato a compimento in mezz'ora di attesa. La fonte non prepara archivi grandi in tempi
utili, e insistere significherebbe occupare il proprio turno senza risultato: il tetto è
quindi quattrocento.

### Il limite di traffico della fonte, e perché determina il ritmo di convergenza

C'è un secondo comportamento della fonte, scoperto sul campo e non documentato nella
specifica, che vale più di qualunque ottimizzazione: il filtro di protezione impone un limite
durevole per client sulla sola rotta di interrogazione dello stato. Dopo un'attività di export
sostenuta, quella rotta risponde 409 in modo persistente, per decine di minuti, mentre la
ricerca avanzata, la richiesta di un nuovo export e la sua conferma continuano a rispondere
regolarmente. Non è quindi un sovraccarico del servizio né un errore del client: è un tetto al
volume di export che una singola postazione può ottenere in una finestra di tempo.

La conseguenza pratica è che un recupero massivo non si può fare in una sessione, per quanto
bene sia scritto il codice: va necessariamente distribuito su più giorni. Il codice lo
riconosce invece di subirlo. Dopo otto rifiuti consecutivi conclude che il limite è durevole,
interrompe il giro con un messaggio che dice esplicitamente che non è un errore del progetto e
non richiede alcun intervento, e lascia che sia l'esecuzione successiva a riprendere dalle
lacune residue. Insistere sui lotti seguenti otterrebbe lo stesso rifiuto consumando il budget
senza recuperare nulla.

## 4. Convergenza a budget, invece di un installer che sembra bloccato

Il recupero storico completo, dal 1861 a oggi, richiede ore. Metterlo dentro un installer
pensato per durare quindici minuti su una postazione di studio legale lo avrebbe fatto
sembrare bloccato per mezza giornata. Il comando accetta quindi un budget di tempo con
`--minuti`: scarica quanto sta nel tempo concesso, e poiché riparte sempre dalle lacune
residue, molti passaggi brevi convergono come uno lungo.

L'installer ne esegue una parte dagli anni recenti, e l'attività pianificata giornaliera
completa il resto nei giorni successivi con un budget di trenta minuti per giro, tenuto basso
di proposito perché la macchina di uno studio può essere accesa e in uso. Quando le lacune
sono chiuse quella chiamata costa solo l'enumerazione. Finché non lo sono, il controllo di
completezza scrive nel registro dell'aggiornamento che il corpus ha lacune, invece di
lasciarle invisibili.

## 5. Il controllo di completezza

È il pezzo che rende il lavoro definitivo invece che episodico, perché il difetto vero non
era l'incompletezza ma il fatto che fosse silenziosa. Il comando è
`scripts/check_completezza.py`, esce con codice 1 quando trova lacune, e non stampa un totale
rassicurante: stampa quale classe manca e quale atto atteso non si trova.

Fa due controlli indipendenti, perché uno solo non basterebbe. Dall'alto chiede alla fonte
quali tipologie di atto esistono e quanti atti ha ciascuna, e le confronta con l'indice.
L'elenco delle tipologie viene ricavato dall'API a ogni esecuzione e non è scritto nel
codice: cablarlo ripeterebbe esattamente l'errore che ha prodotto la lacuna, cioè fidarsi di
un elenco di ciò che c'è per stabilire ciò che dovrebbe esserci. Dal basso verifica una lista
di atti notori, scelti perché uno studio legale li consulta davvero, uno per uno. Se i due
controlli divergono ha ragione il secondo, perché una collezione può esistere ed essere
popolata solo in parte.

Il controllo dal basso verifica anche una cosa che un semplice conteggio non vedrebbe: che
l'atto presente abbia davvero l'articolato. Il codice penale nel corpus a monte è un guscio
di quattro chunk con la sola formula di approvazione, quindi per gli atti che sono corpi
normativi articolati il controllo richiede una soglia minima di chunk e segnala
`SENZA TESTO` quando non è raggiunta. Un atto presente ma vuoto non è un atto presente.

## 6. Comandi

```
uv run python scripts/check_completezza.py            verifica e dice cosa manca (esce 1 se manca)
uv run python scripts/check_completezza.py --offline   solo le sentinelle, senza rete
uv run python scripts/fetch_normattiva.py              colma tutte le classi mancanti
uv run python scripts/fetch_normattiva.py --dry-run    misura le lacune senza scaricare
uv run python scripts/fetch_normattiva.py --minuti 30  colma quanto sta in mezz'ora
uv run python scripts/fetch_atto.py <urn>              recupera e indicizza un singolo atto
```

Il recupero di un singolo atto per URN, che prima non esisteva perché `fetch_codici.py` è
cablato sui cinque codici fondamentali, usa lo stesso export asincroni del recupero massivo
con il filtro ristretto a numero e anno. Costa qualche secondo in più di una richiesta
diretta, e in cambio esiste un solo percorso di codice invece di due da tenere allineati.

## 7. Effetto sul recall

Il vincolo posto dall'incarico era di misurare il recall prima e dopo, perché su una ricerca
puramente lessicale un corpus più grande può peggiorare la precisione. La misura è quella di
`scripts/benchmark_retrieval.py`, ventisei domande con l'articolo atteso.

```
prima  (287.805 file indicizzati)   recall@1 14/26   recall@5 19/26   recall@8 19/26
dopo   (vedi nota)                  recall@1 14/26   recall@5 19/26   recall@8 19/26
```

Il benchmark è costruito su codici e testi unici, cioè su atti che erano già nel corpus, e
non contiene domande sulle classi recuperate: misura quindi la non-regressione, che è
esattamente ciò che il vincolo chiedeva di sorvegliare, e non il guadagno. Il guadagno si
vede invece sulle domande che prima non avevano risposta possibile: la L. 194/1978, che non
esisteva nel corpus, oggi è indicizzata con i suoi 22 articoli ed è restituita dalla ricerca
sui termini della sua materia.

Va detto con precisione anche il limite di questa misura. Aggiungere migliaia di leggi
introduce nuovi concorrenti nel ranking, e il benchmark attuale non li esercita perché le sue
domande puntano tutte su codici. Un benchmark che copra anche le classi recuperate è la
verifica che manca, ed è registrata come tale nella roadmap invece di essere data per fatta.

## 8. Stato e cosa resta

La macchina è completa e verificata: conversione, scrittura, indicizzazione incrementale,
recupero massivo a lotti, recupero per URN, controllo di completezza, integrazione
nell'installer e nell'attività pianificata. La validazione più significativa non è stata
provocata: l'attività pianificata di Windows già registrata su questa macchina ha eseguito da
sola, la notte del 30 luglio, le fasi nuove nell'ordine previsto, e ha scritto nel proprio
registro che il corpus ha ancora lacune indicando il comando per il dettaglio. Il percorso non
presidiato funziona.

Il popolamento è invece per costruzione progressivo, e il ritmo non lo decide il progetto ma la
fonte, per il limite di traffico descritto sopra. Le lacune misurate erano 9.313 leggi, 1.584
decreti-legge e la Costituzione; alla fine della sessione di sviluppo sono recuperati la
Costituzione con i suoi 139 articoli e 18 allegati, la L. 194/1978 e la L. 219/2017 (le due
leggi da cui l'intera vicenda è nata), e circa novecento atti fra leggi e decreti-legge,
partendo dai più recenti. Il resto si chiude nell'arco di alcuni giorni di esecuzioni
giornaliere a budget, e ogni giro lascia traccia in `data/index/auto_update.log`.

Il numero esatto di ciò che manca in ogni momento lo dice `scripts/check_completezza.py`, e
questo è il vero punto del lavoro: la lacuna residua non va ricordata a memoria, non è
implicita, e non può tornare silenziosa. Un atto atteso che non si trova ha un nome nel
rapporto del controllo, e il controllo esce in errore.

Un'ultima nota di onestà sull'ordine dei fatti. La macchina è stata verificata su ogni suo
passo con dati reali, ma la verifica che conta per uno studio legale, cioè fare una domanda in
Claude Desktop su una legge ordinaria e vedersela citare correttamente, è stata fatta finora
solo sulla L. 194/1978 attraverso il tool di ricerca, non in una sessione di chat completa. È
il primo passo da rifare quando il popolamento sarà arrivato a coprire le materie di interesse.

[^1]: *API*, Application Programming Interface - interfaccia con cui un sistema espone i
propri dati a un altro programma in modo strutturato.

[^2]: *Akoma Ntoso* - standard OASIS di rappresentazione XML dei documenti giuridici, che
marca esplicitamente articoli, rubriche e commi.

[^3]: *URN*, Uniform Resource Name - identificatore stabile di un atto normativo; nello
standard NIR italiano ha la forma `urn:nir:stato:legge:1978-05-22;194`.

[^4]: *WAF*, Web Application Firewall - filtro che ispeziona il traffico verso un servizio
web e può bloccarlo prima che raggiunga l'applicazione.
