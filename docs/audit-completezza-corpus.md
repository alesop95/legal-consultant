# Audit di completezza del corpus

> Documento di progetto, tracciato. Misura quanto della legislazione italiana il corpus locale contiene davvero, confrontandolo con la fonte, ne diagnostica la causa a monte e ne descrive il modo di fallire. Nasce da un incarico esterno del 2026-07-28, scritto da un progetto che ha scoperto la lacuna usando questo strumento per capitoli medico-legali. Ogni cifra qui riportata è stata misurata sul corpus indicizzato o letta dall'API pubblica di Normattiva nella sessione del 2026-07-29; dove una verifica non è stata possibile è dichiarata come tale invece di essere inferita, per lo standard di `interaction-style.md`.

## 1. Il difetto, nella sua forma esatta

Il difetto non è che manchino alcune leggi. È che un'intera classe di atti normativi è assente da un corpus che si dichiara completo, e che l'assenza non si manifesta come errore: si manifesta come una risposta plausibile costruita su atti diversi da quello richiesto. Chi interroga il sistema legge un risultato pertinente al tema e ne conclude che quella sia la norma applicabile.

La verifica più eloquente non è un conteggio ma il comportamento osservabile del prodotto. Alla domanda sui termini dell'interruzione volontaria di gravidanza il tool `cerca_normativa` restituisce oggi quattro risultati, tutti pertinenti al tema e nessuno dei quali è la norma che lo disciplina: l'art. 19 del D.Lgs. 151/2001 sulla tutela della maternità, l'art. 99 del D.Lgs. 154/2013 la cui rubrica è letteralmente *Modifiche alla legge 22 maggio 1978, n. 194*, l'art. 73 dello stesso testo unico sull'indennità, e l'art. 593-bis del codice penale sull'interruzione colposa. Il corpus conosce l'atto che modifica la L. 194/1978 e non conosce la L. 194/1978. Alla domanda su consenso informato e disposizioni anticipate di trattamento la risposta contiene l'art. 580 del codice penale che cita la L. 219/2017 in nota, il regolamento ministeriale sulla banca dati delle DAT[^1], e la legge di ratifica della Convenzione di Rotterdam sul *consenso informato a priori* per i pesticidi pericolosi, che condivide con la domanda le parole e non l'oggetto. La L. 219/2017 non compare.

Un corpus dichiaratamente parziale sarebbe meno pericoloso di questo, perché chi lo interroga saprebbe di dover verificare altrove. Qui l'assenza della norma viene interpretata come inesistenza della norma, e il risultato restituito ne prende il posto.

## 2. Metodo di misura

L'audit procede su due accertamenti indipendenti, perché l'elenco delle collezioni presenti è esso stesso l'oggetto sotto esame e non può fare da metro a sé stesso.

Il primo accertamento è dall'alto e usa la fonte come denominatore. Normattiva espone da dicembre 2024 un'API[^2] Open Data pubblica e documentata, il cui gateway è dichiarato in chiaro in `https://dati.normattiva.it/assets/env.js` e la cui specifica OpenAPI 3.0.1 è pubblicata su `https://dati.normattiva.it/assets/come_fare_per/openapi-bff-opendata.json`. Nessuno schema di sicurezza è dichiarato e le chiamate riescono senza credenziali. Da essa si ricavano tre tipologiche: l'elenco canonico delle trenta denominazioni di atto, le tre classi di provvedimento (atto senza aggiornamenti, atto aggiornato, atto abrogato) e le collezioni predefinite. La rotta `POST /api/v1/ricerca/avanzata` restituisce in `numeroAttiTrovati` il conteggio autorevole degli atti per ciascuna combinazione di tipologia e classe, e pagina fino a mille elementi per richiesta, il che ha permesso di enumerare per intero gli insiemi rilevanti invece di stimarli.

Il secondo accertamento è dal basso ed è quello che ha rivelato il problema in partenza: un campione di sessantadue atti notori appartenenti a classi diverse, verificato uno per uno sul corpus. Il confronto avviene per famiglia di tipo, numero e anno ricavati dai metadati dell'indice, non per URN[^3] esatta, così che una data sbagliata nella lista del campione non possa produrre un falso risultato di assenza. Dove i due accertamenti divergono prevale il secondo.

Un accorgimento aritmetico va dichiarato perché una sua svista produce numeri sbagliati in modo convincente. Gli atti normativi italiani pubblicati in Gazzetta Ufficiale condividono un'unica serie progressiva annuale: nel 2024 il numero 202 è un decreto-legge, il 207 una legge e il 209 un decreto legislativo. Calcolare la copertura di una singola classe rapportandola al numero massimo raggiunto in quell'anno da quella classe usa quindi un denominatore che appartiene a tutte le classi insieme, e restituisce percentuali di copertura tanto basse quanto prive di significato. I conteggi di questo documento usano come denominatore i conteggi dichiarati dalla fonte per tipologia, non stime ricavate dalla numerazione.

## 3. Che cosa contiene il corpus, per tipologia

Il corpus indicizzato contiene 287.805 file, che corrispondono a 190.594 atti normativi distinti: 95.544 atti compaiono in più di una collezione e sono quindi contati più volte. La cifra di oltre 280.000 atti che il corpus dichiara, e che il tool `info_corpus` riporta all'utente, è un conteggio di file, non di norme; l'inflazione è di circa il cinquanta per cento sul numero reale di atti.

Il confronto per tipologia fra la fonte e il corpus è il seguente. La colonna Normattiva riporta `numeroAttiTrovati` della ricerca avanzata per quella denominazione, la colonna corpus gli atti distinti per URN presenti nell'indice locale.

| Tipologia | Normattiva | Corpus | Copertura |
|---|---:|---:|---:|
| COSTITUZIONE | 1 | 0 | assente |
| DECRETO PRESIDENZIALE | 7 | 0 | assente |
| DELIBERAZIONE | 16 | 0 | assente |
| DECRETO DEL CAPO DEL GOVERNO, PRIMO MINISTRO SEGRETARIO DI STATO | 1 | 0 | assente |
| DECRETO LEGISLATIVO PRESIDENZIALE | 59 | 2 | 3,4% |
| ORDINANZA | 26 | 2 | 7,7% |
| DECRETO-LEGGE | 3.856 | 2.267 | 58,8% |
| DECRETO DEL CAPO PROVVISORIO DELLO STATO | 1.222 | 820 | 67,1% |
| LEGGE | 32.680 | 23.351 | 71,5% |
| DECRETO DEL CAPO DEL GOVERNO | 25 | 18 | 72,0% |
| DECRETO | 2.537 | 2.138 | 84,3% |
| DECRETO LUOGOTENENZIALE | 7.554 | 6.555 | 86,8% |
| DECRETO MINISTERIALE | 409 | 377 | 92,2% |
| REGIO DECRETO-LEGGE | 10.071 | 9.744 | 96,8% |
| DECRETO DEL DUCE DEL FASCISMO, CAPO DEL GOVERNO | 37 | 36 | 97,3% |
| DECRETO-LEGGE LUOGOTENENZIALE | 1.366 | 1.345 | 98,5% |
| DECRETO DEL PRESIDENTE DEL CONSIGLIO DEI MINISTRI | 361 | 358 | 99,2% |
| DECRETO DEL PRESIDENTE DELLA REPUBBLICA | 47.760 | 47.431 | 99,3% |
| REGIO DECRETO | 91.346 | 90.970 | 99,6% |
| DECRETO LEGISLATIVO | 2.915 | 2.904 | 99,6% |
| LEGGE COSTITUZIONALE | 50 | 50 | 100% |
| REGIO DECRETO LEGISLATIVO | 120 | 120 | 100% |
| DECRETO LEGISLATIVO LUOGOTENENZIALE | 1.215 | 1.216 | 100,1% |
| Totale | 205.052 | 190.594 | 92,9% |

Le sette tipologie residue, tutte di dimensione unitaria o minima, risultano coperte integralmente e sono omesse per brevità. Il dato `DECRETO LEGISLATIVO LUOGOTENENZIALE` supera il cento per cento di un'unità: è un atto in più nel corpus rispetto alla fonte, non indagato perché ininfluente. Nessuna tipologia presente nel corpus è estranea all'elenco di Normattiva, quindi non ci sono classificazioni inventate a valle.

Letto in aggregato questo prospetto è rassicurante e va per questo maneggiato con diffidenza: il 92,9 per cento di copertura complessiva è vero e non risponde alla domanda che conta, perché il totale è dominato da 91.346 regi decreti e 47.760 decreti presidenziali di interesse prevalentemente storico, mentre la lacuna si concentra esattamente sugli atti che uno studio legale consulta ogni giorno. È la stessa illusione dei 287.805 atti dichiarati: un numero grande che copre un'assenza precisa.

## 4. Dove si concentra la lacuna

Per isolare la parte che conta, l'analisi scende sotto la tipologia e incrocia la classe di provvedimento, cioè lo stato di aggiornamento che la fonte stessa attribuisce a ogni atto. Le leggi non abrogate sono state enumerate integralmente dall'API, tutte e 13.730, e confrontate una per una con l'indice locale.

```
Leggi non abrogate su Normattiva          13.730   (10.503 mai modificate + 3.227 modificate e vigenti)
  presenti nel corpus                      4.417   32,2%
  ASSENTI dal corpus                       9.313   67,8%
     di cui mai modificate                 6.558
     di cui modificate e vigenti           2.755
```

Le 4.417 leggi presenti sono esattamente quelle che ricadono in un sottotipo qualificato, cioè leggi di conversione, di ratifica, costituzionali, delega, contenenti deleghe, finanziarie e di bilancio, di delegazione europea. Una legge ordinaria che non ricada in uno di quei sottotipi non appartiene a nessuna collezione e non esiste nel corpus. Il campione dal basso conferma la diagnosi in modo netto: delle trenta leggi ordinarie notorie verificate, ventinove sono assenti, fra cui la L. 194/1978 sull'interruzione volontaria di gravidanza, la L. 184/1983 sull'adozione, la L. 219/2017 sul consenso informato, la L. 833/1978 istitutiva del Servizio sanitario nazionale, la L. 40/2004 sulla procreazione assistita, la L. 405/1975 sui consultori, la L. 24/2017 sulla responsabilità sanitaria, la L. 241/1990 sul procedimento amministrativo, la L. 300/1970 statuto dei lavoratori, la L. 604/1966 sui licenziamenti individuali, la L. 898/1970 sul divorzio, la L. 91/1992 sulla cittadinanza, la L. 104/1992 sull'handicap, la L. 76/2016 sulle unioni civili, la L. 431/1998 sulle locazioni, la L. 633/1941 sul diritto d'autore, la L. 689/1981 sulle sanzioni amministrative e la L. 69/2019 detta codice rosso. L'unica trentesima presente, la L. 675/1996 sul trattamento dei dati personali, c'è perché è stata abrogata, e c'è nel testo originale del 1996.

Il secondo fronte, che l'incarico non prevedeva e che l'audit ha trovato, riguarda i decreti-legge ed è quantitativamente più grave.

```
Decreti-legge non abrogati su Normattiva   1.636   (21 mai modificati + 1.615 modificati e vigenti)
  presenti nel corpus                         52   3,2%
  ASSENTI dal corpus                       1.584   96,8%
```

I 2.267 decreti-legge che il corpus contiene sono quasi interamente quelli abrogati o decaduti. Il decreto-legge convertito e vigente, che è la forma con cui in Italia si legifera nella pratica, è assente come testo proprio: presente è soltanto la sua legge di conversione, che non contiene il testo del decreto. Il file della L. 77/2020, che ha convertito il decreto Rilancio, pesa 4.125 byte e consiste nell'unico articolo della formula di conversione, con un collegamento in uscita a Normattiva per il testo del decreto e senza l'allegato delle modificazioni a cui la formula stessa rinvia. Le centinaia di articoli del D.L. 34/2020 non sono nel corpus in nessuna forma. Fra gli assenti ci sono i decreti-legge del 2026 in vigore oggi, dal D.L. 133/2026 sui prezzi petroliferi al D.L. 66/2026 sul piano casa.

Alla stessa famiglia di difetto appartiene un caso già noto al progetto e ora inquadrato nella sua causa comune. Il codice penale nella collezione `Codici` del corpus a monte è un guscio di quattro chunk: contiene la formula di approvazione del regio decreto e non il testo articolato allegato. Il codice penale interrogabile oggi, con i suoi 976 chunk, viene da `data/codici-extra`, cioè dal recupero autonomo che questo progetto aveva già dovuto fare. La stessa lacuna è segnalata upstream nella issue #3 del 2026-07-11, aperta da terzi e senza risposta.

Il filo comune fra legge di conversione senza decreto, decreto di approvazione senza codice e legge ordinaria assente è uno solo: il corpus a monte cattura l'atto come involucro formale e perde il contenuto normativo quando questo sta altrove, in un allegato o in un atto distinto.

Infine, tre assenze pulite e piccole ma di rilievo pratico sproporzionato alla loro dimensione. La Costituzione della Repubblica è per Normattiva una tipologia autonoma con un solo atto, e quell'atto non è nel corpus: nessuna URN del corpus contiene `costituzione`, e le uniche occorrenze dell'espressione nei titoli sono tre decreti di emissione di francobolli commemorativi. Le sedici deliberazioni e i sette decreti presidenziali sono assenti in blocco. Va invece corretta un'aspettativa che sembrava una quarta assenza: il codice di procedura penale è presente, perché in Normattiva non è una tipologia ma il DPR 447/1988, e come DPR il corpus lo contiene.

## 5. Diagnosi della causa a monte

Il corpus è prodotto dallo script pubblico `ahmeabd/italia-corpus-script`. La causa non è un elenco di collezioni cablato nel codice, non è un filtro che scarta, e non è una scoperta dinamica che perde pezzi per errore. È che lo script adotta come unica fonte di verità il catalogo delle collezioni preconfezionate che Normattiva stessa espone, e quel catalogo non contiene la legge ordinaria.

Il `config.py` dello script dichiara un solo endpoint di enumerazione.

```python
BASE_URL = "https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1"
ENDPOINT_URL = f"{BASE_URL}/collections/download/collection-preconfezionata"
COLLECTIONS_URL = f"{BASE_URL}/collections/collection-predefinite"
```

Il modulo `normattiva.py` esegue la **GET** su `COLLECTIONS_URL` e restituisce la lista senza toccarla; l'unico scarto in tutto il modulo è il salto delle righe con nome vuoto. In `pipeline.py` la lista arriva intatta al ciclo di download e l'unico `continue` è di nuovo sul nome vuoto. Non esistono allowlist, blocklist, slicing né limiti di conteggio, e `__main__.py` non espone alcuna opzione per aggiungere collezioni. Lo script è quindi un mirror fedele: la lacuna è ereditata, non introdotta.

L'endpoint di produzione restituisce sessantasette righe che si riducono a ventitré collezioni distinte, declinate nei formati originale, multivigente e vigente, e i ventitré nomi coincidono uno a uno con le ventitré cartelle di primo livello del corpus. Fra quei nomi non c'è una voce `Leggi`, e non c'è una voce per la Costituzione. Le collezioni predefinite non sono una partizione di Normattiva ma pacchetti tematici curati, che coprono decreti, regolamenti, testi unici, codici e i soli sottotipi qualificati di legge.

Ne segue una distinzione che è il cuore della diagnosi. L'affermazione del README del corpus secondo cui le collezioni sono ventitré in sync completo è letteralmente vera rispetto al catalogo delle collezioni predefinite. L'affermazione secondo cui il corpus raccoglie tutta la legislazione pubblicata su Normattiva non è sostenuta, e non è documentata da nessuna parte come limite noto: il `CONTRIBUTING.md` invita a segnalare atti mancanti ma non dichiara quali collezioni siano coperte. La cifra da usare come pietra di paragone è quella delle FAQ di Normattiva, cioè tutti gli atti normativi numerati pubblicati in Gazzetta Ufficiale o nella Raccolta Ufficiale dal 1861 a oggi.

Esiste inoltre, e non è usata dallo script, una seconda via di export nella stessa API che raggiunge la classe mancante. La legge ordinaria ha un proprio codice di tipo provvedimento, `PLE`, distinto da `PLC` della legge costituzionale, e la ricerca avanzata accetta `denominazioneAtto` con paginazione fino a mille elementi: è la via con cui questo audit ha enumerato le 13.730 leggi non abrogate. Sopra di essa sta un flusso asincrono di export massivo, `nuova-ricerca` che restituisce un token, `conferma-ricerca` in PUT, polling su `check-status` fino allo stato 303 e download dello ZIP dall'header `x-ipzs-location`, con formati di uscita che comprendono lo stesso Akoma Ntoso[^4] che il convertitore dello script già sa interpretare. Esiste anche `dettaglio-atto-urn`, aggiunta nella revisione del 10 marzo 2026, per il recupero puntuale di un singolo atto per URN.

Due cautele su questa via, dichiarate come non verificate. Il flusso asincrono non è stato eseguito, quindi la fattibilità pratica di un export massivo dell'intera classe `PLE` non è provata, né lo sono i suoi limiti di dimensione e l'effettiva necessità della conferma via email; la specifica documenta uno stato 503 di carico eccessivo, quindi esiste un throttling lato IPZS[^5]. E davanti al gateway c'è un WAF[^6], perché `https://dati.normattiva.it/api` risponde 409 dichiarando il blocco: un uso massivo non può essere assunto come consentito senza verificarlo.

## 6. Vitalità del progetto a monte

Il dato serve a decidere dove intervenire, e va letto per quello che è: numeri osservati su GitHub il 2026-07-29, non una previsione di comportamento del maintainer.

Il repository dello script ha come ultimo commit il 2026-06-21, circa cinque settimane prima dell'audit, e non ha mai avuto issue né pull request: zero aperte e zero chiuse in entrambe le categorie. Non esiste quindi alcuna evidenza misurabile dei tempi di risposta a un contributo esterno, né in senso favorevole né in senso contrario. Il repository del dataset ha 503 commit e come ultimo commit il 2026-07-18: fino a quella data il job girava effettivamente ogni giorno, e da undici giorni non produce commit, quindi il sync dichiarato ogni ventiquattro ore risulta fermo. La causa dell'interruzione non è osservabile da GitHub e non è stata accertata. Le due issue aperte sul dataset, la #2 del 2026-07-04 sulle norme tecniche e la #3 del 2026-07-11 sul testo mancante degli articoli di codice penale e civile, risultano senza risposta del maintainer nel contenuto letto, rispettivamente da venticinque e diciotto giorni. Nessuna issue, in nessuno dei due repository, segnala l'assenza della legge ordinaria.

## 7. Tabella di sintesi dell'audit

| Ambito | Esito | Misura |
|---|---|---|
| Leggi ordinarie non abrogate | manca | 9.313 assenti su 13.730, di cui 2.755 modificate e vigenti |
| Decreti-legge non abrogati | manca | 1.584 assenti su 1.636; presente solo la legge di conversione, senza il testo del decreto |
| Costituzione della Repubblica | manca | 1 atto, assente |
| Deliberazioni, decreti presidenziali | manca | 16 e 7 atti, assenti in blocco |
| Decreti legislativi presidenziali, ordinanze | parziale | 2 su 59 e 2 su 26 |
| Testo articolato dei codici allegati a regio decreto | manca a monte | guscio di 4 chunk; supplito localmente da `data/codici-extra` |
| Decreti legislativi, DPR, testi unici, codici, regi decreti | c'è | copertura fra 99,3% e 100% |
| Leggi costituzionali, di ratifica, di conversione, di bilancio, delega | c'è | le 4.417 leggi presenti sono tutte e solo queste |
| Codice di procedura penale | c'è | è il DPR 447/1988, non una tipologia autonoma |
| Conteggio degli atti dichiarato dal prodotto | fuorviante | 287.805 file corrispondono a 190.594 atti distinti |
| Giurisprudenza e dottrina | fuori perimetro | nessuna collezione, tabella o campo la prevede |
| Fattibilità dell'export massivo asincrono | non verificato | flusso non eseguito; throttling e WAF documentati |
| Causa dell'arresto del sync a monte dal 2026-07-18 | non verificato | non osservabile da GitHub |
| Completezza interna delle 23 collezioni presenti | non verificato | le collezioni sono pacchetti curati, non dump per tipo |

## 8. Che cosa questo audit non dice

Non dice che il motore sia difettoso. L'indice FTS5[^7], il ranking pesato e il server MCP[^8] funzionano e non sono in discussione: la copertura è un problema di ingresso dei dati, non di recupero. Non dice che le ventitré collezioni presenti siano complete al loro interno: la ricerca a monte suggerisce che siano sottoinsiemi curati, e verificarlo richiederebbe di campionare ciascuna collezione contro la ricerca avanzata sulla stessa tipologia, cosa non fatta. Non dice nulla sulla legislazione regionale, che vive su un sistema separato e resta fuori dal perimetro dichiarato del progetto.

[^1]: *DAT*, disposizioni anticipate di trattamento - dichiarazioni con cui una persona esprime in anticipo le proprie volontà in materia di trattamenti sanitari, disciplinate dalla L. 219/2017.

[^2]: *API*, Application Programming Interface - interfaccia con cui un sistema espone i propri dati a un altro programma in modo strutturato, invece che a un lettore umano.

[^3]: *URN*, Uniform Resource Name - identificatore stabile e canonico di un atto normativo; nello standard NIR italiano ha la forma `urn:nir:stato:legge:1978-05-22;194`.

[^4]: *Akoma Ntoso* - standard OASIS di rappresentazione XML dei documenti giuridici, che struttura articoli, rubriche e commi in modo esplicito invece di affidarli alla formattazione.

[^5]: *IPZS*, Istituto Poligrafico e Zecca dello Stato - ente che gestisce la pubblicazione della Gazzetta Ufficiale e l'infrastruttura di Normattiva.

[^6]: *WAF*, Web Application Firewall - filtro che ispeziona il traffico verso un servizio web e può bloccarlo prima che raggiunga l'applicazione.

[^7]: *FTS5*, Full-Text Search versione 5 - modulo di SQLite per la ricerca full-text con ranking BM25 nativo, usato come indice locale del progetto.

[^8]: *MCP*, Model Context Protocol - standard con cui un client AI dialoga con sistemi esterni attraverso tool esposti da un server; qui è il server locale `legge-it`.
