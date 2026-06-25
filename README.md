# Consulente Legale

Assistente legale locale per uso privato e aziendale, basato sul corpus della
legislazione italiana ([italia-corpus](https://github.com/ahmeabd/italia-corpus)).
Realizzato come **MCP server locale** interrogato da **Claude Desktop**.

- **Usa l'abbonamento Claude Team** — il ragionamento lo fa Claude Desktop chiamando i
  tool dell'MCP server. Nessun costo API pay-as-you-go.
- **Locale e privacy-first:** corpus, indice e ricerca interamente sulla tua macchina.
  Solo la conversazione (domanda + estratti restituiti) passa per Claude Desktop.
- **No GPU:** ricerca **BM25 / full-text** (SQLite FTS5). Indicizzazione veloce.
- **Sempre aggiornato:** il corpus si auto-aggiorna giornalmente (commit git); l'indice
  viene reindicizzato in modo incrementale.

> ⚠️ Strumento informativo, **non costituisce consulenza legale**. Per uso professionale
> fare sempre riferimento alla *Gazzetta Ufficiale*.

## Stato

Progetto in fase di avvio. Vedi **[HANDOFF.md](HANDOFF.md)** per architettura, stack,
decisioni tecniche e roadmap.

## Quick start (previsto)

```bash
git submodule update --init           # scarica italia-corpus
uv sync                               # dipendenze (include `mcp`)
python scripts/bootstrap_index.py     # prima indicizzazione FTS5
```

Poi registrare il server in `claude_desktop_config.json`:

```json
"legge-it": {
  "command": "uv",
  "args": ["--directory", "E:\\legal-consultant", "run", "python", "-m",
           "legal_consultant.mcp_server"]
}
```

e riavviare Claude Desktop. Creare infine un Project "Consulente Legale" con le istruzioni
descritte nell'handoff (§5.4).
