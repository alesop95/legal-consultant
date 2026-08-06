# Giurisprudenza: analisi di fattibilità

> Documento di progetto, tracciato. Valuta se e come aggiungere la giurisprudenza al corpus, che oggi contiene esclusivamente testo legislativo. È un'analisi, non un piano di lavoro: la conclusione è deliberatamente restrittiva e va letta prima di scrivere qualunque riga di codice sul tema. Redatta il 2026-07-29 su richiesta di valutare l'estensione. Le condizioni d'uso riportate sono citate alla lettera dalle pagine dei titolari; ciò che non è stato verificato è dichiarato tale.

## 1. La domanda e la risposta in breve

La domanda è se convenga aggiungere la giurisprudenza al motore di ricerca locale. La risposta è che conviene su un solo sottoinsieme, la Corte costituzionale, attraverso i suoi open data, in una tabella distinta interrogata da un tool separato; e che non conviene, o non è lecito, su tutto il resto. La parte che un avvocato vorrebbe di più, l'orientamento della Corte di cassazione, è precisamente quella che non si può avere legittimamente, e questo va detto nel prodotto invece di essere lasciato intendere.

## 2. Fonti: cosa è accessibile e a quali condizioni

### Corte costituzionale

Il sito istituzionale non è una via praticabile: l'host è protetto da un *bot manager*[^1] che risponde con un rinvio a un servizio di validazione a ogni richiesta, compresa la home page, e il footer riserva tutti i diritti. Esiste però un canale ufficiale distinto e pensato per il riuso, `https://dati.cortecostituzionale.it/`, che dichiara in modo esplicito sia in home sia nella pagina di download la licenza applicata.

```
I dati disponibili in vari formati sono rilasciati con licenza
Creative Commons (CC BY SA 3.0) per il libero riuso.
```

Il contenuto è distinto esattamente come servirebbe, ed è stato verificato scaricando gli archivi. Le pronunce arrivano in XML, CSV e JSON, in archivi annuali, con il testo integrale già strutturato in una testata che porta anno, numero, ECLI[^2], tipologia fra sentenza e ordinanza, presidente, relatore, redattore, data di decisione e data di deposito, e in un corpo diviso in fatto, diritto e dispositivo. Le massime stanno in un archivio separato e portano, per ciascuna, numero, titolo, testo e un blocco di riferimenti normativi strutturati con codice, numero, data, articolo, specificazione e comma. Le dimensioni sono modeste: circa 85 MB in tutto, circa 18.000 pronunce dal 1956 e 46.486 massime, contro un indice locale che oggi conta 966.316 chunk. Sul campione dal 2001 il blocco dei riferimenti normativi è presente sull'85 per cento delle massime, e una citazione di precedenti in forma testuale compare sul 27 per cento. Esiste anche un endpoint SPARQL[^3], non collaudato.

Una clausola va decisa prima e non dopo. La licenza CC BY-SA 3.0 porta un obbligo di condivisione allo stesso modo. Per l'uso locale non c'è distribuzione e l'obbligo non si attiva, ma la voce di roadmap che prevede la distribuzione di un indice pre-costruito distribuirebbe un'opera derivata da un dataset con quella clausola, con conseguenti obblighi di attribuzione e di licenza compatibile sulla base di dati derivata.

### Corte di cassazione

Qui la risposta non è un rischio da ponderare, è un divieto scritto che nomina esattamente le due operazioni che questo progetto compie per definizione.

Il canale pubblico esiste ed è tecnicamente aperto: SentenzeWeb, su `italgiure.giustizia.it`, è un client sottile sopra una collezione di ricerca interrogabile senza credenziali, che restituisce JSON. Contiene 1.923.820 documenti complessivi, di cui 236.938 testi integrali penali e 189.542 civili, più un milione e mezzo di record di registro con i nomi delle parti in chiaro. Due proprietà lo rendono comunque inadatto anche prescindendo dalla liceità: i testi integrali coprono soltanto una finestra scorrevole dal 2021 a oggi, quindi mancano sistematicamente le decisioni anteriori da cui un orientamento attuale si discosta, e non contiene alcuna massima.

Le condizioni d'uso pubblicate dal CED[^4] sono queste, alla lettera.

```
I documenti si possono utilizzare soltanto per uso proprio; è vietata la
distribuzione anche gratuita dei documenti ottenuti, la riproduzione su
supporti informatici nonché l'elaborazione dei dati del CED.
(Art. 9 del DPR 322 del 1981)
```

La convenzione di abbonamento attualmente in distribuzione aggiunge una clausola scritta per questo scenario.

```
È vietato in ogni caso sottoporre a trattamento, anche automatizzato, mediante
sistemi di intelligenza artificiale, i documenti, le informazioni e i dati resi
disponibili dal CED.
```

Riprodurre i documenti su un supporto adatto all'elaborazione elettronica e sottoporli a un sistema di intelligenza artificiale sono le due cose che questo prodotto fa, e sono le due che il titolare vieta per nome. Le massime, poi, stanno solo dietro l'abbonamento a pagamento e ricadono nelle stesse clausole. Si aggiunge, in modo indipendente, un problema di dati personali: i record di registro contengono in chiaro nomi di parti e difensori, e copiarli in un archivio locale ricercabile è un trattamento per cui l'esenzione domestica del GDPR[^5] è fragile.

Un punto di onestà sul perimetro: se l'art. 9 del DPR 322/1981, scritto in un regolamento sulla concessione dell'utenza, vincoli anche il visitatore anonimo che nessuna concessione ha sottoscritto è una questione giuridica che questa analisi non risolve e che resta non verificata. Resta però che per il canale pubblico non è pubblicata alcuna licenza, che le risposte portano un'intestazione che chiede di non essere indicizzate, e che il titolare invoca espressamente anche la tutela sui generis sulla banca dati. La direzione della volontà del titolare non è interpretabile in due modi. Va anche notato che l'art. 5 della legge 633/1941, che sottrae al diritto d'autore i testi degli atti ufficiali dello Stato, qui non aiuta: il vincolo non è di diritto d'autore sul testo, e le massime sono elaborazioni redazionali dell'Ufficio del massimario, non l'atto ufficiale.

### Merito e giustizia amministrativa

La Banca Dati di Merito Pubblica contiene circa 3,5 milioni di provvedimenti civili pseudonimizzati dal 2016, ma è accessibile solo dal Portale dei Servizi Telematici con identità digitale, senza API né scarico massivo né licenza di riuso; le note legali autorizzano la riproduzione per finalità non commerciali citando la fonte, e il riuso strutturato passa da accordi individuali, come mostra la convenzione fra Ministero e Associazione Italiana Editori del gennaio 2025.

OpenGA della giustizia amministrativa è l'unico portale giudiziario con una licenza aperta piena dichiarata, ma il contenuto è di registro e di statistica: scaricando un dataset reale si trovano sede, sezione, numero, esito e oggetto del ricorso, e non si trova la motivazione né il testo. È un livello di metadati, non un corpus giurisprudenziale. Il dominio `dati.giustizia.it`, spesso citato, non esiste: la risoluzione DNS fallisce.

## 3. Lo schema dei chunk non regge le sentenze

Alcune corrispondenze fra lo schema attuale e una pronuncia sono innocue: il campo dell'URN accoglie bene un ECLI, che gli open data forniscono già, la collezione è riusabile come provenienza, il percorso resta il file di origine. Numero e data accolgono numero e data di deposito, con la perdita che una sentenza ha due date entrambe rilevanti, decisione e deposito, e una sola colonna disponibile. Tre corrispondenze invece rompono, e non per questioni di eleganza.

La prima riguarda la rubrica, ed è la più grave perché contaminerebbe la parte normativa già funzionante. Le rubriche presenti nell'indice hanno una mediana di quattro token di contenuto e un novantesimo percentile di undici; il titolo di una massima della Corte costituzionale, misurato su un campione recente, ha una mediana di cinquantacinque token. È un ordine di grandezza di differenza, su una colonna che pesa dodici volte il corpo. Il bonus di rubrica del progetto calcola quanta parte dell'etichetta è coperta dalle parole della domanda e scatta sopra la metà: su un'etichetta di cinquantacinque token non scatterà mai, quindi il meccanismo che da solo ha portato il recall@8 da 15/26 a 19/26 sarebbe inerte sulle massime, mentre il peso dodici farebbe scavalcare l'articolo la cui rubrica è il nomen iuris esatto da parte di una massima che condivide con la domanda due o tre parole generiche. Non è un problema di taratura: un solo vettore di pesi non può servire un'etichetta di quattro token e una di cinquantacinque.

La seconda riguarda il campo della vigenza, e il problema non è che sia priva di senso, è che sarebbe attivamente pericolosa. La ricerca filtra per vigenza attiva per default, quindi perché una sentenza sia trovabile bisognerebbe scriverla come vigente, cioè asserire nel dato qualcosa che il dato non sostiene.

La terza riguarda l'articolo. Una sentenza non ha articoli, e la deduplica della ricerca ha per chiave la coppia URN e articolo: se tutti i chunk di una pronuncia avessero articolo vuoto, la deduplica collasserebbe l'intera sentenza a un solo risultato; se si piegasse quel campo a ospitare il numero di massima, la colonna significherebbe due cose diverse.

Restano senza posto, infine, proprio i dati che rendono utile una sentenza e che le fonti forniscono già strutturati: organo, sezione, esito, materia, tipologia di giudizio, riferimenti normativi e citazioni di precedenti. La conclusione è una tabella distinta, con pesi e logica di bonus propri, un tool MCP separato, e i riferimenti normativi in una tabella relazionale ordinaria e non full-text. Quest'ultimo punto è il vero guadagno: la domanda su quali pronunce interpretino l'art. 2043 del codice civile diventa una join deterministica, che non consuma token e non dipende dal lessico. Lo schema attuale non può esprimerla in alcun modo.

## 4. La ricerca lessicale è più debole qui che sulla normativa

Il limite già misurato sulla normativa, cioè circa il 27 per cento dei concetti che non emerge perché la parola non è nella rubrica, si aggrava sulla giurisprudenza per tre ragioni distinte.

Sulla normativa l'etichetta esiste ed è un nomen iuris stabile e breve, e il fallimento è che la domanda usi un sinonimo. Una massima non ha nomen iuris: il suo titolo è una catena di descrittori procedurali scritta nel linguaggio classificatorio interno dell'Ufficio del massimario, non la lingua in cui si formula una domanda. Il disallineamento inoltre si inverte: il bonus del progetto è tarato sul fatto che le domande sono più prolisse delle rubriche, mentre qui l'etichetta è prolissa e la domanda è breve e concettuale, quindi si invertono sia il verso sia la magnitudine e nessuna riponderazione recupera l'euristica.

La conferma più forte viene dall'istituzione stessa: la collezione pubblica del CED contiene 6.806 documenti che sono una tabella di sinonimi costruita a mano, con voci che espandono per esempio l'abbagliamento su abbagliare, anabbagliante, abbagliante e fanale. Il soggetto che gestisce da più tempo la ricerca lessicale sulla giurisprudenza italiana ha ritenuto necessario affiancarle un thesaurus manuale, e questo progetto non ha nulla di equivalente.

Esiste un solo fattore mitigante, ed è reale: per la Corte costituzionale i riferimenti normativi strutturati offrono una via di recupero che non passa dal lessico. Nessun numero di recall è stato misurato su giurisprudenza, perché non esiste un benchmark e produrne uno a tavolino sarebbe inventato; l'affermazione che il punto di partenza sarebbe più vicino al 15/26 pre-bonus che al 19/26 è un'inferenza ragionata e va trattata come tale.

## 5. Il rischio del precedente superato

L'abrogazione è un evento: ha una data, un autore, un atto pubblicato e un esito binario. L'*overruling*[^6] è un processo diffuso, graduale, talvolta non dichiarato: una sezione si discosta senza dirlo, le sezioni unite compongono un contrasto senza formalmente rovesciare, il diritto vivente si sposta su una dozzina di decisioni. Nessuna autorità pubblica un indicatore, quindi la colonna non manca per dimenticanza: manca il fatto sottostante.

Nell'architettura di questo prodotto la conseguenza è precisa, e peggiore di quanto sembri. La proposta di valore è la citazione verificabile. Una citazione verificabile a una sentenza reale che non rappresenta più l'orientamento è peggio di nessuna citazione, perché il passo di verifica riesce: l'utente controlla il virgolettato, lo trova esatto, e ne è confermato nell'errore. Sulla normativa la stessa architettura ha una difesa vera, il flag di vigenza, che il parser addirittura irrobustisce declassando la collezione degli abrogati. Qui non esiste nulla di analogo, e inventare un indicatore euristico sarebbe l'opzione peggiore, perché somiglierebbe alla garanzia della normativa senza esserlo.

Il rischio è però asimmetrico per fonte, e questa asimmetria è la ragione principale della conclusione. Per la Corte costituzionale è in larga parte governabile, perché la dichiarazione di illegittimità è definitiva ed erga omnes ai sensi dell'art. 136 della Costituzione, quindi una sentenza di accoglimento non viene superata: rimuove la norma. Il residuo si concentra sulle decisioni di rigetto e su quelle interpretative, e per queste il 27 per cento di massime che citano precedenti, parsato in un grafo di citazioni, permette di mostrare le pronunce successive che citano quella su cui si sta per fare affidamento. Non è un indicatore di superamento, ma è abbastanza per non rispondere con sicurezza quando esiste una pronuncia citante più recente. Per la Cassazione non è governabile con i dati pubblici, perché una finestra di cinque anni senza massime e senza le segnalazioni di contrasto significa ragionare di orientamento con un corpus strutturalmente incapace di mostrarlo. Per il merito è in gran parte privo di senso, perché una sentenza di tribunale non è precedente in alcuna accezione vincolante e milioni di provvedimenti recuperati per via lessicale sono una macchina per citare con sicurezza pronunce isolate di primo grado, magari riformate in appello senza che nulla nel record lo dica.

## 6. Conclusione

Procedere solo sulla Corte costituzionale, dagli open data ufficiali, in una tabella full-text distinta con un tool MCP distinto, e non procedere su Cassazione, merito e dottrina.

Le ragioni in ordine di peso sono queste. La legittimità è chiara e verificabile solo per la Corte costituzionale, con licenza esplicita, formato macchina, testo integrale e massime separate. Sulla Cassazione non c'è un rischio da soppesare ma un divieto scritto che nomina le operazioni che il progetto compie, e quella linea non si attraversa per il fatto che l'accesso sia tecnicamente aperto. Il merito è dietro identità digitale senza licenza di riuso. Il costo del sottoinsieme è piccolo. E la capacità genuinamente nuova non sarebbe la ricerca full-text, che come argomentato sopra sarebbe più debole che sulla normativa, ma la congiunzione fra norma e giurisprudenza attraverso i riferimenti strutturati, che è deterministica e risponde alla domanda che un professionista pone davvero.

Va detto con chiarezza nel disclaimer, e non lasciato intendere, che coprire la Corte costituzionale non è coprire la giurisprudenza italiana. Un prodotto che aggiunge la Corte costituzionale e lascia credere di avere la giurisprudenza creerebbe un problema di onestà più grande di quello che risolve, ed è lo stesso difetto, l'incompletezza silenziosa, da cui è nato l'audit del corpus.

Non verificato: la completezza dell'archivio della Corte per l'anno in corso oltre alle date dei file, l'endpoint SPARQL, e se l'esposizione in chiaro della collezione di ricerca del CED sia intenzionale, circostanza che comunque non cambia nulla sulle condizioni di riuso.

[^1]: *bot manager* - servizio che filtra il traffico automatizzato verso un sito e ne subordina l'accesso al superamento di una validazione.

[^2]: *ECLI*, European Case Law Identifier - identificatore europeo standard di una decisione giudiziaria, stabile e citabile.

[^3]: *SPARQL*, SPARQL Protocol and RDF Query Language - linguaggio di interrogazione per dati in forma di grafo, esposto come endpoint HTTP.

[^4]: *CED*, Centro Elettronico di Documentazione - struttura della Corte di cassazione che cura gli archivi di giurisprudenza interrogabili tramite ItalgiureWeb.

[^5]: *GDPR*, General Data Protection Regulation - regolamento (UE) 2016/679 sulla protezione dei dati personali, la cui esenzione per attività a carattere esclusivamente personale o domestico ha perimetro ristretto.

[^6]: *overruling* - mutamento dell'orientamento giurisprudenziale con cui un precedente consolidato viene abbandonato in favore di una diversa interpretazione.
