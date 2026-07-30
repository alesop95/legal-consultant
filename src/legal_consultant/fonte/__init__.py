"""Accesso alle fonti normative ufficiali per colmare le lacune del corpus.

Il corpus principale `italia-corpus` rispecchia il catalogo delle collezioni
preconfezionate di Normattiva, che non comprende la legge ordinaria, il
decreto-legge vigente e la Costituzione (vedi `docs/audit-completezza-corpus.md`).
Questo package parla direttamente con l'API Open Data di Normattiva per recuperare
quelle classi, e converte l'export Akoma Ntoso nello stesso Markdown con
frontmatter che il resto della pipeline già sa leggere.
"""

from . import akn, normattiva

__all__ = ["akn", "normattiva"]
