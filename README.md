# Consulente Legale

Assistente legale locale per uso privato e aziendale, basato sul corpus della
legislazione italiana ([italia-corpus](https://github.com/ahmeabd/italia-corpus)).
Realizzato come **MCP server locale** interrogato da **Claude Desktop**.

- **Usa l'abbonamento Claude Team** — il ragionamento lo fa Claude Desktop chiamando i
  tool dell'MCP server. Nessun costo API pay-as-you-go.
- **Locale e privacy-first:** corpus, indice e ricerca interamente sulla tua macchina.
  Solo la conversazione (domanda + estratti restituiti) passa per Claude Desktop.
- **No GPU:** ricerca **BM25 / full-text** (SQLite FTS5). Indicizzazione veloce.
- **Sempre aggiornato:** il corpus è un clone locale di italia-corpus, aggiornabile con
  `git pull` e reindicizzazione incrementale (`scripts/update_corpus.py`).
- **Codici fondamentali inclusi:** civile, penale, procedura civile, navigazione e penali
  militari, il cui articolato manca in italia-corpus, sono scaricati da Normattiva e
  versionati nel repo (`data/codici-extra`).
- **Lacune di italia-corpus colmate dalla fonte ufficiale:** il corpus di terze parti
  rispecchia il catalogo delle collezioni preconfezionate di Normattiva, che non comprende
  la legge ordinaria, il decreto-legge vigente e la Costituzione. Queste classi vengono
  recuperate dall'API Open Data di Normattiva (`scripts/fetch_normattiva.py`) e indicizzate
  accanto alle altre. La misura della lacuna è in
  **[docs/audit-completezza-corpus.md](docs/audit-completezza-corpus.md)**.
- **Completezza verificabile a comando:** `scripts/check_completezza.py` confronta il corpus
  con le tipologie dichiarate dalla fonte e con una lista di atti notori, e fallisce dicendo
  cosa manca invece di restituire un totale rassicurante.

> ⚠️ Strumento informativo, **non costituisce consulenza legale**. Per uso professionale
> fare sempre riferimento alla *Gazzetta Ufficiale* / [Normattiva](https://www.normattiva.it).

## Stato

Funzionante e verificato end-to-end in Claude Desktop: alla domanda risponde citando gli
articoli con il loro URN, dal corpus locale, senza ricorso al web. Vedi
**[HANDOFF.md](HANDOFF.md)** per architettura, stack e decisioni.

## Installazione

### Windows, un clic (consigliata per l'uso finale)

Prerequisito: Claude Desktop già installato (piano Team). Non serve altro software
preesistente: né Python, né git, né conoscenze tecniche.

Per procurarsi il progetto senza usare git, sulla pagina GitHub del repository si preme il
pulsante verde **Code**, poi **Download ZIP**, e si estrae lo ZIP scaricato in una cartella a
piacere. Fatto questo, doppio clic su **`install.cmd`** dentro quella cartella.

Lo script, senza privilegi di amministratore, installa `git` e `uv` se mancano, configura git
per i percorsi lunghi (i nomi-file del corpus superano i 260 caratteri di Windows), scarica il
corpus, costruisce l'indice e registra il server `legge-it` in Claude Desktop preservando gli
altri server. La prima esecuzione richiede una connessione internet e dura tipicamente 15-20
minuti (il tempo dipende dalla velocità della connessione e dal disco): la maggior parte è
download del corpus (circa 2 GB) e costruzione dell'indice. Si apre una finestra nera con
scritte tecniche in inglese e italiano: è normale, non richiede di leggerla né di intervenire,
va solo lasciata finire.

Se Windows mostra un avviso blu **"Windows ha protetto il PC"** (SmartScreen, tipico sui
portatili aziendali con antivirus gestito dall'IT), è perché lo script è scaricato da internet
e non firmato digitalmente, non perché sia dannoso: si sceglie **Ulteriori informazioni** e poi
**Esegui comunque**. In caso di dubbio, verificare con il proprio reparto IT prima di procedere.

Se qualcosa va storto a metà (connessione caduta, PC spento), si può rilanciare `install.cmd`
tutte le volte che serve: riprende da dove serve senza ripetere i passi già completati (per
esempio non riscarica il corpus se è già presente) e non danneggia nulla.

Al termine: chiudere **del tutto** Claude Desktop (anche dall'icona nella tray vicino
all'orologio) e riaprirlo. Per verificare che tutto funzioni, fare una domanda di diritto
italiano qualsiasi (per esempio "quali sono i termini di prescrizione per il reato di
omicidio?"): la risposta deve citare gli articoli con il loro riferimento normativo (URN) e
chiudersi con un disclaimer.

### Manuale (sviluppatori, o altri OS)

```bash
uv run python scripts/setup.py        # clona il corpus, sincronizza l'ambiente, indicizza
```

Poi registrare il server nel client. Per **Claude Code** è già pronto `.mcp.json` in radice:
basta aprire il progetto e approvare il server. Per **Claude Desktop** aggiungere a
`claude_desktop_config.json` (usare il percorso assoluto di `uv` se non è nel PATH):

```json
"legge-it": {
  "command": "uv",
  "args": ["--directory", "E:\\legal-consultant", "run", "python", "-m",
           "legal_consultant.mcp_server"]
}
```

## Uso

### Setup permanente: il Project (consigliato)

In Claude Desktop creare un Project "Consulente Legale" e incollare nel campo istruzioni il
testo di **[`prompts/consulente-legale.md`](prompts/consulente-legale.md)**. Impone di usare
solo gli strumenti `legge-it`, mai la ricerca web, e di citare atto e articolo con l'URN. Da
lì ogni chat nel progetto si comporta da consulente legale senza altre indicazioni.

### Setup veloce: istruzione nella singola domanda

Senza Project, si antepone alla domanda l'istruzione esplicita:

```
Usando esclusivamente lo strumento legge-it e senza fare ricerche sul web,
<domanda di diritto italiano>.
```

Alla prima chiamata di ogni strumento scegliere **Consenti sempre** per non rivedere il prompt
di permesso.

### Strumenti esposti

`cerca_normativa` (ricerca BM25 → estratti citabili), `leggi_atto` (testo integrale di un atto
o articolo per URN), `info_corpus` (ampiezza e freschezza della base normativa).

## Aggiornamento della normativa

L'installazione Windows registra da sé un'attività pianificata (`ConsulenteLegale-Aggiornamento`)
che ogni giorno alle 6:00, se il PC è acceso e l'utente ha effettuato l'accesso, aggiorna il
corpus e — al più una volta alla settimana — i codici fondamentali, reindicizzando solo ciò che è
cambiato. Non richiede alcun intervento manuale né privilegi di amministratore; l'esito di ogni
esecuzione si trova in `data/index/auto_update.log`. Se la registrazione automatica fallisse (per
esempio per una policy aziendale che limita l'Utilità di pianificazione), l'installer lo segnala
ma prosegue comunque: l'aggiornamento va allora lanciato a mano, con lo stesso script che usa
l'attività pianificata:

```bash
uv run python scripts/auto_update.py      # corpus + codici, con la stessa logica dell'attività pianificata
```

Restano disponibili anche i due passaggi separati, utili per un aggiornamento mirato o per un
sistema diverso da Windows:

```bash
uv run python scripts/update_corpus.py     # solo il corpus: fetch + reset incrementale
uv run python scripts/fetch_codici.py      # ri-scarica i codici fondamentali da Normattiva
uv run python scripts/fetch_normattiva.py  # colma le classi assenti da italia-corpus
uv run python scripts/fetch_atto.py <urn>  # recupera un singolo atto dato il suo URN
```

## Verificare che la base normativa sia completa

```bash
uv run python scripts/check_completezza.py
```

Confronta le tipologie di atto che Normattiva dichiara con quelle presenti nell'indice, e
verifica una per una una lista di leggi che uno studio consulta davvero. Esce con codice 1 e
dice quale classe manca e quale atto atteso non si trova. È il rimedio a un difetto reale del
corpus di terze parti, documentato in
**[docs/audit-completezza-corpus.md](docs/audit-completezza-corpus.md)**: dichiarava sync
completo mentre mancavano oltre novemila leggi vigenti, e nulla lo segnalava.

Al primo avvio il recupero delle classi mancanti è progressivo: l'installer ne fa una parte a
partire dagli anni recenti e l'attività pianificata completa il resto nei giorni successivi,
perché il recupero storico dal 1861 richiede ore. Finché non è finito, il comando qui sopra
dice esattamente quanto resta.

## Limiti noti

Il filtro dei soli atti vigenti esclude la collezione delle abrogate, ma non garantisce la
vigenza odierna di ogni singolo atto: verificare sempre su Normattiva. La ricerca è lessicale
(BM25): per l'articolo esatto di un codice il consulente usa `leggi_atto`. Il corpus contiene
solo testo legislativo: nessuna giurisprudenza e nessuna dottrina, e le ragioni per cui
l'estensione è stata circoscritta alla sola Corte costituzionale sono in
**[docs/giurisprudenza-fattibilita.md](docs/giurisprudenza-fattibilita.md)**.
