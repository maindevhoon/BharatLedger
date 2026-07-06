"""Red Team agent — argues the project's cost is EXCESSIVE. ARCHITECTURE.md §4.2.

Thin domain wrapper around the DebateLLMClient abstraction (llm_client.py): this module owns
the *prompt framing and turn assembly*, while the client owns *how* the argument gets generated
(mock rule-based today; real Gemini via Vertex AI once USE_VERTEX_AI=true and ADC is configured
— see README). This separation is what lets the whole debate pipeline run identically whether
or not live credentials are available, and is where a full ADK LlmAgent/Runner wrapping would
slot in later without changing run_debate.py's orchestration.
"""
from __future__ import annotations

from pipeline.agents.llm_client import DebateLLMClient
from pipeline.benchmark_ratio import BenchmarkComparison
from pipeline.schema import DebateTurn, Project


def run_red_team(project: Project, comparison: BenchmarkComparison, client: DebateLLMClient) -> DebateTurn:
    arguments = client.red_team_arguments(project, comparison)
    return DebateTurn(agent="red", stance="excessive", arguments=arguments)
