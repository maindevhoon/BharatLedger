"""API response models. Reuses pipeline/schema.py directly where possible (ARCHITECTURE.md §5
— response models mirror the same schema everything else uses); adds thin wrapper shapes for
pagination and aggregate stats that don't belong in the core domain schema.
"""
from __future__ import annotations

from pydantic import BaseModel

from pipeline.schema import ProjectSummary


class PaginatedProjects(BaseModel):
    results: list[ProjectSummary]
    total: int
    limit: int
    offset: int


class BandCounts(BaseModel):
    well_justified: int = 0
    partially_justified: int = 0
    needs_review: int = 0


class StatsResponse(BaseModel):
    country: str
    total_projects: int
    total_scored: int
    justification_band_counts: BandCounts
    trending_projects: list[ProjectSummary]


class ErrorResponse(BaseModel):
    error: str
    detail: str = ""
