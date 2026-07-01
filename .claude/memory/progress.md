# Work-log

> Append-only, in ordine cronologico inverso (la voce più recente in alto). Ogni passo
> significativo di codice e ogni intervento manuale rilevante lascia una voce con data, file
> toccati, motivo e commit di riferimento. Qui confluisce anche il log di riconciliazione dei
> documenti `.docx`, con il nome del documento sorgente e l'esito, così la data di allineamento
> sopravvive a un clone.

## 2026-06-30 — Integrazione codici fondamentali da Normattiva (civile, penale, ecc.)

Commit: (non ancora committato)
File toccati: `src/legal_consultant/ingest/parser.py` (regex articolo estesa: cattura rubrica
anche tra parentesi `### Art. N. (Rubrica)` oltre che col trattino, retro-compatibile);
`src/legal_consultant/config.py` (+ `EXTRA_CORPUS_PATH`); `scripts/fetch_codici.py` (nuovo);
`scripts/bootstrap_index.py` (indicizza anche la collezione supplementare); `tests/test_pipeline.py`
(+ caso rubrica tra parentesi); `data/codici-extra/Codici/*.md` (5 codici scaricati, ~5.2 MB).
Aggiornate le schede pertinenti e `memory/index.md`.
Motivo: chiusura della lacuna emersa dal test in Claude Desktop. I vecchi codici emanati con Regio
Decreto (civile, penale, procedura civile, navigazione, penali militari) in italia-corpus c'erano
solo come decreto di approvazione, senza articolato. PoC su `normattiva2md` (onData, MIT) validato:
il codice civile scaricato da Normattiva (pubblico dominio) ha 3282 articoli, ma con rubrica tra
parentesi che il regex non catturava (352/3282 → 3282/3282 dopo l'estensione). Scritto
`fetch_codici.py` che scarica i 5 codici da Normattiva via `uvx normattiva2md`, ne riscrive il
frontmatter nello schema del progetto e li salva in `data/codici-extra` (tracciato, fuori dal
submodule). Re-index dell'intero corpus + supplemento: 287.816 atti, 966.126 chunk, 306s. Verifica
end-to-end: art. 2043 c.c., art. 157 c.p., art. 112 c.p.c. ora presenti e ricercabili dal nostro
indice; `cerca_normativa("risarcimento del danno per fatto illecito")` → art. 2043 c.c. `uv run
pytest` → 10 verdi. Aggiornamento del supplemento: rilanciare `fetch_codici.py` + reindex.

## 2026-06-30 — Corpus reale indicizzato end-to-end + percorsi lunghi Windows + fix vigenti/dedup

Commit: (codice non ancora committato; indice e corpus sono fuori da git)
File toccati: `src/legal_consultant/config.py` (+ `long_path`); `src/legal_consultant/ingest/parser.py`
(open via `long_path`; `vigente` declassato a False per la collezione delle abrogate);
`src/legal_consultant/index/fts.py` (+ `dedup` per (urn, articolo) in `search`);
`src/legal_consultant/update/__init__.py` (`is_file` via `long_path`); `scripts/setup.py`
(`core.longpaths` automatico); schede `STACK.md`, `deployment.md`, `design-and-security.md`.
Motivo: portato il sistema su tutto il corpus reale, end-to-end, su Windows. Limite MAX_PATH (260
char) aggirato in modo trasparente, senza admin: git estrae con `core.longpaths`, Python apre con
prefisso `\\?\` via `config.long_path` (verificato leggendo un atto con path da 276 char). Riusati i
330 MB gia' scaricati: `git -C data/italia-corpus reset --hard` ha completato l'estrazione (287.813
file). `bootstrap_index.py` sull'intero corpus: 287.811 atti, 759.881 chunk, 23 errori (caratteri di
controllo, loggati), 744s, indice 2.4 GB. Due problemi di qualita' emersi dal test reale e corretti:
nel corpus il campo `vigente` e' True anche per le abrogate, quindi si declassa l'intera collezione
"Atti normativi abrogati (in originale)" (123.828 atti esclusi dai vigenti, restano 163.957);
deduplica per atto+articolo perche' il corpus archivia alcuni atti in piu' collezioni. `uv run
pytest` → 9 verdi; smoke dei tool MCP sull'indice reale corretto (es. "licenziamento per giusta
causa" → D.Lgs. 23/2015 art. 3). Limite noto: "vigente" qui significa "non nella collezione delle
abrogate", non "in vigore oggi" su Normattiva; ranking BM25 su query concettuali variabile (ADR-003).

## 2026-06-30 — Hardening, Fase 3, packaging trasparente e disclaimer (su fixture)

Commit: bd19b1d
File toccati: `src/legal_consultant/index/fts.py` (+ `to_match_query`, `search` con `sanitize`);
`src/legal_consultant/update/__init__.py` (nuovo: `corpus_revision`, `pull`, `changed_files`,
`reindex_paths`, `read_state`/`write_state`); `src/legal_consultant/mcp_server.py` (`info_corpus`
con freschezza + disclaimer; prompt MCP `consulenza_legale`); `scripts/update_corpus.py` (nuovo);
`scripts/setup.py` (nuovo); `.mcp.json` (nuovo, registrazione Claude Code); `prompts/consulente-legale.md`
(nuovo); `tests/test_pipeline.py` (+4 test). Aggiornate le schede `STACK.md`, `current-work.md`,
`deployment.md`, `design-and-security.md`, `dev-testing.md`, `roadmap.md` e `memory/index.md`.
Motivo: completato lo sviluppo del prodotto su decisione dell'utente (target Claude Code +
Desktop; scope: hardening, packaging, Fase 3, disclaimer). Hardening: la ricerca sanifica l'input
libero in una query MATCH sempre valida. Fase 3: aggiornamento incrementale del corpus via git
diff + reindex per path, con stato persistito letto da `info_corpus`. Packaging: registrazione
versionata in `.mcp.json`, setup a un comando, istruzioni e disclaimer esposti anche come prompt
MCP. `uv run pytest` → 9 test verdi; smoke di tool e prompt su fixture ok; avvio stdio pulito.
Corpus ancora non clonato: verifica end-to-end e casi d'uso rinviati al bootstrap reale.

## 2026-06-30 — Fase 2: server MCP "legge-it" (su fixture)

Commit: f954aaa
File toccati: `src/legal_consultant/mcp_server.py` (nuovo); `src/legal_consultant/index/fts.py`
(+ `get_act`, + `corpus_stats`; `search` ora include `vigente` nel SELECT); `pyproject.toml`
(+ dipendenza `mcp>=1.2`); `uv.lock`; `tests/test_pipeline.py` (+ test `get_act` e `corpus_stats`).
Aggiornate e ri-ancorate a `6111cd3` le schede `STACK.md`, `current-work.md`, `deployment.md`,
`design-and-security.md`, `dev-testing.md`, `roadmap.md`; aggiornati `memory/index.md` e questo
work-log.
Motivo: implementata la Fase 2. Server `FastMCP("legge-it")` su transport stdio con tre tool —
`cerca_normativa` (sopra `fts.search`), `leggi_atto` (sopra `fts.get_act`), `info_corpus` (sopra
`fts.corpus_stats`) — con descrizioni orientate alla citazione e degrado con grazia se l'indice
manca. Logica dati in `index.fts`, server sottile con helper puri di formattazione. `uv sync
--extra dev` ok; `uv run pytest` → 5 test verdi; smoke dei tre tool su indice di fixture corretto;
avvio `python -m legal_consultant.mcp_server` su stdio pulito. Corpus ancora non clonato e server
non ancora registrato in Claude Desktop.

## 2026-06-25 — Fase 1: pipeline ingest + indice FTS5 (su fixture)

Commit: 6111cd3
File toccati: `pyproject.toml`; `src/legal_consultant/` (`__init__`, `config.py`, `ingest/parser.py`,
`index/fts.py` + `__init__`); `scripts/bootstrap_index.py`; `tests/test_pipeline.py` e
`tests/fixtures/Codici/` (2 atti reali). Aggiornate le schede `STACK.md` e `current-work.md`.
Motivo: implementato il nucleo della Fase 1. Ispezionato lo schema reale del frontmatter YAML via
API GitHub (`tipo/numero/data/titolo/urn/codice_redazionale/vigente`) e la struttura del corpo
(articoli `## Art. N.` con rubrica, commi, preambolo). Scritto il parser (chunking per articolo) e
l'indice SQLite FTS5 (BM25, tokenizer `unicode61 remove_diacritics 2`, filtro vigenti). `uv sync`
ok; `uv run pytest` → 3 test verdi (parser + ricerca BM25 su atti reali). Corpus NON ancora
clonato (clone shallow del submodule rimandato per dimensione: ~831 MB lato git + storia
giornaliera). Esito: pipeline validata su fixture, pronta per il bootstrap sul corpus reale.

## 2026-06-25 — Primo ancoraggio delle schede al commit iniziale

Commit: 1e4c79b
File toccati: tutte le schede di `context/` (STACK, design-and-security, deployment, dev-testing,
current-work, roadmap) e `memory/index.md`.
Motivo: eseguita la skill `sync-context` (Passo 0) dopo il primo commit. Sostituito il segnaposto
`PENDING-FIRST-COMMIT` con l'hash di HEAD (`1e4c79b`) in `generated-from-commit` e
`last-verified-commit` di ogni scheda, e nel commit di riferimento dello snapshot. Da qui il
drift futuro si misura normalmente rispetto a HEAD.

## 2026-06-25 — Inizializzazione del sistema di progetto

Commit: 1e4c79b
File toccati: anatomia di `.claude` (PROJECT-SYSTEM.md, rules/, skills/, templates/ importati dal
bundle; settings.json, memory/, context/ istanziati), `CLAUDE.md`, `CLAUDE.local.md`,
`.gitignore` (merge dello snippet). git inizializzato (branch `main`), identità locale
github-personal (alesop95), remoto `git@github-personal:alesop95/legal-consultant.git` (verificato
vuoto via ls-remote). Schede strutturali create con solo frontmatter; `roadmap.md`,
`current-work.md` e `decisions.md` seminate con le decisioni confermate.
Motivo: installazione del sistema portabile di contesto, documentazione e version control
descritto in `.claude/PROJECT-SYSTEM.md`. Auto-memory nativa lasciata disattivata
(`autoMemoryEnabled: false`). MCP di sviluppo (code-context) rimandato.

## 2026-06-25 — Handoff iniziale e scelte di architettura (pre-sistema)

Commit: 1e4c79b
File toccati: `HANDOFF.md`, `README.md`, `.env.example`.
Motivo: ricerca su italia-corpus e strumenti, e definizione dell'architettura confermata con
l'utente (vedi ADR-002/003/004): server MCP locale + Claude Desktop, retrieval BM25 senza GPU,
corpus solo italiano via submodule self-updating.
