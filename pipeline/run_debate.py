"""
Orchestrates one project through the full debate pipeline: benchmark comparison -> Red Team ->
Blue Team -> Council -> Verdict. ARCHITECTURE.md §4.4, PLAN.md Phase 3.

This is the single-project building block; batch_score.py calls this in a loop over every
project lacking a cached verdict (the offline plane, PLAN.md §1).

Note on "ADK": true ADK Agent/Runner orchestration (sequential agent graph) is the natural next
step once live Vertex AI credentials are available (config.use_vertex_ai=true) — the sequencing
here (red -> blue -> council, each reading the prior turns) is already exactly the shape an ADK
SequentialAgent would run. Swapping the orchestration layer under llm_client.get_llm_client()
for a real ADK Runner is a mechanical follow-up, not a redesign.
"""
from __future__ import annotations

from pipeline.agents.council import run_council
from pipeline.agents.llm_client import DebateLLMClient, get_llm_client
from pipeline.agents.red_team import run_red_team
from pipeline.agents.blue_team import run_blue_team
from pipeline.benchmark_ratio import compare_with_terrain
from pipeline.benchmarks_data import INDIA_STATES
from pipeline.crosscheck import compute_transparency
from pipeline.schema import (
    Benchmark, DebateTranscript, ModelVersions, Project, SourceDocument, Verdict,
)


def _model_versions(client: DebateLLMClient) -> ModelVersions:
    name = getattr(client, "model_name", None)
    if name:
        return ModelVersions(red=name, blue=name, council=name, extraction=name)
    # GeminiClient exposes flash_model (red/blue) and pro_model (council) separately
    flash = getattr(client, "flash_model", "unknown")
    pro = getattr(client, "pro_model", "unknown")
    return ModelVersions(red=flash, blue=flash, council=pro, extraction=flash)


def run_debate_for_project(
    project: Project,
    benchmarks: list[Benchmark],
    source_docs: list[SourceDocument],
    client: DebateLLMClient | None = None,
) -> Verdict | None:
    """Returns None if no matching benchmark exists for this project's sector/unit (should not
    happen for in-scope sectors, but fail closed rather than fabricate a comparison)."""
    client = client or get_llm_client()

    terrain = INDIA_STATES.get(project.state, "plain")
    comparison = compare_with_terrain(project, benchmarks, terrain)
    if comparison is None:
        return None

    transparency_score, conflicts = compute_transparency(project.project_id, source_docs)

    red_turn = run_red_team(project, comparison, client)
    blue_turn = run_blue_team(project, comparison, client)
    council_turn = run_council(
        project, comparison, red_turn.arguments, blue_turn.arguments, transparency_score, client
    )

    transcript = DebateTranscript(turns=[red_turn, blue_turn, council_turn])

    return Verdict(
        project_id=project.project_id,
        justification_score=council_turn.score,
        justification_rationale=council_turn.rationale,
        transparency_score=transparency_score,
        transparency_conflicts=conflicts,
        debate_transcript=transcript,
        model_versions=_model_versions(client),
    )
