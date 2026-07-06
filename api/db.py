"""
Read-only data access layer for the online plane (ARCHITECTURE.md §6). One interface, two
possible backends selected by `config.use_bigquery` — SQLite is the default and what this
session's demo runs on. BigQuery implementation is stubbed for when USE_BIGQUERY=true and the
project's data has been pushed there via pipeline/load_bigquery.py (not required for the demo).

No LLM calls happen anywhere in this module — the online plane only ever reads cached rows
(PLAN.md §1, the two-plane architecture).
"""
from __future__ import annotations

import json
import sqlite3
from typing import Optional

from pipeline.config import config
from pipeline.schema import (
    ConflictItem, DebateTranscript, JustificationBand, ModelVersions, Project, ProjectSummary,
    ProjectWithVerdict, RankingRow, Sector, TransparencyBand, Verdict,
)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.sqlite_path)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_project(row: sqlite3.Row) -> Project:
    d = dict(row)
    d.pop("cost_per_unit_cr", None)
    return Project(**d)


def _row_to_verdict(row: sqlite3.Row) -> Verdict:
    return Verdict(
        project_id=row["project_id"],
        justification_score=row["justification_score"],
        justification_rationale=row["justification_rationale"],
        transparency_score=row["transparency_score"],
        transparency_conflicts=[ConflictItem(**c) for c in json.loads(row["transparency_conflicts_json"])],
        debate_transcript=DebateTranscript(**json.loads(row["debate_transcript_json"])),
        scored_at=row["scored_at"],
        model_versions=ModelVersions(**json.loads(row["model_versions_json"])),
    )


def search_projects(
    q: Optional[str] = None,
    state: Optional[str] = None,
    sector: Optional[str] = None,
    year: Optional[int] = None,
    country: str = "IN",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[ProjectSummary], int]:
    """Returns (results, total_count) for pagination."""
    conn = _connect()
    try:
        where = ["p.country = ?"]
        params: list = [country]

        if q:
            where.append("(p.name LIKE ? OR p.state LIKE ?)")
            like = f"%{q}%"
            params += [like, like]
        if state:
            where.append("p.state = ?")
            params.append(state)
        if sector:
            where.append("p.sector = ?")
            params.append(sector)
        if year:
            where.append("p.year = ?")
            params.append(year)

        where_clause = " AND ".join(where)

        total = conn.execute(
            f"SELECT COUNT(*) FROM projects p WHERE {where_clause}", params
        ).fetchone()[0]

        rows = conn.execute(
            f"""SELECT p.*, v.justification_score, v.transparency_score
                FROM projects p LEFT JOIN verdicts v ON p.project_id = v.project_id
                WHERE {where_clause}
                ORDER BY v.justification_score IS NULL, p.sanctioned_cr DESC
                LIMIT ? OFFSET ?""",
            params + [limit, offset],
        ).fetchall()

        results = []
        for row in rows:
            project = _row_to_project(row)
            j_score = row["justification_score"]
            t_score = row["transparency_score"]
            results.append(ProjectSummary(
                project_id=project.project_id, country=project.country, state=project.state,
                sector=project.sector, name=project.name, year=project.year,
                sanctioned_cr=project.sanctioned_cr, cost_per_unit_cr=project.cost_per_unit_cr,
                outcome_unit=project.outcome_unit,
                justification_score=j_score,
                justification_band=JustificationBand.from_score(j_score) if j_score is not None else None,
                transparency_band=TransparencyBand.from_score(t_score),
            ))

        return results, total
    finally:
        conn.close()


def get_project(project_id: str) -> Optional[ProjectWithVerdict]:
    conn = _connect()
    try:
        prow = conn.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone()
        if prow is None:
            return None
        project = _row_to_project(prow)

        vrow = conn.execute("SELECT * FROM verdicts WHERE project_id = ?", (project_id,)).fetchone()
        verdict = _row_to_verdict(vrow) if vrow is not None else None

        return ProjectWithVerdict(project=project, verdict=verdict)
    finally:
        conn.close()


def get_debate(project_id: str) -> Optional[DebateTranscript]:
    conn = _connect()
    try:
        vrow = conn.execute(
            "SELECT debate_transcript_json FROM verdicts WHERE project_id = ?", (project_id,)
        ).fetchone()
        if vrow is None:
            return None
        return DebateTranscript(**json.loads(vrow["debate_transcript_json"]))
    finally:
        conn.close()


def get_rankings(sector: str, year: int, country: str = "IN") -> list[RankingRow]:
    conn = _connect()
    try:
        rows = conn.execute(
            """SELECT * FROM rankings WHERE sector = ? AND year = ? AND country = ?
               ORDER BY rank ASC""",
            (sector, year, country),
        ).fetchall()
        return [RankingRow(**dict(row)) for row in rows]
    finally:
        conn.close()


def get_stats(country: str = "IN") -> dict:
    conn = _connect()
    try:
        total_projects = conn.execute(
            "SELECT COUNT(*) FROM projects WHERE country = ?", (country,)
        ).fetchone()[0]
        total_scored = conn.execute(
            """SELECT COUNT(*) FROM projects p JOIN verdicts v ON p.project_id = v.project_id
               WHERE p.country = ?""", (country,),
        ).fetchone()[0]

        band_counts = {}
        for row in conn.execute(
            """SELECT
                 CASE WHEN v.justification_score >= 75 THEN 'well_justified'
                      WHEN v.justification_score >= 45 THEN 'partially_justified'
                      ELSE 'needs_review' END AS band,
                 COUNT(*) AS n
               FROM projects p JOIN verdicts v ON p.project_id = v.project_id
               WHERE p.country = ? GROUP BY band""",
            (country,),
        ):
            band_counts[row["band"]] = row["n"]

        # trending = the hand-curated flagship projects (data/seed/, via generate_seed.py),
        # tagged distinctly by model_versions.council='hand-authored-seed-v1' — NOT the same
        # as extraction_method='manual', which the bulk synthetic dataset also uses (its
        # SourceDocuments are programmatically authored, not extracted from a real PDF, but
        # are not the curated flagship set either). This is the one signal that reliably
        # identifies just the 6 flagship projects.
        trending_rows = conn.execute(
            """SELECT p.project_id FROM projects p
               JOIN verdicts v ON p.project_id = v.project_id
               WHERE v.model_versions_json LIKE '%hand-authored-seed-v1%' AND p.country = ?
               LIMIT 6""",
            (country,),
        ).fetchall()
        trending_ids = [r["project_id"] for r in trending_rows]
        trending = []
        for pid in trending_ids:
            pv = get_project(pid)
            if pv and pv.verdict:
                trending.append(ProjectSummary.from_project_and_verdict(pv.project, pv.verdict))

        return {
            "country": country,
            "total_projects": total_projects,
            "total_scored": total_scored,
            "justification_band_counts": band_counts,
            "trending_projects": trending,
        }
    finally:
        conn.close()
