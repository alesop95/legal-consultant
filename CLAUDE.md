# legal-consultant

> Istruzioni di team, versionate. Questo file è l'indice del progetto: indicizza i soli file
> satellite tracciati e descrive la procedura di ripresa. Le preferenze personali vivono in
> `CLAUDE.local.md`, ignorato da git, non qui.

## Cos'è questo progetto

Consulente legale locale per uso privato e aziendale, basato sul corpus della legislazione
italiana ([italia-corpus](https://github.com/ahmeabd/italia-corpus)). È realizzato come **server
MCP locale in Python** ("legge-it") interrogato da **Claude Desktop**: la ricerca normativa
(BM25 / SQLite FTS5, interamente locale, senza GPU) gira sulla macchina; il ragionamento e la
chat li fa Claude Desktop tramite l'abbonamento Team, quindi senza consumare token API. Solo la
conversazione (domanda + estratti restituiti dai tool) lascia la macchina. Il design completo,
con architettura, decisioni e roadmap, è in `HANDOFF.md` (tracciato, in radice).

## Contesto operativo

```
OS sviluppo:    Windows
Identità git:   github-personal (alesop95/ alessio.sopranzi.95@gmail.com), impostata locale
Remoto:         git@github-personal:alesop95/legal-consultant.git (vuoto al primo commit)
```

## Procedura di ripresa in una sessione nuova

Lo stato del progetto è interamente recuperabile su disco. All'inizio di una sessione si segue
questo percorso fisso. Si legge per primo `.claude/memory/index.md`, che dà branch, commit di
riferimento, stato di verifica di ogni scheda e punto di ripresa. Si legge poi
`.claude/context/current-work.md` se c'è una feature attiva, per sapere cosa è in lavorazione e
quali sono i TODO e i limiti d'ambiente. Si invoca la skill `sync-context` per verificare il
drift tra schede e codice, e si leggono solo le schede pertinenti al task, mai tutte insieme. Il
work-log `.claude/memory/progress.md` e il registro `.claude/memory/decisions.md` forniscono la
storia e le decisioni quando servono. Il materiale grezzo sotto `_notes/` si apre solo per
verificare un requisito originale. Per una ripresa rapida esiste, quando presente,
`_notes/RESUME-PROMPT.md`, privato e ignorato: riporta lo stato raggiunto e un prompt pronto da
incollare. Va aggiornato alla fine di ogni sessione con il punto in cui si è arrivati, mentre lo
stato canonico resta `.claude/memory/index.md`.

## Indice dei file satellite tracciati

Documento di progetto, in radice.

```
HANDOFF.md   architettura, stack, decisioni tecniche e roadmap (design di riferimento)
README.md    descrizione pubblica per GitHub
```

Memoria e meta-stato, sotto `.claude/memory/`, letti sempre a inizio sessione.

```
.claude/memory/index.md       snapshot e tabella di sincronizzazione, da leggere per primo
.claude/memory/progress.md    work-log append-only di passi e riconciliazioni
.claude/memory/decisions.md   registro ADR-lite delle decisioni architetturali
```

Schede tecniche, sotto `.claude/context/`, con frontmatter di riconciliazione.

```
.claude/context/STACK.md                stack, flussi di codice, ruolo architetturale dei file
.claude/context/design-and-security.md  paradigmi di design e sicurezza applicativa
.claude/context/deployment.md           livelli test e produzione, hosting, comandi
.claude/context/dev-testing.md          test di sviluppo, runner, rotte mockate, hook
.claude/context/current-work.md         feature attiva, definition of done, domande aperte
.claude/context/roadmap.md              direzione e priorità
```

Regole modulari caricate su necessità, sotto `.claude/rules/`, e skill richiamabili, sotto
`.claude/skills/`. Lo standard di sistema completo è in `.claude/PROJECT-SYSTEM.md`.

## Vincoli di team

Le operazioni di `git add`, commit e push restano sempre manuali dell'utente: l'agente prepara i
file, non committa. L'identità git è impostata a livello locale del repo secondo
`.claude/rules/git-identity-and-repo.md`. Lo stile di documentazione e di interazione è quello di
`.claude/rules/interaction-style.md`. Claude non scrive autonomamente nei file di memoria e di
contesto: li aggiorna solo su richiesta esplicita, così il versionamento resta sotto controllo
umano.
