"""
Bharat Ledger API — the online plane (ARCHITECTURE.md §5). Read-only over cached data; no LLM
calls in the request path except the optional demo-only /debate/live endpoint.

Run: uvicorn api.main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api import db
from api.models import BandCounts, ErrorResponse, PaginatedProjects, StatsResponse
from pipeline.config import config
from pipeline.schema import DebateTranscript, ProjectWithVerdict, RankingRow

app = FastAPI(
    title="Bharat Ledger API",
    description=(
        "Read-only API serving cached spend-reasonableness scores. Scores are decision aids "
        "that assess cost reasonableness against benchmarks and source agreement — they are "
        "not allegations of wrongdoing. See /api/v1/stats for an overview and the About page "
        "(web/) for the full methodology."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/projects", response_model=PaginatedProjects)
def list_projects(
    q: str | None = Query(default=None, description="Free-text search over name/state"),
    state: str | None = None,
    sector: str | None = None,
    year: int | None = None,
    country: str = "IN",
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    results, total = db.search_projects(
        q=q, state=state, sector=sector, year=year, country=country, limit=limit, offset=offset
    )
    return PaginatedProjects(results=results, total=total, limit=limit, offset=offset)


@app.get(
    "/api/v1/projects/{project_id}",
    response_model=ProjectWithVerdict,
    responses={404: {"model": ErrorResponse}},
)
def get_project(project_id: str):
    result = db.get_project(project_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No project found with id {project_id!r}")
    return result


@app.get(
    "/api/v1/projects/{project_id}/debate",
    response_model=DebateTranscript,
    responses={404: {"model": ErrorResponse}},
)
def get_debate(project_id: str):
    transcript = db.get_debate(project_id)
    if transcript is None:
        raise HTTPException(
            status_code=404, detail=f"No debate transcript found for project {project_id!r}"
        )
    return transcript


@app.get("/api/v1/rankings", response_model=list[RankingRow])
def get_rankings(sector: str, year: int, country: str = "IN"):
    return db.get_rankings(sector=sector, year=year, country=country)


@app.get("/api/v1/stats", response_model=StatsResponse)
def get_stats(country: str = "IN"):
    raw = db.get_stats(country=country)
    return StatsResponse(
        country=raw["country"],
        total_projects=raw["total_projects"],
        total_scored=raw["total_scored"],
        justification_band_counts=BandCounts(**raw["justification_band_counts"]),
        trending_projects=raw["trending_projects"],
    )


@app.post(
    "/api/v1/projects/{project_id}/debate/live",
    response_model=DebateTranscript,
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def run_debate_live(project_id: str):
    """Demo-only: re-runs the debate pipeline live instead of reading the cache, so the
    audience can watch the Red/Blue/Council turns generate in real time. Guarded by a config
    flag (ENABLE_LIVE_DEBATE_ENDPOINT) since this is explicitly NOT part of the online plane's
    normal cheap-at-scale design (ARCHITECTURE.md §1) — it exists purely for the live demo.
    """
    if not config.enable_live_debate_endpoint:
        raise HTTPException(status_code=403, detail="Live debate endpoint is disabled")

    # local imports: keep the offline-plane pipeline out of the API's always-loaded import path
    import sqlite3

    from pipeline.batch_score import _load_benchmarks, _load_project, _load_source_docs
    from pipeline.run_debate import run_debate_for_project

    conn = sqlite3.connect(config.sqlite_path)
    proj_cols = [d[0] for d in conn.execute("SELECT * FROM projects LIMIT 0").description]
    row = conn.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"No project found with id {project_id!r}")

    project = _load_project(row, proj_cols)
    benchmarks = _load_benchmarks(conn)
    source_docs = _load_source_docs(conn, project_id)
    conn.close()

    verdict = run_debate_for_project(project, benchmarks, source_docs)
    if verdict is None:
        raise HTTPException(status_code=404, detail="No matching benchmark for this project")
    return verdict.debate_transcript


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "use_bigquery": config.use_bigquery, "use_vertex_ai": config.use_vertex_ai}
