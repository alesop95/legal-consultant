# Registro delle decisioni architetturali

> Convenzione ADR-lite, append-only. Ogni decisione architetturale non ovvia entra come voce
> numerata con data, stato, contesto, decisione, motivazione e conseguenze. Una decisione non si
> cancella e non si riscrive: quando viene superata, si aggiunge una nuova voce che dichiara di
> superare la precedente e ne cita il numero. Le inferenze non confermate si marcano come da
> verificare e si promuovono a decisione solo quando una fonte le conferma.

## ADR-001 — Adozione del sistema di progetto portabile

Data: 2026-06-25
Stato: accettata
Contesto: il progetto necessita di uno stato interamente recuperabile da un clone e di
documentazione che resti allineata al codice senza rilettura integrale a ogni sessione.
Decisione: adottare il sistema descritto in `.claude/PROJECT-SYSTEM.md`, con motore di
riconciliazione ancorato ai commit e doppio livello documentale tracciato/ignorato.
Motivazione: persistenza strutturale su disco indipendente dalla sessione di chat, e controllo
umano sul versionamento.
Conseguenze: ogni passo significativo aggiorna schede, `last-verified-commit`, snapshot e
work-log; commit e push restano manuali.

## ADR-002 — Server MCP locale + Claude Desktop invece di app con API

Data: 2026-06-25
Stato: accettata
Contesto: l'abbonamento Claude Team e l'API Anthropic sono prodotti separati e fatturati a
parte; il Team plan non include crediti API. L'utente vuole evitare il consumo di token
pay-as-you-go e dispone già di Claude Desktop con server MCP configurati.
Decisione: realizzare il consulente come server MCP locale in Python ("legge-it") che espone
strumenti di ricerca normativa, consumato da Claude Desktop. Il ragionamento lo fa Claude
Desktop tramite l'abbonamento. La citazione e il disclaimer si governano via descrizioni dei
tool e via un Project dedicato in Claude Desktop.
Motivazione: nessun costo API, riuso del setup MCP esistente, UI già pronta, stesso confine di
privacy (solo la conversazione lascia la macchina).
Conseguenze: niente UI né integrazione API custom; soggezione ai limiti d'uso del piano Team;
minore controllo sul prompt di sistema (compensato dalle istruzioni del Project). Da validare in
Fase 2 che il piano Team consenta server MCP locali senza restrizioni amministrative.

## ADR-003 — Retrieval BM25 (SQLite FTS5) senza embedding né GPU per l'MVP

Data: 2026-06-25
Stato: accettata
Contesto: GPU non disponibile; il corpus è grande (>280k atti, milioni di chunk per articolo);
gli embedding di qualità (BGE-M3) sono pesanti su CPU alla prima indicizzazione.
Decisione: per l'MVP usare retrieval lessicale BM25 su SQLite FTS5, con chunking per articolo e
metadati per la citazione. Rimandare l'embedding semantico leggero CPU (es. multilingual-e5-small
in ONNX) a una fase successiva per una ricerca ibrida, solo se il recall lessicale risulta
insufficiente.
Motivazione: indicizzazione veloce senza GPU; il match lessicale esatto è forte nel diritto
(numeri di articolo, nomi di leggi, termini tecnici).
Conseguenze: recall semantico limitato all'inizio; la ricerca ibrida resta in backlog.

## ADR-004 — Corpus via git submodule self-updating, solo diritto italiano

Data: 2026-06-25
Stato: accettata
Contesto: `italia-corpus` si auto-aggiorna giornalmente, con un commit per ogni modifica
normativa; copre la sola legislazione italiana.
Decisione: integrare il corpus come git submodule sotto `data/`, aggiornarlo con `git pull`
schedulato (Windows Task Scheduler) e reindicizzare in modo incrementale via `git diff` tra il
commit indicizzato e quello nuovo. Ambito limitato al diritto italiano; il diritto UE (EUR-Lex)
resta in backlog.
Motivazione: nessuno scraper da costruire; aggiornamento incrementale economico; ambito ridotto
che semplifica l'MVP.
Conseguenze: copertura aggiornata fino all'ultimo pull (per le ultimissime novità si valuta il
web search di Claude Desktop, opzionale); estensione UE rinviata.
