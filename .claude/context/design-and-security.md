---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - src/legal_consultant/**
last-verified-commit: 889f843
---

# Design e sicurezza applicativa

> Aggiornato leggendo il codice di Fase 1 (ingest + indice) e Fase 2 (server MCP). Il confine di
> privacy di riferimento è in `HANDOFF.md`: corpus, indice e ricerca interamente locali; solo la
> conversazione (query + estratti) lascia la macchina via Claude Desktop.

## Paradigmi di software design

L'architettura è a strati con dipendenze a senso unico. In basso lo strato dati `index.fts`, che
conosce solo SQLite e FTS5 ed espone funzioni pure su una connessione (`search`, `get_act`,
`corpus_stats`, `insert_act`, `to_match_query`); accanto lo strato di ingest (`ingest.parser`), che
trasforma un file `.md` in `ParsedAct`, e il package `update` (Fase 3), che orchestra git e
reindicizzazione sopra lo strato dati separando la logica pura (`reindex_paths`, stato) dalle
chiamate a git (`corpus_revision`, `changed_files`, `pull`); in cima il server `mcp_server`, strato
di presentazione che fa wiring dei tre tool e del prompt MCP e formatta l'output con helper puri
(`_hit_to_dict`, `_citazione`). Il server non contiene logica di ricerca: la delega interamente a
`index.fts` e `update`. La scelta tiene tool e reindex verificabili sull'indice di fixture senza
avviare il transport MCP né toccare git, e isola il cambiamento del protocollo dal cambiamento
della ricerca. La configurazione dei percorsi è centralizzata in `config.py`, unico punto che legge
ambiente e `.env`. Il contratto tra moduli passa per le dataclass di `parser` (`Act`, `Chunk`,
`ParsedAct`) e per le `sqlite3.Row` dello strato dati, mai per strutture implicite.

## Sicurezza applicativa

Il confine di privacy è netto: corpus, indice e ricerca sono on-disk; il server gira come
sottoprocesso locale su stdio, senza alcuna superficie di rete. Solo la conversazione (la query e
gli estratti restituiti dai tool) lascia la macchina, e solo attraverso Claude Desktop. Il prodotto
non usa chiavi API e non gestisce segreti applicativi: `config.py` legge soltanto percorsi, mai
credenziali, e i valori di `.env` non si committano. La superficie esposta è l'insieme degli input
dei tre tool. Gli accessi al database sono tutti per query parametrizzate (binding `?`), quindi gli
identificatori e i filtri passati ai tool non aprono a SQL injection. Il parametro `query` di
`cerca_normativa`, che alimenta l'operatore MATCH di FTS5 (la cui sintassi interpreta virgolette,
asterisco, operatori `NEAR`/`AND`), è reso inoffensivo da `to_match_query`: estrae i soli token
alfanumerici e li cita come termini letterali, così un input non tecnico non può comporre una
espressione MATCH invalida né iniettare operatori. I tool degradano con grazia quando l'indice non
esiste, restituendo un messaggio diagnostico invece di sollevare eccezioni che risalirebbero al
client, e la freschezza in `info_corpus` è best-effort: se git o il submodule mancano, ripiega su
una fonte meno precisa senza fallire. Il package `update` esegue git come sottoprocesso solo sul
percorso del corpus configurato, con `pull --ff-only` per non riscrivere mai la storia.

Portabilità su Windows: il corpus italiano ha nomi di file molto lunghi, che sul filesystem
sforano il limite storico di 260 caratteri (MAX_PATH). Il prodotto lo aggira in modo trasparente,
senza chiedere all'utente privilegi di amministratore né modifiche al registro di sistema, su due
fronti. Lato git, l'estrazione dei file usa `core.longpaths=true` (impostato dal `setup.py` con
`-c` e persistito nel clone del corpus), che fa scrivere a git i path lunghi tramite le API estese.
Lato Python, `config.long_path` antepone il prefisso `\\?\` quando si apre o si interroga un file
del corpus, così `open` e `os.stat` superano lo stesso limite. È una scelta di design al servizio
della trasparenza per l'utente finale: il setup è un comando solo e funziona su una macchina
Windows non amministrata.

## Diagrammi

| Diagramma | Sorgente | Componenti rappresentati |
|---|---|---|
| (nessuno ancora) | | da produrre se la complessità lo giustifica |
