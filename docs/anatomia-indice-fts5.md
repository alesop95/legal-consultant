# Anatomia dell'indice: perché `legge.sqlite` pesa 3,1 GB

> Documento di misura, scritto il 2026-10-14 su domanda del proprietario, che chiedeva perché l'indice pesasse tanto e se si potesse snellire. Nessun file è stato modificato: questo documento misura e descrive le strade, non ne percorre nessuna. Le misure sono state prese in sola lettura con `PRAGMA query_only`, e ogni interrogazione usata è riportata qui sotto perché chiunque possa rifarle.

## La domanda e la risposta corta

L'indice occupa 3,23 GB, cioè 788.543 pagine da 4096 byte. La scomposizione, misurata sommando la lunghezza effettiva dei valori tabella per tabella, è questa.

| componente | peso | che cos'è |
|---|---|---|
| `chunks_content` | 1,797 GB | i valori delle colonne, cioè una copia integrale del testo indicizzato più i metadati |
| `chunks_data` | 1,077 GB | l'indice invertito vero e proprio, cioè le liste di posizioni dei termini |
| `chunks_docsize` | 11,3 MB | la lunghezza di ogni documento, serve a BM25 |
| `chunks_idx` | 0,4 MB | la mappa dei termini verso i blocchi di `chunks_data` |
| pagine di struttura e spazio libero | circa 0,34 GB | alberi B, intestazioni, frammentazione |

Dentro `chunks_content` il solo campo `testo` vale 1,390 GB, il campo `titolo` 140 MB e il campo `path` 150 MB. Il dato che risponde alla domanda è il primo: **l'indice contiene una seconda copia integrale del corpus**. Il corpus su disco, in `data/italia-corpus/`, è fatto di 287.834 file Markdown per 1,414 GB di byte effettivi, e il testo dentro l'indice è sostanzialmente lo stesso materiale, spezzato in chunk.

Non è uno spreco accidentale ed è bene dirlo subito, perché la reazione istintiva davanti a una copia è toglierla. Quella copia è il prezzo di una funzione precisa: `src/legal_consultant/index/fts.py` alla riga 214 costruisce il risultato della ricerca con `snippet(chunks, ...)`, cioè chiede a SQLite l'estratto con il termine cercato evidenziato, e alla riga 261 rilegge l'articolo intero con una `SELECT ... testo`. FTS5 può fare entrambe le cose solo se il contenuto delle colonne è memorizzato nella tabella. Un indice che trovasse gli atti senza poter mostrare l'estratto costerebbe un terzo dello spazio e restituirebbe un elenco di titoli.

## Come è fatta la tabella

```sql
CREATE VIRTUAL TABLE chunks USING fts5(
  urn UNINDEXED, tipo UNINDEXED, numero UNINDEXED, data UNINDEXED,
  titolo, collezione UNINDEXED, articolo, rubrica,
  vigente UNINDEXED, path UNINDEXED, testo,
  tokenize = 'unicode61 remove_diacritics 2'
);
```

Le righe sono 997.660, cioè i chunk, e corrispondono a 193.109 valori distinti di `urn` e ai 290.320 atti dichiarati in `data/index/state.json`. La lunghezza media di un chunk è di 1393 caratteri. Quattro colonne sono indicizzate, `titolo`, `articolo`, `rubrica` e `testo`, e il ranking le pesa diversamente, con `rubrica` a 12, `titolo` a 3 e `testo` a 1; le altre sette sono `UNINDEXED`, cioè non finiscono nell'indice invertito ma vengono comunque memorizzate per intero, perché servono a comporre la citazione nella risposta.

Qui sta una ridondanza che è utile vedere, anche se non è la voce principale. Sette colonne su undici descrivono l'atto e non il chunk: l'urn, il tipo, il numero, la data, la collezione, lo stato di vigenza e il percorso del file sono identici per tutti i chunk dello stesso atto. Sono scritte 997.660 volte quando gli atti distinti sono meno di trecentomila. Lo stesso vale per `titolo`, che però è indicizzato e serve al ranking, quindi non si tratta allo stesso modo. Le sole colonne genuinamente per chunk sono `articolo`, `rubrica` e `testo`.

## Le quattro strade, con il loro costo

La prima è il `VACUUM`, ed è giusto nominarla per toglierla di mezzo: la lista delle pagine libere è di 3237 pagine, cioè 13 MB su 3,23 GB. Non c'è niente da recuperare, l'indice non è gonfio di spazio sprecato.

La seconda è normalizzare i metadati per atto, spostando le sette colonne `UNINDEXED` in una tabella ordinaria di atti e lasciando nei chunk un solo riferimento. Vale circa 250 MB, cioè l'otto per cento, e costa un cambio di schema in `fts.py` più una reindicizzazione completa. È un intervento contenuto che non cambia il comportamento: stesse risposte, stesso ranking, stessi estratti.

La terza è ridurre il perimetro, ed è una decisione editoriale travestita da decisione tecnica. La collezione «Atti normativi abrogati (in originale)» conta 416.040 righe su 997.660, cioè il 42 per cento delle righe, per 0,402 GB di testo; con la sua quota di indice e di metadati vale circa 0,8-0,9 GB. Prima di proporla ho verificato se fosse ridondante, perché un'abrogazione in originale potrebbe duplicare il testo vigente: non lo è. Confrontando le impronte dei testi, solo 6494 righe su 416.040 hanno un testo identico a un chunk vigente, cioè l'1,6 per cento. Quelle righe sono contenuto, non duplicazione, e toglierle significa rinunciare a cercare nel diritto abrogato, che per una consulenza su fatti passati è esattamente ciò che serve. La decisione non è mia.

La quarta è l'unica che cambia l'ordine di grandezza, e anche l'unica che cambia il funzionamento. FTS5 ammette le tabelle *contentless*, dichiarate con `content=''`: l'indice invertito resta, il contenuto delle colonne non viene memorizzato. L'indice scenderebbe dai 3,23 GB attuali a poco più di 1,1, ai quali va aggiunta una tabella laterale con i metadati per atto e il riferimento al file, un centinaio di megabyte scarsi nella forma normalizzata. Il totale starebbe intorno a 1,2 GB, cioè meno di un terzo. Il prezzo è che `snippet()` smette di esistere e che `SELECT testo` non restituisce nulla: il testo andrebbe riletto dal file `.md` su disco usando il `path`, e l'estratto evidenziato andrebbe ricostruito in Python. Ogni risultato pagherebbe una lettura di file, e la logica di evidenziazione, che oggi è una riga di SQL, diventerebbe codice da scrivere, da provare e da mantenere allineato al tokenizzatore, perché un estratto che evidenzia la parola sbagliata è peggio di nessun estratto.

Va aggiunto un vincolo che non riguarda lo spazio ma la coerenza: in questa forma il corpus su disco diventa una dipendenza di esecuzione e non più solo di indicizzazione. Oggi `data/italia-corpus/` serve a costruire e ad aggiornare l'indice, e `scripts/auto_update.py` lo tiene allineato con un `git pull` più la reindicizzazione dei soli file cambiati; con l'indice contentless servirebbe anche a rispondere, e un corpus disallineato di un commit produrrebbe estratti che non corrispondono al testo indicizzato.

## Una misura collaterale che vale la pena conoscere

La cartella del corpus occupa 2,1 GB sul disco ma contiene 1,414 GB di byte: la differenza, circa 0,7 GB, è lo spazio perso in coda all'ultimo cluster di ciascuno dei 287.834 file, che su NTFS con cluster da 4 KB e file di quattro o cinque kilobyte in media è una perdita strutturale e non un difetto. La compressione NTFS su quella sola cartella la recupererebbe quasi tutta ed è trasparente a git, al prezzo di operazioni di git più lente. Sul file `.sqlite` invece non va attivata: un database scritto in luogo dentro un file compresso dal filesystem si frammenta e rallenta. Gli oggetti git del corpus, in `.git/modules/data/italia-corpus`, pesano altri 522 MB.

Per contesto: il volume E: ha 203 GB liberi su 239, quindi nessuna di queste strade è urgente. Contano più per i tempi di copia e di backup che per lo spazio.

## Come rifare le misure

Tutte in sola lettura. La scomposizione per tabella, che è il numero da cui parte questo documento, si ottiene sommando le lunghezze dei valori, perché l'estensione `dbstat` non è compilata nel SQLite di questo Python.

```sql
SELECT sum(length(coalesce(c0,''))+length(coalesce(c1,''))+length(coalesce(c2,''))
         + length(coalesce(c3,''))+length(coalesce(c4,''))+length(coalesce(c5,''))
         + length(coalesce(c6,''))+length(coalesce(c7,''))+length(coalesce(c8,''))
         + length(coalesce(c9,''))+length(coalesce(c10,''))) FROM chunks_content;
SELECT sum(length(c10)) FROM chunks_content;
SELECT sum(length(block)) FROM chunks_data;
SELECT c8, count(*), sum(length(c10)) FROM chunks_content GROUP BY c8;
```

Il confronto sulla ridondanza degli atti abrogati non va scritto come sotto-interrogazione correlata, perché su un milione di righe diventa quadratico e non termina in tempi utili: si leggono le righe una volta sola, si tiene in memoria l'insieme delle impronte dei testi vigenti e si contano gli abrogati che vi corrispondono. In Python sono una ventina di righe e un paio di minuti.

Le dimensioni del corpus si misurano sui byte effettivi e non con `du`, che riporta lo spazio occupato sul disco e quindi include lo spreco dei cluster:

```powershell
(Get-ChildItem -Path data/italia-corpus -Filter *.md -Recurse | Measure-Object -Property Length -Sum).Sum
```

## Che cosa è stato deciso

Niente, per ora, ed è una scelta. L'intervento del 2026-10-14 riguardava gli export Discord di un altro progetto, dove la compressione è reversibile bit per bit e la prova di non averla sbagliata si scrive in un manifesto di impronte. Qui nessuna delle strade ha quella proprietà: la seconda e la terza richiedono di ricostruire l'indice, la quarta di riscrivere il modo in cui si ottengono gli estratti. Per ciascuna, prima di percorrerla, va congelata una batteria di interrogazioni reali con le risposte attuali, inclusi gli estratti, e il confronto riga per riga va fatto su una copia del database prima di sostituire l'originale. `scripts/benchmark_retrieval.py` è il punto da cui partire per costruire quella batteria.
