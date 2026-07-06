"""Blue Team agent — argues the project's cost is JUSTIFIED. ARCHITECTURE.md §4.3.

See red_team.py's module docstring for the design rationale (thin wrapper over
DebateLLMClient; identical shape whether mock or real Gemini is behind the client).
"""
from __future__ import annotations

from pipeline.agents.llm_client import DebateLLMClient
from pipeline.benchmark_ratio import BenchmarkComparison
from pipeline.schema import DebateTurn, Project


def run_blue_team(project: Project, comparison: BenchmarkComparison, client: DebateLLMClient) -> DebateTurn:
    arguments = client.blue_team_arguments(project, comparison)
    return DebateTurn(agent="blue", stance="justified", arguments=arguments)
