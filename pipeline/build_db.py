"""
Builds the local SQLite mirror (PLAN.md Phase 1 deliverable: "SQLite built and populated").

This is the store the demo actually runs on by default (USE_BIGQUERY=false). It combines:
  - data/synthetic/{projects,source_documents,benchmarks}.csv  (generate_synthetic.py)
  - data/seed/seed_projects.json                                (generate_seed.py — takes
    precedence: these are the hand-curated flagship projects with full verdicts/transcripts)
  - a CPU-pandas fallback `rankings` table, so Phase 5/6 work immediately without waiting on
    the Colab cudf notebook (Phase 4 later produces the authoritative version of this table
    and this script can re-import it — see import_rankings_csv()).

Schema mirrors pipeline/schema.py exactly (ARCHITECTURE.md §2) — one schema, two stores.

Run: python3 -m pipeline.build_db
"""
from __future__ import annotations

import json
import sqlite3

import pandas as pd

from pipeline.config import config

_DDL = """
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    country TEXT NOT NULL,
    state TEXT NOT NULL,
    sector TEXT NOT NULL,
    name TEXT NOT NULL,
    year INTEGER NOT NULL,
    sanctioned_cr REAL NOT NULL,
    disbursed_cr REAL NOT NULL,
    utilized_cr REAL NOT NULL,
    outcome_value REAL NOT NULL,
    outcome_unit TEXT NOT NULL,
    cost_per_unit_cr REAL NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS source_documents (
    doc_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    source_type TEXT NOT NULL,
    title TEXT NOT NULL,
    url_or_path TEXT,
    claimed_sanctioned_cr REAL,
    claimed_disbursed_cr REAL,
    claimed_utilized_cr REAL,
    extracted_at TEXT,
    extraction_method TEXT
);

CREATE TABLE IF NOT EXISTS benchmarks (
    benchmark_id TEXT PRIMARY KEY,
    country TEXT NOT NULL,
    sector TEXT NOT NULL,
    outcome_unit TEXT NOT NULL,
    terrain TEXT NOT NULL,
    median_cost_per_unit_cr REAL NOT NULL,
    p25_cost_per_unit_cr REAL NOT NULL,
    p75_cost_per_unit_cr REAL NOT NULL,
    source_note TEXT
);

CREATE TABLE IF NOT EXISTS verdicts (
    project_id TEXT PRIMARY KEY REFERENCES projects(project_id),
    justification_score INTEGER NOT NULL,
    justification_rationale TEXT NOT NULL,
    transparency_score INTEGER,
    transparency_conflicts_json TEXT NOT NULL,
    debate_transcript_json TEXT NOT NULL,
    scored_at TEXT NOT NULL,
    model_versions_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rankings (
    country TEXT NOT NULL,
    sector TEXT NOT NULL,
    year INTEGER NOT NULL,
    state TEXT NOT NULL,
    median_cost_per_unit_cr REAL NOT NULL,
    rank INTEGER NOT NULL,
    efficiency_score INTEGER NOT NULL,
    PRIMARY KEY (country, sector, year, state)
);

CREATE INDEX IF NOT EXISTS idx_projects_state ON projects(state);
CREATE INDEX IF NOT EXISTS idx_projects_sector ON projects(sector);
CREATE INDEX IF NOT EXISTS idx_projects_year ON projects(year);
CREATE INDEX IF NOT EXISTS idx_source_documents_project ON source_documents(project_id);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.sqlite_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_DDL)
    conn.commit()


def load_synthetic(conn: sqlite3.Connection) -> None:
    projects = pd.read_csv(config.synthetic_dir / "projects.csv")
    projects["cost_per_unit_cr"] = projects["utilized_cr"] / projects["outcome_value"]
    projects[[
        "project_id", "country", "state", "sector", "name", "year",
        "sanctioned_cr", "disbursed_cr", "utilized_cr", "outcome_value",
        "outcome_unit", "cost_per_unit_cr", "description",
    ]].to_sql("projects", conn, if_exists="append", index=False)

    docs = pd.read_csv(config.synthetic_dir / "source_documents.csv")
    docs[[
        "doc_id", "project_id", "source_type", "title", "url_or_path",
        "claimed_sanctioned_cr", "claimed_disbursed_cr", "claimed_utilized_cr",
        "extracted_at", "extraction_method",
    ]].to_sql("source_documents", conn, if_exists="append", index=False)

    benchmarks = pd.read_csv(config.synthetic_dir / "benchmarks.csv")
    benchmarks.to_sql("benchmarks", conn, if_exists="append", index=False)

    conn.commit()
    print(f"  loaded {len(projects)} synthetic projects, {len(docs)} source docs, "
          f"{len(benchmarks)} benchmarks")


def load_seed(conn: sqlite3.Connection) -> None:
    seed_path = config.seed_dir / "seed_projects.json"
    if not seed_path.exists():
        print("  no seed_projects.json found — run `python3 -m pipeline.generate_seed` first")
        return

    records = json.loads(seed_path.read_text())
    cur = conn.cursor()
    n_projects = n_docs = n_verdicts = 0

    for record in records:
        p = record["project"]
        cur.execute(
            """INSERT OR REPLACE INTO projects
               (project_id, country, state, sector, name, year, sanctioned_cr, disbursed_cr,
                utilized_cr, outcome_value, outcome_unit, cost_per_unit_cr, description)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (p["project_id"], p["country"], p["state"], p["sector"], p["name"], p["year"],
             p["sanctioned_cr"], p["disbursed_cr"], p["utilized_cr"], p["outcome_value"],
             p["outcome_unit"], p["cost_per_unit_cr"], p["description"]),
        )
        n_projects += 1

        for d in record["source_documents"]:
            cur.execute(
                """INSERT OR REPLACE INTO source_documents
                   (doc_id, project_id, source_type, title, url_or_path, claimed_sanctioned_cr,
                    claimed_disbursed_cr, claimed_utilized_cr, extracted_at, extraction_method)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (d["doc_id"], d["project_id"], d["source_type"], d["title"], d["url_or_path"],
                 d["claimed_sanctioned_cr"], d["claimed_disbursed_cr"], d["claimed_utilized_cr"],
                 d["extracted_at"], d["extraction_method"]),
            )
            n_docs += 1

        v = record["verdict"]
        cur.execute(
            """INSERT OR REPLACE INTO verdicts
               (project_id, justification_score, justification_rationale, transparency_score,
                transparency_conflicts_json, debate_transcript_json, scored_at, model_versions_json)
               VALUES (?,?,?,?,?,?,?,?)""",
            (v["project_id"], v["justification_score"], v["justification_rationale"],
             v["transparency_score"], json.dumps(v["transparency_conflicts"]),
             json.dumps(v["debate_transcript"]), v["scored_at"], json.dumps(v["model_versions"])),
        )
        n_verdicts += 1

    conn.commit()
    print(f"  loaded {n_projects} seed projects, {n_docs} source docs, {n_verdicts} verdicts")


def build_fallback_rankings(conn: sqlite3.Connection) -> None:
    """CPU-pandas ranking so Phase 5/6 work before the Colab cudf notebook (Phase 4) runs.
    Phase 4's notebook produces the authoritative version and can overwrite this table via
    import_rankings_csv() below — same shape, so nothing downstream needs to change.
    """
    projects = pd.read_sql("SELECT * FROM projects", conn)
    if projects.empty:
        print("  no projects loaded yet — skipping rankings")
        return

    grouped = (
        projects.groupby(["country", "sector", "year", "state"])["cost_per_unit_cr"]
        .median()
        .reset_index()
        .rename(columns={"cost_per_unit_cr": "median_cost_per_unit_cr"})
    )

    rows = []
    for (country, sector, year), group in grouped.groupby(["country", "sector", "year"]):
        group = group.sort_values("median_cost_per_unit_cr").reset_index(drop=True)
        lo, hi = group["median_cost_per_unit_cr"].min(), group["median_cost_per_unit_cr"].max()
        span = max(hi - lo, 1e-9)
        for rank, row in enumerate(group.itertuples(), start=1):
            # lower cost/unit -> higher efficiency score (100 = cheapest, 0 = most expensive)
            efficiency = round(100 * (1 - (row.median_cost_per_unit_cr - lo) / span))
            rows.append({
                "country": country, "sector": sector, "year": int(year), "state": row.state,
                "median_cost_per_unit_cr": row.median_cost_per_unit_cr,
                "rank": rank, "efficiency_score": efficiency,
            })

    conn.execute("DELETE FROM rankings")
    pd.DataFrame(rows).to_sql("rankings", conn, if_exists="append", index=False)
    conn.commit()
    print(f"  built fallback rankings: {len(rows)} rows across "
          f"{grouped['sector'].nunique()} sectors x {grouped['year'].nunique()} years")


def import_rankings_csv(csv_path) -> None:
    """Called after Phase 4's cudf_benchmark.ipynb produces its authoritative rankings CSV,
    to replace the CPU fallback with the GPU-computed (identical-shape) table."""
    conn = _connect()
    df = pd.read_csv(csv_path)
    conn.execute("DELETE FROM rankings")
    df.to_sql("rankings", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    print(f"Imported {len(df)} ranking rows from {csv_path} (replacing fallback)")


def main() -> None:
    config.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if config.sqlite_path.exists():
        config.sqlite_path.unlink()  # rebuild clean each run — idempotent, deterministic

    conn = _connect()
    print("Creating schema...")
    init_schema(conn)

    print("Loading synthetic data...")
    load_synthetic(conn)

    print("Loading seed (flagship) data...")
    load_seed(conn)

    print("Building fallback rankings (CPU pandas; Phase 4 will supersede with cudf output)...")
    build_fallback_rankings(conn)

    conn.close()
    print(f"\nDone. Database at {config.sqlite_path} "
          f"({config.sqlite_path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
