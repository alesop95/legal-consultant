"""Ingestione del corpus: parsing del Markdown + frontmatter YAML e chunking per articolo."""

from .parser import Act, Chunk, ParsedAct, parse_act

__all__ = ["Act", "Chunk", "ParsedAct", "parse_act"]
