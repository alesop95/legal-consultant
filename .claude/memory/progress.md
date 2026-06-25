# Work-log

> Append-only, in ordine cronologico inverso (la voce più recente in alto). Ogni passo
> significativo di codice e ogni intervento manuale rilevante lascia una voce con data, file
> toccati, motivo e commit di riferimento. Qui confluisce anche il log di riconciliazione dei
> documenti `.docx`, con il nome del documento sorgente e l'esito, così la data di allineamento
> sopravvive a un clone.

## 2026-06-25 — Inizializzazione del sistema di progetto

Commit: PENDING-FIRST-COMMIT
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

Commit: PENDING-FIRST-COMMIT
File toccati: `HANDOFF.md`, `README.md`, `.env.example`.
Motivo: ricerca su italia-corpus e strumenti, e definizione dell'architettura confermata con
l'utente (vedi ADR-002/003/004): server MCP locale + Claude Desktop, retrieval BM25 senza GPU,
corpus solo italiano via submodule self-updating.
