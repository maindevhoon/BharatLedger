"""
Canonical data models for Bharat Ledger — see docs/ARCHITECTURE.md §2 for the full spec.

This is the SINGLE SOURCE OF TRUTH for every entity in the system (PLAN.md §5, cross-cutting
requirement #2: "one schema, two stores"). SQLite tables, BigQuery tables, seed data files, and
API response models all derive from or validate against these classes. Never redefine these
shapes elsewhere — import from here.

Uses pydantic v2 so we get:
  - runtime validation (catches malformed synthetic/LLM data early)
  - free JSON Schema generation (useful for structured LLM output / ADK tool schemas)
  - .model_dump() for easy SQLite/BigQuery row conversion
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


# --------------------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------------------

class Sector(str, Enum):
    ROADS = "roads"
    EDUCATION = "education"
    HEALTH = "health"
    WATER = "water"
    ENERGY = "energy"


class SourceType(str, Enum):
    UNION_BUDGET = "union_budget"
    STATE_BUDGET = "state_budget"
    CAG_REPORT = "cag_report"
    SYNTHETIC = "synthetic"


class ExtractionMethod(str, Enum):
    DOCUMENT_AI = "document_ai"
    PYMUPDF = "pymupdf"
    MANUAL = "manual"  # hand-curated seed data


class JustificationBand(str, Enum):
    WELL_JUSTIFIED = "well_justified"          # 75-100
    PARTIALLY_JUSTIFIED = "partially_justified"  # 45-74
    NEEDS_REVIEW = "needs_review"                # 0-44

    @staticmethod
    def from_score(score: int) -> "JustificationBand":
        if score >= 75:
            return JustificationBand.WELL_JUSTIFIED
        if score >= 45:
            return JustificationBand.PARTIALLY_JUSTIFIED
        return JustificationBand.NEEDS_REVIEW


class TransparencyBand(str, Enum):
    CONSISTENT = "consistent"          # >= 85
    MINOR_CONFLICTS = "minor_conflicts"  # 60-84
    SOURCES_CONFLICT = "sources_conflict"  # < 60
    SINGLE_SOURCE = "single_source"     # only one source document available — not scored

    @staticmethod
    def from_score(score: Optional[int]) -> "TransparencyBand":
        if score is None:
            return TransparencyBand.SINGLE_SOURCE
        if score >= 85:
            return TransparencyBand.CONSISTENT
        if score >= 60:
            return TransparencyBand.MINOR_CONFLICTS
        return TransparencyBand.SOURCES_CONFLICT


class DebateStance(str, Enum):
    EXCESSIVE = "excessive"   # Red Team
    JUSTIFIED = "justified"   # Blue Team


# --------------------------------------------------------------------------------------
# Core entities (ARCHITECTURE.md §2.1 - §2.5)
# --------------------------------------------------------------------------------------

class Project(BaseModel):
    """A single government spending project. ARCHITECTURE.md §2.1."""

    project_id: str = Field(..., description="Stable slug, e.g. in-hr-roads-dwarka-expressway-2023")
    country: str = Field(default="IN", description="ISO-2 country code. India first, not India only.")
    state: str = Field(..., description="e.g. Haryana")
    sector: Sector
    name: str
    year: int = Field(..., description="Fiscal year start, e.g. 2023 for FY23-24")

    sanctioned_cr: float = Field(..., ge=0, description="₹ crore, amount sanctioned")
    disbursed_cr: float = Field(..., ge=0, description="₹ crore, amount disbursed so far")
    utilized_cr: float = Field(..., ge=0, description="₹ crore, amount actually utilized")

    outcome_value: float = Field(..., gt=0, description="Physical output quantity")
    outcome_unit: str = Field(..., description="km, schools, beds, mld, mw")

    description: str = Field(default="", description="Terrain/scope context — feeds the debate agents")

    @computed_field  # type: ignore[misc]
    @property
    def cost_per_unit_cr(self) -> float:
        """₹ crore per outcome unit. Derived, never stored independently, to avoid drift."""
        if self.outcome_value <= 0:
            return 0.0
        return round(self.utilized_cr / self.outcome_value, 4)


class SourceDocument(BaseModel):
    """One document's claimed figures for a project. ARCHITECTURE.md §2.2.

    Multiple SourceDocument rows can exist per project_id; disagreement between them is the
    raw material for the Transparency Score (see crosscheck.py).
    """

    doc_id: str
    project_id: str
    source_type: SourceType
    title: str
    url_or_path: str = Field(default="", description="Provenance — file path or URL")

    claimed_sanctioned_cr: Optional[float] = None
    claimed_disbursed_cr: Optional[float] = None
    claimed_utilized_cr: Optional[float] = None

    extracted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    extraction_method: ExtractionMethod = ExtractionMethod.MANUAL


class Benchmark(BaseModel):
    """A cost-per-unit yardstick used by the debate agents and the deterministic prior.
    ARCHITECTURE.md §2.3.
    """

    benchmark_id: str
    country: str = "IN"
    sector: Sector
    outcome_unit: str
    terrain: str = Field(..., description="plain, hilly, urban, coastal — cost driver")

    median_cost_per_unit_cr: float = Field(..., gt=0)
    p25_cost_per_unit_cr: float = Field(..., gt=0)
    p75_cost_per_unit_cr: float = Field(..., gt=0)

    source_note: str = ""


class ConflictItem(BaseModel):
    """One cross-source disagreement, part of Verdict.transparency_conflicts."""

    field: str = Field(..., description="e.g. sanctioned_cr")
    source_a: str
    value_a: float
    source_b: str
    value_b: float
    delta_cr: float


class ArgumentItem(BaseModel):
    """One argument made by Red Team or Blue Team."""

    claim: str
    evidence: str
    figure: str = Field(default="", description="The specific number/benchmark cited")


class DebateTurn(BaseModel):
    """One turn in the debate transcript (ARCHITECTURE.md §4.4)."""

    agent: str = Field(..., description="'red', 'blue', or 'council'")
    stance: Optional[str] = None  # DebateStance value for red/blue; None for council
    arguments: list[ArgumentItem] = Field(default_factory=list)
    verdict: Optional[str] = None       # only set on the council turn
    score: Optional[int] = None         # only set on the council turn
    rationale: Optional[str] = None     # only set on the council turn


class DebateTranscript(BaseModel):
    turns: list[DebateTurn] = Field(default_factory=list)


class ModelVersions(BaseModel):
    red: str = ""
    blue: str = ""
    council: str = ""
    extraction: str = ""


class Verdict(BaseModel):
    """The cached output of the offline plane for one project. ARCHITECTURE.md §2.4.

    This is what the online plane (FastAPI) reads and never recomputes on the fly.
    """

    project_id: str

    justification_score: int = Field(..., ge=0, le=100)
    justification_rationale: str

    transparency_score: Optional[int] = Field(default=None, ge=0, le=100)
    transparency_conflicts: list[ConflictItem] = Field(default_factory=list)

    debate_transcript: DebateTranscript = Field(default_factory=DebateTranscript)

    scored_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_versions: ModelVersions = Field(default_factory=ModelVersions)

    @computed_field  # type: ignore[misc]
    @property
    def justification_band(self) -> JustificationBand:
        return JustificationBand.from_score(self.justification_score)

    @computed_field  # type: ignore[misc]
    @property
    def transparency_band(self) -> TransparencyBand:
        return TransparencyBand.from_score(self.transparency_score)


class RankingRow(BaseModel):
    """One row of the state efficiency leaderboard, produced by the cudf benchmark notebook
    (or its CPU-pandas fallback). ARCHITECTURE.md §2.5.
    """

    country: str = "IN"
    sector: Sector
    year: int
    state: str

    median_cost_per_unit_cr: float
    rank: int = Field(..., ge=1)
    efficiency_score: int = Field(..., ge=0, le=100)


# --------------------------------------------------------------------------------------
# Composite / API-facing shapes
# --------------------------------------------------------------------------------------

class ProjectWithVerdict(BaseModel):
    """What the Project Score Card screen needs in one response: project + its verdict.
    Mirrors GET /projects/{project_id} in ARCHITECTURE.md §5.
    """

    project: Project
    verdict: Optional[Verdict] = None


class ProjectSummary(BaseModel):
    """Lightweight shape for search/listing/trending screens (ProjectCard component)."""

    project_id: str
    country: str
    state: str
    sector: Sector
    name: str
    year: int
    sanctioned_cr: float
    cost_per_unit_cr: float
    outcome_unit: str
    justification_score: Optional[int] = None
    justification_band: Optional[JustificationBand] = None
    transparency_band: Optional[TransparencyBand] = None

    @staticmethod
    def from_project_and_verdict(project: Project, verdict: Optional[Verdict]) -> "ProjectSummary":
        return ProjectSummary(
            project_id=project.project_id,
            country=project.country,
            state=project.state,
            sector=project.sector,
            name=project.name,
            year=project.year,
            sanctioned_cr=project.sanctioned_cr,
            cost_per_unit_cr=project.cost_per_unit_cr,
            outcome_unit=project.outcome_unit,
            justification_score=verdict.justification_score if verdict else None,
            justification_band=verdict.justification_band if verdict else None,
            transparency_band=verdict.transparency_band if verdict else None,
        )
