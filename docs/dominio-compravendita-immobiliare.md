# Copertura del dominio: compravendita immobiliare residenziale

> Verifica del 28 agosto 2026. Mappa le norme che governano l'acquisto di un immobile residenziale sul contenuto effettivo del corpus, dichiara le lacune trovate e quelle colmate, e riporta il modo di interrogare il server su questa materia. E' il primo audit per dominio del progetto, e nasce da un uso reale: la valutazione di un acquisto immobiliare condotta con lo strumento in `E:\real-estate`.

## Perche' un audit per dominio

I due controlli di completezza esistenti guardano il corpus dall'alto, confrontando le tipologie di atto con quelle dichiarate dalla fonte, e dal basso, con una lista di atti notori. Entrambi sono trasversali per costruzione, e questo e' il loro pregio ma anche il loro limite: una materia puo' risultare coperta perche' i suoi atti principali ci sono, e restare inservibile perche' manca la singola norma che decide la questione.

La compravendita immobiliare e' l'esempio che ha reso evidente il problema. E' la materia su cui un privato consulta per primo uno strumento come questo, e attraversa quattro rami che nel corpus vivono in classi diverse, cioe' l'imposizione fiscale, la disciplina edilizia, la pubblicita' immobiliare e il contratto. Prima di questa verifica il corpus conteneva il testo unico dell'edilizia, il testo unico dell'imposta di registro, il codice civile e la disciplina delle locazioni, e sarebbe sembrato coprire la materia. Mancava pero' la legge 52 del 1985, il cui articolo 29 comma 1-bis e' la norma che rende nullo l'atto di trasferimento privo della dichiarazione di conformita' catastale: la disposizione singola piu' consultata dell'intera materia.

## Che cosa e' stato verificato e con quale esito

La verifica ha misurato la presenza di ogni atto rilevante e, per quelli articolati, la quantita' di testo effettivamente indicizzata. La colonna dei caratteri e' quella che conta, per la ragione spiegata nella sezione successiva.

| Atto | Cosa disciplina nel dominio | Caratteri | Esito |
|---|---|---|---|
| DPR 131/1986 | Imposta di registro, nota II-bis sull'agevolazione prima casa | 336.828 | presente |
| Legge 266/2005 | Regola prezzo-valore, art. 1 comma 497 | 587.288 | presente |
| DPR 601/1973 | Imposta sostitutiva sui finanziamenti a medio e lungo termine | 108.002 | presente |
| DPR 917/1986, TUIR | Detrazione degli interessi passivi, plusvalenza da cessione | 2.394.276 | presente |
| DPR 380/2001 | Testo unico edilizia, tolleranze costruttive, menzioni urbanistiche | 745.087 | presente |
| D.lgs. 122/2005 | Fideiussione e polizza decennale nell'acquisto da costruttore | 114.231 | presente |
| D.lgs. 23/2011 | Cedolare secca sulle locazioni | 310.489 | presente |
| DL 50/2017 | Locazioni brevi e obblighi degli intermediari | 424.044 | presente |
| DL 69/2024 | Salva Casa, stato legittimo e tolleranze | 39.755 | presente |
| Legge 431/1998 | Locazioni abitative, canone libero e concordato | 50.942 | presente |
| Legge 160/2019 | Disciplina dell'IMU | 1.038.802 | presente |
| D.lgs. 504/1992 | Base imponibile ancora richiamata dall'IMU | 357.687 | presente |
| D.lgs. 192/2005 | Prestazione energetica degli edifici, APE | 237.593 | presente |
| Codice civile | Caparra, preliminare, trascrizione, mediazione, condominio | 1.635.660 | presente |
| Legge 47/1985 | Menzioni urbanistiche in atto, art. 40 | 75.612 | **lacuna colmata** |
| Legge 52/1985 | Conformita' catastale a pena di nullita', art. 29 comma 1-bis | 23.759 | **lacuna colmata** |
| Legge 448/1998 | Credito d'imposta per riacquisto della prima casa, art. 7 | assente | **lacuna aperta** |

Le due lacune colmate sono state recuperate con `scripts/fetch_atto.py` dalla fonte ufficiale e sono ora indicizzate. La lacuna aperta e' tale perche' la fonte non restituisce l'atto all'URN `urn:nir:stato:legge:1998-12-23;448`, ne' con il recupero forzato: fino a quando non si trova la via di accesso corretta, sulle domande relative al credito d'imposta per riacquisto il consulente deve dichiarare che la norma non e' nel corpus, invece di rispondere sulla base di quanto trova di simile.

## Un difetto del controllo di completezza, trovato e corretto

Il criterio con cui il controllo distingueva un atto presente da un guscio senza articolato era il numero di chunk indicizzati, con una soglia di dieci. Su questa materia il criterio si e' rivelato sbagliato in modo sistematico.

Le leggi finanziarie sono formalmente composte da un solo articolo con centinaia di commi, e finiscono nell'indice come due o tre chunk pur contenendo tutto. La legge 266 del 2005, che porta la regola del prezzo-valore, sta in due chunk e in quasi seicentomila caratteri. Con il criterio a chunk sarebbe stata dichiarata priva di articolato, cioe' esattamente il falso allarme peggiore per un controllo la cui ragione d'essere e' non dare falsa sicurezza: un controllo che grida al lupo su un atto integro perde credibilita' anche quando segnala una lacuna vera.

Il criterio e' stato quindi cambiato in una soglia sui caratteri, ventimila, che misura cio' che conta davvero. Il numero di chunk resta a video come informazione, ma non decide piu' l'esito. La stessa colonna dei caratteri rende ora leggibile a colpo d'occhio la differenza fra un atto sostanzioso e un guscio, che prima richiedeva un'interrogazione manuale dell'indice.

## Che cosa il corpus copre bene, e che cosa per natura non copre

La verifica ha confermato che il testo unico dell'edilizia nel corpus e' il consolidato vigente e non una versione storica: l'articolo 34-bis contiene il comma 1-bis introdotto dal Salva Casa, con il riferimento agli interventi realizzati entro il 24 maggio 2024. E' un punto che vale la pena sapere, perche' significa che sulle tolleranze costruttive il consulente risponde con il testo aggiornato senza bisogno di ricostruire la catena delle modifiche.

Restano invece fuori dal corpus, e vanno dichiarati all'utente quando la domanda li tocca, tre insiemi di fonti. I decreti ministeriali, fra cui il decreto 37 del 2008 sulla conformita' degli impianti, che nella prassi della compravendita e' documento richiesto ad ogni rogito. Gli accordi territoriali sul canone concordato, che sono atti locali stipulati fra le associazioni di categoria di ciascun Comune e determinano il canone applicabile: non sono legislazione statale e nessun corpus nazionale li conterra' mai. Le delibere comunali sulle aliquote IMU, per la stessa ragione. Su tutte e tre la risposta corretta e' indicare dove si trovano, non cercare nel corpus un surrogato.

Va infine ricordato il limite gia' noto e documentato in `docs/giurisprudenza-fattibilita.md`: il corpus e' legislazione, non giurisprudenza. Su una materia come la conformita' catastale, dove la distinzione fra irregolarita' che producono nullita' e difetti minori e' opera della Cassazione e non del testo di legge, il consulente puo' citare la norma ma non l'interpretazione consolidata, e deve dirlo.

## Come interrogare il corpus su questa materia

La ricerca per parole chiave da sola non e' affidabile su questo dominio, per una ragione strutturale: le norme fiscali immobiliari vivono dentro leggi finanziarie enormi, dove il comma rilevante e' una riga fra migliaia, e il ranking testuale la seppellisce. La strada efficace e' quella gia' prevista dalle istruzioni del consulente, cioe' usare `leggi_atto` con l'URN dell'atto e il numero dell'articolo quando si sa gia' dove guardare, e riservare `cerca_normativa` all'esplorazione.

I riferimenti da cui partire sono i seguenti. Per l'agevolazione prima casa, la nota II-bis all'articolo 1 della tariffa parte prima del DPR 131/1986. Per il prezzo-valore, l'articolo 1 comma 497 della legge 266/2005. Per l'imposta sostitutiva sul mutuo, gli articoli da 15 a 20 del DPR 601/1973. Per la detrazione degli interessi passivi, l'articolo 15 comma 1 lettera b del TUIR, e per la plusvalenza l'articolo 67 comma 1 lettera b dello stesso. Per la conformita' catastale, l'articolo 29 comma 1-bis della legge 52/1985. Per le menzioni urbanistiche, l'articolo 46 del DPR 380/2001 e l'articolo 40 della legge 47/1985. Per le tolleranze, l'articolo 34-bis del DPR 380/2001. Per l'acquisto dal costruttore, gli articoli 2 e 4 del d.lgs. 122/2005. Per la caparra confirmatoria, l'articolo 1385 del codice civile, per la trascrizione del preliminare l'articolo 2645-bis, per la provvigione del mediatore l'articolo 1755, per la solidarieta' sulle spese condominiali l'articolo 63 delle disposizioni di attuazione.

Una cautela sulle leggi di bilancio. Sono indicizzate, ma il loro articolo unico e' un blocco di centinaia di migliaia di caratteri: chiedere l'articolo 1 della legge 199 del 2025 restituisce quasi un milione di caratteri, il che non e' utile a nessuno. Su queste la strada e' la ricerca testuale dentro l'atto per il concetto specifico, non la lettura dell'articolo.

## Manutenzione

L'audit va rifatto quando cambia la legge di bilancio, perche' e' li' che le aliquote immobiliari si spostano, e quando `scripts/check_completezza.py` segnala una regressione sulle sentinelle del dominio. Le sentinelle immobiliari sono ora parte della lista in quello script e falliscono da sole se un atto sparisce dall'indice, il che rende questo documento una spiegazione del perche', non il meccanismo di controllo.
