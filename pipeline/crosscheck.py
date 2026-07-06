"""
Cross-source consistency check -> Transparency Score. ARCHITECTURE.md §3.1.

Fully deterministic (no LLM) by design: this score must be defensible and reproducible on its
own, independent of any AI judgment call. See agent.md §3 — Justification and Transparency are
two different questions and must never be blended.
"""
from __future__ import annotations

from pipeline.schema import ConflictItem, SourceDocument, TransparencyBand

_TRACKED_FIELDS = [
    ("sanctioned_cr", "claimed_sanctioned_cr"),
    ("disbursed_cr", "claimed_disbursed_cr"),
    ("utilized_cr", "claimed_utilized_cr"),
]

# Below this relative delta, a disagreement is noise, not a reportable conflict.
_CONFLICT_ITEMIZE_THRESHOLD = 0.05  # 5%


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def compute_transparency(
    project_id: str, source_docs: list[SourceDocument]
) -> tuple[int | None, list[ConflictItem]]:
    """Returns (transparency_score, conflicts).

    transparency_score is None when fewer than 2 source documents exist for the project —
    absence of conflicting evidence is not the same as confirmed consistency
    (TransparencyBand.SINGLE_SOURCE), so callers must not treat None as a low score.
    """
    docs = [d for d in source_docs if d.project_id == project_id]
    if len(docs) < 2:
        return None, []

    rel_disagreements: list[float] = []
    conflicts: list[ConflictItem] = []

    for field_name, claimed_attr in _TRACKED_FIELDS:
        values = [(d, getattr(d, claimed_attr)) for d in docs if getattr(d, claimed_attr) is not None]
        if len(values) < 2:
            continue

        vals_only = [v for _, v in values]
        v_min, v_max = min(vals_only), max(vals_only)
        rel = (v_max - v_min) / max(v_min, 1.0)
        rel_disagreements.append(rel)

        if rel >= _CONFLICT_ITEMIZE_THRESHOLD:
            doc_min = min(values, key=lambda x: x[1])[0]
            doc_max = max(values, key=lambda x: x[1])[0]
            conflicts.append(
                ConflictItem(
                    field=field_name,
                    source_a=doc_min.title,
                    value_a=doc_min_val if (doc_min_val := getattr(doc_min, claimed_attr)) is not None else 0.0,
                    source_b=doc_max.title,
                    value_b=getattr(doc_max, claimed_attr),
                    delta_cr=round(v_max - v_min, 2),
                )
            )

    if not rel_disagreements:
        return None, []

    mean_disagreement = sum(rel_disagreements) / len(rel_disagreements)
    score = round(100 * (1 - _clamp(mean_disagreement, 0.0, 1.0)))
    return score, conflicts


def band_for(score: int | None) -> TransparencyBand:
    return TransparencyBand.from_score(score)
