"""Supreme Council agent — synthesizes Red + Blue into a final verdict. ARCHITECTURE.md §4.4.

See red_team.py's module docstring for the design rationale. The Council additionally receives
the Transparency Score (crosscheck.py) as input — a project with conflicting sources is
inherently a weaker basis for any judgment call, which the client's scoring logic accounts for
(see llm_client.py). Justification and Transparency remain two separate reported numbers;
this coupling is a scoring *input*, never a merge of the two into one output.
"""
from __future__ import annotations

from pipeline.agents.llm_client import DebateLLMClient
from pipeline.benchmark_ratio import BenchmarkComparison
from pipeline.schema import ArgumentItem, DebateTurn, Project


def run_council(
    project: Project,
    comparison: BenchmarkComparison,
    red_args: list[ArgumentItem],
    blue_args: list[ArgumentItem],
    transparency_score: int | None,
    client: DebateLLMClient,
) -> DebateTurn:
    score, rationale = client.council_verdict(project, comparison, red_args, blue_args, transparency_score)
    verdict_label = (
        "well_justified" if score >= 75 else "partially_justified" if score >= 45 else "needs_review"
    )
    return DebateTurn(agent="council", verdict=verdict_label, score=score, rationale=rationale)
