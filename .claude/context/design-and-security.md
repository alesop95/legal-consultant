---
generated-from-commit: 1e4c79b
generated-from-branch: main
generated-date: 2026-06-25
covers-paths:
  - src/legal_consultant/**
last-verified-commit: 6111cd3
---

# Design e sicurezza applicativa

> Aggiornato leggendo il codice di Fase 1 (ingest + indice) e Fase 2 (server MCP). Il confine di
> privacy di riferimento è in `HANDOFF.md`: corpus, indice e ricerca interamente locali; solo la
> conversazione (query + estratti) lascia la macchina via Claude Desktop.

## Paradigmi di software design

L'architettura è a strati con dipendenze a senso unico. In basso lo strato dati `index.fts`, che
conosce solo SQLite e FTS5 ed espone funzioni pure su una connessione (`search`, `get_act`,
`corpus_stats`, `insert_act`); sopra di esso lo strato di ingest (`ingest.parser`), che trasforma
un file `.md` in `ParsedAct`; in cima il server `mcp_server`, strato di presentazione che fa
wiring dei tre tool MCP sopra lo strato dati e formatta l'output con helper puri (`_hit_to_dict`,
`_citazione`). Il server non contiene logica di ricerca: la delega interamente a `index.fts`. La
scelta tiene i tool verificabili sull'indice di fixture senza avviare il transport MCP, e isola il
cambiamento del protocollo dal cambiamento della ricerca. La configurazione dei percorsi è
centralizzata in `config.py`, unico punto che legge ambiente e `.env`. Il contratto tra moduli
passa per le dataclass di `parser` (`Act`, `Chunk`, `ParsedAct`) e per le `sqlite3.Row` dello
strato dati, mai per strutture implicite.

## Sicurezza applicativa

Il confine di privacy è netto: corpus, indice e ricerca sono on-disk; il server gira come
sottoprocesso locale su stdio, senza alcuna superficie di rete. Solo la conversazione (la query e
gli estratti restituiti dai tool) lascia la macchina, e solo attraverso Claude Desktop. Il prodotto
non usa chiavi API e non gestisce segreti applicativi: `config.py` legge soltanto percorsi, mai
credenziali, e i valori di `.env` non si committano. La superficie esposta è l'insieme degli input
dei tre tool. Gli accessi al database sono tutti per query parametrizzate (binding `?`), quindi gli
identificatori e i filtri passati ai tool non aprono a SQL injection. Resta un punto aperto: il
parametro `query` di `cerca_normativa` viene passato all'operatore MATCH di FTS5, la cui sintassi
interpreta alcuni caratteri (virgolette, asterisco, operatori `NEAR`/`AND`); un input malformato
può sollevare un errore SQL anziché essere trattato come testo. Non è un rischio di sicurezza ma di
robustezza, ed è tracciato tra le domande aperte di `current-work.md`. I tool degradano con grazia
quando l'indice non esiste, restituendo un messaggio diagnostico invece di sollevare eccezioni che
risalirebbero al client.

## Diagrammi

| Diagramma | Sorgente | Componenti rappresentati |
|---|---|---|
| (nessuno ancora) | | da produrre se la complessità lo giustifica |
