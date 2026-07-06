"""
Runs the offline debate pipeline over every project lacking a cached verdict, and writes
results into the `verdicts` table. PLAN.md Phase 3 deliverable: idempotent, re-runnable, skips
already-scored projects (the 6 seed projects already have hand-authored verdicts from
generate_seed.py and are skipped here).

Applies the responsible-AI language guard (agent.md §3 / PLAN.md §5.1) to every generated
rationale and argument before caching; any hit raises rather than silently caching bad text.

Run: python3 -m pipeline.batch_score [--limit N] [--force]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time

from pipeline.agents.llm_client import get_llm_client
from pipeline.config import config, contains_banned_language
from pipeline.run_debate import run_debate_for_project
from pipeline.schema import Benchmark, Project, Sector, SourceDocument


def _load_benchmarks(conn: sqlite3.Connection) -> list[Benchmark]:
    rows = conn.execute("SELECT * FROM benchmarks").fetchall()
    cols = [d[0] for d in conn.execute("SELECT * FROM benchmarks LIMIT 0").description]
    return [Benchmark(**dict(zip(cols, row))) for row in rows]


def _load_project(row, cols) -> Project:
    d = dict(zip(cols, row))
    d.pop("cost_per_unit_cr", None)  # computed field, not a constructor arg
    return Project(**d)


def _load_source_docs(conn: sqlite3.Connection, project_id: str) -> list[SourceDocument]:
    cols = [d[0] for d in conn.execute("SELECT * FROM source_documents LIMIT 0").description]
    rows = conn.execute(
        "SELECT * FROM source_documents WHERE project_id = ?", (project_id,)
    ).fetchall()
    return [SourceDocument(**dict(zip(cols, row))) for row in rows]


def _check_language(text: str, project_id: str, where: str) -> None:
    hits = contains_banned_language(text)
    if hits:
        raise ValueError(
            f"Responsible-AI language guard failed for {project_id} ({where}): "
            f"found banned terms {hits} in: {text!r}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Only score the first N pending projects")
    parser.add_argument("--force", action="store_true", help="Re-score projects that already have a verdict")
    args = parser.parse_args()

    conn = sqlite3.connect(config.sqlite_path)
    conn.row_factory = None

    benchmarks = _load_benchmarks(conn)
    proj_cols = [d[0] for d in conn.execute("SELECT * FROM projects LIMIT 0").description]

    if args.force:
        pending_rows = conn.execute("SELECT * FROM projects").fetchall()
    else:
        pending_rows = conn.execute(
            "SELECT p.* FROM projects p LEFT JOIN verdicts v ON p.project_id = v.project_id "
            "WHERE v.project_id IS NULL"
        ).fetchall()

    if args.limit:
        pending_rows = pending_rows[: args.limit]

    client = get_llm_client()
    print(f"Scoring {len(pending_rows)} project(s) using client: {type(client).__name__}")

    scored = 0
    skipped_no_benchmark = 0
    t0 = time.time()

    for row in pending_rows:
        project = _load_project(row, proj_cols)
        source_docs = _load_source_docs(conn, project.project_id)

        verdict = run_debate_for_project(project, benchmarks, source_docs, client=client)
        if verdict is None:
            skipped_no_benchmark += 1
            continue

        # responsible-AI gate — check every piece of generated text before caching
        _check_language(verdict.justification_rationale, project.project_id, "council rationale")
        for turn in verdict.debate_transcript.turns:
            for arg in turn.arguments:
                _check_language(arg.claim + " " + arg.evidence, project.project_id, f"{turn.agent} argument")

        conn.execute(
            """INSERT OR REPLACE INTO verdicts
               (project_id, justification_score, justification_rationale, transparency_score,
                transparency_conflicts_json, debate_transcript_json, scored_at, model_versions_json)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                verdict.project_id, verdict.justification_score, verdict.justification_rationale,
                verdict.transparency_score,
                json.dumps([c.model_dump(mode="json") for c in verdict.transparency_conflicts]),
                json.dumps(verdict.debate_transcript.model_dump(mode="json")),
                verdict.scored_at, json.dumps(verdict.model_versions.model_dump(mode="json")),
            ),
        )
        scored += 1
        if scored % 100 == 0:
            print(f"  ... {scored} scored")

    conn.commit()
    conn.close()

    elapsed = time.time() - t0
    print(f"\nDone. Scored {scored} project(s) in {elapsed:.1f}s "
          f"({skipped_no_benchmark} skipped: no matching benchmark).")


if __name__ == "__main__":
    main()
