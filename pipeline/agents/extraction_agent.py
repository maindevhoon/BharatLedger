"""Extraction Agent — normalizes raw extracted figures into clean SourceDocument fields.
ARCHITECTURE.md §4.1.

extract.py (PyMuPDF/Document AI) does the heavy lifting of finding candidate figures in a PDF.
This module owns the narrower "disambiguation and normalization" job ARCHITECTURE.md assigns
to the Extraction Agent: unit normalization (lakh vs crore), and flagging when no figure was
found for a required field so callers can decide how to handle it (skip vs. mark incomplete)
rather than silently treating None as zero.

Deterministic by design — normalization rules don't need an LLM call to get right, and keeping
this rule-based means extraction stays auditable and free to re-run at scale.
"""
from __future__ import annotations

_LAKH_TO_CRORE = 0.01  # 1 lakh = 0.01 crore


def normalize_to_crore(value: float, unit_hint: str) -> float:
    """unit_hint is whatever unit word was found near the figure in the source text
    ('crore', 'lakh', 'cr', 'lakhs') — case-insensitive."""
    unit = unit_hint.strip().lower()
    if unit in ("lakh", "lakhs"):
        return round(value * _LAKH_TO_CRORE, 4)
    return value  # already crore, or unit unspecified (assume crore — the dominant unit in
    # Union Budget / CAG reporting for project-scale figures)


def validate_figures(figures: dict[str, float | None]) -> list[str]:
    """Returns the list of expected fields that came back empty, so callers (batch_score.py,
    extract.py's demo) can surface an honest 'incomplete extraction' signal instead of quietly
    treating a missing figure as zero."""
    return [field for field, value in figures.items() if value is None]
