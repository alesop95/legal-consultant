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

> ⚠️ Strumento informativo, **non costituisce consulenza legale**. Per uso professionale
> fare sempre riferimento alla *Gazzetta Ufficiale* / [Normattiva](https://www.normattiva.it).

## Stato

Funzionante e verificato end-to-end in Claude Desktop: alla domanda risponde citando gli
articoli con il loro URN, dal corpus locale, senza ricorso al web. Vedi
**[HANDOFF.md](HANDOFF.md)** per architettura, stack e decisioni.

## Installazione

### Windows, un clic (consigliata per l'uso finale)

Ottenuta la cartella del progetto, fare doppio clic su **`install.cmd`**. Lo script, senza
privilegi di amministratore, installa `git` e `uv` se mancano, configura git per i percorsi
lunghi (i nomi-file del corpus superano i 260 caratteri di Windows), scarica il corpus,
costruisce l'indice e registra il server `legge-it` in Claude Desktop preservando gli altri
server. La prima esecuzione dura qualche minuto (download del corpus e indicizzazione).

Al termine: chiudere **del tutto** Claude Desktop (anche dall'icona nella tray vicino
all'orologio) e riaprirlo.

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

```bash
uv run python scripts/update_corpus.py   # git pull del corpus + reindex incrementale
uv run python scripts/fetch_codici.py     # ri-scarica i codici fondamentali da Normattiva
```

Il primo si può schedulare (Windows Task Scheduler) per tenere la legge aggiornata.

## Limiti noti

Il filtro dei soli atti vigenti esclude la collezione delle abrogate, ma non garantisce la
vigenza odierna di ogni singolo atto: verificare sempre su Normattiva. La ricerca è lessicale
(BM25): per l'articolo esatto di un codice il consulente usa `leggi_atto`.
