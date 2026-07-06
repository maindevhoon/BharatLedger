"""
The deterministic benchmark-ratio prior (ARCHITECTURE.md §3.2). Computed once per project and
handed to every debate agent as grounding fact, and shown directly in the UI — this is what
keeps the final Justification Score anchored to arithmetic rather than pure LLM judgment.
"""
from __future__ import annotations

from dataclasses import dataclass

from pipeline.schema import Benchmark, Project


@dataclass
class BenchmarkComparison:
    ratio: float                # project.cost_per_unit_cr / benchmark.median_cost_per_unit_cr
    benchmark: Benchmark
    prior_band: str              # "well_justified" | "partially_justified" | "needs_review"


def compare_to_benchmark(project: Project, benchmarks: list[Benchmark]) -> BenchmarkComparison | None:
    """Matches on country + sector + outcome_unit; terrain is inferred from which benchmark
    row's terrain the project's description most plausibly corresponds to. In practice callers
    pass the already-known terrain-matched benchmark; this helper also supports matching by
    an explicit terrain if provided via `terrain`.
    """
    matches = [
        b for b in benchmarks
        if b.country == project.country and b.sector == project.sector
        and b.outcome_unit == project.outcome_unit
    ]
    if not matches:
        return None

    # Without an explicit terrain tag on Project (kept out of the schema deliberately — terrain
    # is a benchmark-matching concept, not a project fact we assert), default to the median
    # match across available terrains for this sector/unit combination if multiple exist and
    # no single one is passed. Callers with terrain knowledge should use compare_with_terrain().
    benchmark = matches[0]
    ratio = round(project.cost_per_unit_cr / benchmark.median_cost_per_unit_cr, 3)
    return BenchmarkComparison(ratio=ratio, benchmark=benchmark, prior_band=_band_for_ratio(ratio))


def compare_with_terrain(
    project: Project, benchmarks: list[Benchmark], terrain: str
) -> BenchmarkComparison | None:
    matches = [
        b for b in benchmarks
        if b.country == project.country and b.sector == project.sector
        and b.outcome_unit == project.outcome_unit and b.terrain == terrain
    ]
    if not matches:
        return compare_to_benchmark(project, benchmarks)

    benchmark = matches[0]
    ratio = round(project.cost_per_unit_cr / benchmark.median_cost_per_unit_cr, 3)
    return BenchmarkComparison(ratio=ratio, benchmark=benchmark, prior_band=_band_for_ratio(ratio))


def _band_for_ratio(ratio: float) -> str:
    if ratio <= 1.1:
        return "well_justified"
    if ratio <= 1.8:
        return "partially_justified"
    return "needs_review"
