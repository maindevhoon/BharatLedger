"""
Generates the synthetic dataset Bharat Ledger runs on for the hackathon prototype
(PLAN.md Phase 1). Produces, under data/synthetic/:

  - benchmarks.csv          — cost-per-unit yardsticks (pipeline/benchmarks_data.py)
  - projects.csv            — one row per (state, sector, year) project
  - source_documents.csv    — 1-3 source docs per project; ~18% of projects get
                              deliberately conflicting figures across sources, to
                              exercise the Transparency Score (crosscheck.py)
  - district_flat_large.parquet
                            — the large (multi-million row) district-level expansion
                              of `projects`, used ONLY to feed the NVIDIA cudf.pandas
                              acceleration benchmark (Phase 4). Not used by the app
                              at serve time.

Deterministic: a fixed random seed means re-running produces the same dataset, so the
BigQuery loader / SQLite build / seed data cross-references stay stable.

Run: python3 -m pipeline.generate_synthetic
"""
from __future__ import annotations

import random

import numpy as np
import pandas as pd

from pipeline.benchmarks_data import INDIA_STATES, TERRAIN_MULTIPLIER, build_benchmarks
from pipeline.config import config
from pipeline.schema import Project, Sector, SourceDocument, SourceType, ExtractionMethod

SEED = 20260706  # date-stamped, arbitrary but fixed for reproducibility
YEARS = list(range(2016, 2025))  # FY2016-17 .. FY2024-25 (fiscal year start)

# rough relative scale of a "typical" project's total outcome quantity per sector,
# so amounts and outcome values land in believable ranges (e.g. tens of km, not 0.2 km)
_OUTCOME_SCALE = {
    Sector.ROADS: (15, 120),       # km
    Sector.EDUCATION: (5, 60),     # schools
    Sector.HEALTH: (50, 400),      # beds
    Sector.WATER: (20, 150),       # MLD
    Sector.ENERGY: (30, 300),      # MW
}

_SLUG_SECTOR = {
    Sector.ROADS: "roads", Sector.EDUCATION: "edu", Sector.HEALTH: "health",
    Sector.WATER: "water", Sector.ENERGY: "energy",
}

_DESCRIPTIONS = {
    "plain": "Flat terrain, standard construction conditions.",
    "coastal": "Coastal terrain with saline-resistant construction requirements.",
    "hilly": "Hilly/mountainous terrain requiring tunneling, retaining walls, and slope stabilization.",
    "urban": "Dense urban corridor with significant land acquisition and elevated/underground sections.",
}


def _slugify(state: str) -> str:
    return state.lower().replace(" ", "-")


def _state_code(state: str) -> str:
    parts = state.split()
    if len(parts) == 1:
        return state[:2].lower()
    return "".join(p[0] for p in parts).lower()


def generate_projects(rng: random.Random) -> tuple[list[Project], dict[str, str]]:
    """Returns (projects, project_id -> terrain) — terrain kept alongside for benchmark lookup."""
    projects: list[Project] = []
    terrain_by_id: dict[str, str] = {}
    benchmarks = {(b.sector, b.terrain): b for b in build_benchmarks()}

    for state, terrain in INDIA_STATES.items():
        for sector in Sector:
            for year in YEARS:
                # not every state/sector/year combo has a project — thin it out a bit
                if rng.random() < 0.35:
                    continue

                bench = benchmarks[(sector, terrain)]
                lo, hi = _OUTCOME_SCALE[sector]
                outcome_value = round(rng.uniform(lo, hi), 1)

                # cost-per-unit noise around the benchmark median; occasionally an outlier
                roll = rng.random()
                if roll < 0.12:
                    # deliberate high-cost outlier -> "needs_review" territory
                    cost_per_unit = bench.median_cost_per_unit_cr * rng.uniform(1.8, 3.2)
                elif roll < 0.20:
                    # deliberate efficient outlier -> "well_justified" territory
                    cost_per_unit = bench.median_cost_per_unit_cr * rng.uniform(0.55, 0.85)
                else:
                    cost_per_unit = rng.uniform(bench.p25_cost_per_unit_cr, bench.p75_cost_per_unit_cr)

                utilized_cr = round(cost_per_unit * outcome_value, 2)
                # sanctioned is usually a bit above utilized; disbursed sits between
                sanctioned_cr = round(utilized_cr * rng.uniform(1.02, 1.22), 2)
                disbursed_cr = round(utilized_cr * rng.uniform(0.98, 1.08), 2)

                project_id = (
                    f"in-{_state_code(state)}-{_SLUG_SECTOR[sector]}-{_slugify(state)}-"
                    f"{sector.value}-{year}"
                )
                name = f"{state} {sector.value.capitalize()} Programme FY{year}-{str(year+1)[-2:]}"

                project = Project(
                    project_id=project_id,
                    country="IN",
                    state=state,
                    sector=sector,
                    name=name,
                    year=year,
                    sanctioned_cr=sanctioned_cr,
                    disbursed_cr=disbursed_cr,
                    utilized_cr=utilized_cr,
                    outcome_value=outcome_value,
                    outcome_unit=bench.outcome_unit,
                    description=_DESCRIPTIONS[terrain],
                )
                projects.append(project)
                terrain_by_id[project_id] = terrain

    return projects, terrain_by_id


def generate_source_documents(projects: list[Project], rng: random.Random) -> list[SourceDocument]:
    """1-3 source docs per project; ~18% of projects get deliberately conflicting figures
    across their sources (this is the raw material crosscheck.py turns into the
    Transparency Score — see ARCHITECTURE.md §3.1)."""
    docs: list[SourceDocument] = []

    for project in projects:
        n_sources = rng.choice([1, 2, 2, 3])  # weighted towards 2
        make_conflict = rng.random() < 0.18 and n_sources >= 2

        source_types = rng.sample(
            [SourceType.UNION_BUDGET, SourceType.STATE_BUDGET, SourceType.CAG_REPORT], k=min(n_sources, 3)
        )

        base_sanctioned = project.sanctioned_cr
        base_disbursed = project.disbursed_cr
        base_utilized = project.utilized_cr

        for i, source_type in enumerate(source_types):
            if make_conflict and i == len(source_types) - 1:
                # last source deliberately disagrees on utilized (and sometimes sanctioned)
                drift = rng.uniform(0.12, 0.35) * rng.choice([-1, 1])
                claimed_utilized = round(base_utilized * (1 + drift), 2)
                claimed_sanctioned = round(
                    base_sanctioned * (1 + drift * rng.uniform(0.3, 0.8)), 2
                )
                claimed_disbursed = round(base_disbursed * (1 + drift * rng.uniform(0.3, 0.8)), 2)
            else:
                # small natural noise even for "agreeing" sources
                noise = lambda v: round(v * rng.uniform(0.985, 1.015), 2)
                claimed_sanctioned = noise(base_sanctioned)
                claimed_disbursed = noise(base_disbursed)
                claimed_utilized = noise(base_utilized)

            docs.append(
                SourceDocument(
                    doc_id=f"{project.project_id}-doc{i+1}",
                    project_id=project.project_id,
                    source_type=source_type,
                    title=f"{source_type.value.replace('_', ' ').title()} — {project.name}",
                    url_or_path=f"synthetic://{source_type.value}/{project.project_id}",
                    claimed_sanctioned_cr=claimed_sanctioned,
                    claimed_disbursed_cr=claimed_disbursed,
                    claimed_utilized_cr=claimed_utilized,
                    extraction_method=ExtractionMethod.MANUAL,
                )
            )

    return docs


def generate_large_district_table(projects: list[Project], terrain_by_id: dict[str, str],
                                    rng: random.Random, target_rows: int = 6_000_000) -> pd.DataFrame:
    """Expands each project into many synthetic district-level sub-rows, purely to give the
    NVIDIA cudf.pandas benchmark (Phase 4) a genuinely large table to aggregate. This table is
    NOT read by the API at serve time — only by acceleration/cudf_benchmark.ipynb, which then
    writes back a small `rankings` table that the API *does* serve.
    """
    n_projects = len(projects)
    rows_per_project = max(1, target_rows // n_projects)

    # vectorized generation for speed: build per-project arrays, then concat
    frames = []
    for project in projects:
        terrain = terrain_by_id[project.project_id]
        n = rows_per_project
        cost_noise = rng.gauss(1.0, 0.08)
        costs = np.random.default_rng(abs(hash(project.project_id)) % (2**32)).normal(
            loc=project.cost_per_unit_cr * cost_noise, scale=project.cost_per_unit_cr * 0.05, size=n
        )
        frames.append(pd.DataFrame({
            "country": "IN",
            "state": project.state,
            "sector": project.sector.value,
            "year": project.year,
            "terrain": terrain,
            "district_seq": np.arange(n),
            "cost_per_unit_cr": np.clip(costs, a_min=0.01, a_max=None),
        }))

    return pd.concat(frames, ignore_index=True)


def main() -> None:
    rng = random.Random(SEED)
    np.random.seed(SEED)

    config.synthetic_dir.mkdir(parents=True, exist_ok=True)

    print("Generating benchmarks...")
    benchmarks = build_benchmarks()
    pd.DataFrame([b.model_dump() for b in benchmarks]).to_csv(
        config.synthetic_dir / "benchmarks.csv", index=False
    )
    print(f"  -> {len(benchmarks)} benchmark rows")

    print("Generating projects...")
    projects, terrain_by_id = generate_projects(rng)
    projects_df = pd.DataFrame([p.model_dump() for p in projects])
    projects_df.to_csv(config.synthetic_dir / "projects.csv", index=False)
    print(f"  -> {len(projects)} project rows")

    print("Generating source documents (with ~18% intentional cross-source conflicts)...")
    docs = generate_source_documents(projects, rng)
    docs_df = pd.DataFrame([d.model_dump() for d in docs])
    docs_df.to_csv(config.synthetic_dir / "source_documents.csv", index=False)
    print(f"  -> {len(docs)} source document rows")

    print("Generating large district-level flat table for the cudf.pandas benchmark "
          "(this may take a minute)...")
    large_df = generate_large_district_table(projects, terrain_by_id, rng)
    large_path = config.synthetic_dir / "district_flat_large.parquet"
    large_df.to_parquet(large_path, index=False)
    print(f"  -> {len(large_df):,} rows -> {large_path} ({large_path.stat().st_size / 1e6:.1f} MB)")

    print("\nDone. Files written to", config.synthetic_dir)


if __name__ == "__main__":
    main()
