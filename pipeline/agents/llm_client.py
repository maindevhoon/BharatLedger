"""
LLM client abstraction for the debate agents (ARCHITECTURE.md §4, PLAN.md Phase 3 fallback).

Two implementations behind one interface:
  - MockLLMClient  — deterministic, rule-based, keyed off the benchmark ratio. No network, no
                     cost, no credentials. This is the DEFAULT (config.use_vertex_ai=false) and
                     is what makes the offline plane, caching, and UI replay fully exercisable
                     in this session without live GCP auth.
  - GeminiClient   — real Vertex AI Gemini calls via google-genai. Only instantiated when
                     config.use_vertex_ai=true (requires `gcloud auth application-default
                     login` to have been run — see README). Uses structured output (JSON
                     schema) so responses parse directly into ArgumentItem / verdict fields.

run_debate.py asks for a client via get_llm_client() and never branches on which one it got —
same responsible-AI system preamble (ARCHITECTURE.md §4.0) applies to both.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from pipeline.benchmark_ratio import BenchmarkComparison
from pipeline.config import config
from pipeline.schema import ArgumentItem, Project

SYSTEM_PREAMBLE = """You are an analyst for Bharat Ledger, a public-spending TRANSPARENCY tool. You help citizens
reason about whether government spending is reasonable. You are NOT an accuser and NOT a court.
Hard rules:
- Never use the words corrupt, corruption, scam, loot, fraud, stolen, embezzled, or synonyms.
- Never assert wrongdoing or intent. You assess reasonableness of COST against evidence only.
- Every claim must cite a specific figure, benchmark, or contextual factor you were given.
- If evidence is insufficient, say so plainly rather than speculate.
- Output must be calibrated: "exceeds the median benchmark by X%", "partially justified", etc.
"""


class DebateLLMClient(Protocol):
    def red_team_arguments(
        self, project: Project, comparison: BenchmarkComparison
    ) -> list[ArgumentItem]: ...

    def blue_team_arguments(
        self, project: Project, comparison: BenchmarkComparison
    ) -> list[ArgumentItem]: ...

    def council_verdict(
        self,
        project: Project,
        comparison: BenchmarkComparison,
        red_args: list[ArgumentItem],
        blue_args: list[ArgumentItem],
        transparency_score: int | None,
    ) -> tuple[int, str]:
        """Returns (justification_score, rationale)."""
        ...


# --------------------------------------------------------------------------------------
# Mock client — deterministic, rule-based, the default for this session
# --------------------------------------------------------------------------------------

class MockLLMClient:
    """Rule-based stand-in for the real agents. Arguments and scores are generated from the
    benchmark ratio and transparency score using the same reasoning shape a real Gemini call
    would follow (ARCHITECTURE.md §4.2-4.4), just without the network round-trip. This is what
    lets batch_score.py score all 853+ synthetic projects instantly, for free, in this session.
    """

    model_name = "mock-rule-based-v1"

    def red_team_arguments(
        self, project: Project, comparison: BenchmarkComparison
    ) -> list[ArgumentItem]:
        ratio = comparison.ratio
        args = []
        if ratio > 1.05:
            args.append(ArgumentItem(
                claim=f"Cost per {project.outcome_unit} exceeds the {comparison.benchmark.terrain}-terrain "
                      f"median benchmark.",
                evidence=(
                    f"Reported cost is ₹{project.cost_per_unit_cr:,.2f} cr/{project.outcome_unit} "
                    f"against a median benchmark of ₹{comparison.benchmark.median_cost_per_unit_cr:,.2f} "
                    f"cr/{project.outcome_unit} for {comparison.benchmark.terrain} terrain."
                ),
                figure=f"{ratio:.2f}x median benchmark",
            ))
        else:
            args.append(ArgumentItem(
                claim="No material excess found relative to the benchmark median.",
                evidence=(
                    f"Reported cost of ₹{project.cost_per_unit_cr:,.2f} cr/{project.outcome_unit} "
                    f"is at or below the {comparison.benchmark.terrain}-terrain median benchmark."
                ),
                figure=f"{ratio:.2f}x median benchmark",
            ))
        if ratio > 1.8:
            args.append(ArgumentItem(
                claim="The scale of the premium is unusual even accounting for the applied terrain factor.",
                evidence=(
                    f"Even the upper (p75) benchmark band for {comparison.benchmark.terrain} terrain is "
                    f"₹{comparison.benchmark.p75_cost_per_unit_cr:,.2f} cr/{project.outcome_unit}; this "
                    f"project exceeds that as well."
                ),
                figure=f"above p75 benchmark ({comparison.benchmark.p75_cost_per_unit_cr:,.2f} cr)",
            ))
        return args

    def blue_team_arguments(
        self, project: Project, comparison: BenchmarkComparison
    ) -> list[ArgumentItem]:
        args = [ArgumentItem(
            claim=f"Project context: {project.description}",
            evidence=(
                f"The {comparison.benchmark.terrain}-terrain benchmark already applies a cost "
                f"premium relative to plain terrain to account for this."
            ),
            figure=f"{comparison.benchmark.terrain} terrain benchmark in effect",
        )]
        if comparison.ratio <= comparison.benchmark.p75_cost_per_unit_cr / comparison.benchmark.median_cost_per_unit_cr:
            args.append(ArgumentItem(
                claim="Reported cost falls within the normal benchmark range for this terrain.",
                evidence=(
                    f"₹{project.cost_per_unit_cr:,.2f} cr/{project.outcome_unit} sits within the "
                    f"p25-p75 band (₹{comparison.benchmark.p25_cost_per_unit_cr:,.2f}-"
                    f"₹{comparison.benchmark.p75_cost_per_unit_cr:,.2f} cr)."
                ),
                figure="within p25-p75 benchmark band",
            ))
        return args

    def council_verdict(
        self,
        project: Project,
        comparison: BenchmarkComparison,
        red_args: list[ArgumentItem],
        blue_args: list[ArgumentItem],
        transparency_score: int | None,
    ) -> tuple[int, str]:
        ratio = comparison.ratio
        # deterministic prior -> score mapping, softened slightly by transparency confidence
        if ratio <= 0.85:
            base_score = 92
        elif ratio <= 1.1:
            base_score = 82
        elif ratio <= 1.4:
            base_score = 68
        elif ratio <= 1.8:
            base_score = 52
        elif ratio <= 3.0:
            base_score = 32
        else:
            base_score = 18

        # low transparency slightly reduces confidence in the justification score too, since a
        # figure we can't confirm is a weaker basis for any judgment (kept as a small nudge,
        # not a merge of the two scores — they remain reported separately in Verdict).
        if transparency_score is not None and transparency_score < 60:
            base_score = max(0, base_score - 8)

        score = int(max(0, min(100, base_score)))

        if score >= 75:
            band_phrase = "appears reasonable"
        elif score >= 45:
            band_phrase = "is partially justified"
        else:
            band_phrase = "warrants closer public review"

        rationale = (
            f"Cost is ₹{project.cost_per_unit_cr:,.2f} cr/{project.outcome_unit}, "
            f"{ratio:.2f}x the {comparison.benchmark.terrain}-terrain median benchmark of "
            f"₹{comparison.benchmark.median_cost_per_unit_cr:,.2f} cr. "
            f"{project.description} "
        )
        if transparency_score is not None and transparency_score < 60:
            rationale += (
                "Source documents for this project disagree on the reported figures, which "
                "further limits confidence in any single number. "
            )
        rationale += f"On this evidence, the spend {band_phrase}. This is not an allegation of wrongdoing."

        return score, rationale


# --------------------------------------------------------------------------------------
# Real Gemini client — used only when config.use_vertex_ai=true
# --------------------------------------------------------------------------------------

class GeminiClient:
    """Real Vertex AI Gemini client. Not exercised in this session (USE_VERTEX_AI=false,
    Application Default Credentials not yet configured — see README). google-genai is
    lazy-imported so this class can exist and be imported safely even when unused.
    """

    def __init__(self, flash_model: str | None = None, pro_model: str | None = None):
        from google import genai  # lazy import — only needed on the real path

        self._genai = genai
        self._client = genai.Client(
            vertexai=True, project=config.gcp_project, location=config.gcp_location
        )
        self.flash_model = flash_model or config.gemini_flash_model
        self.pro_model = pro_model or config.gemini_pro_model

    def _generate_json(self, model: str, prompt: str, response_schema: dict) -> dict:
        import json

        response = self._client.models.generate_content(
            model=model,
            contents=SYSTEM_PREAMBLE + "\n\n" + prompt,
            config={"response_mime_type": "application/json", "response_schema": response_schema},
        )
        return json.loads(response.text)

    def red_team_arguments(self, project: Project, comparison: BenchmarkComparison) -> list[ArgumentItem]:
        prompt = (
            f"Argue the strongest EVIDENCE-GROUNDED case that this project's cost is excessive.\n"
            f"Project: {project.name}, {project.state}, {project.sector.value}, FY{project.year}\n"
            f"Cost: ₹{project.cost_per_unit_cr:,.2f} cr/{project.outcome_unit}\n"
            f"Benchmark ({comparison.benchmark.terrain} terrain): median "
            f"₹{comparison.benchmark.median_cost_per_unit_cr:,.2f} cr, "
            f"p75 ₹{comparison.benchmark.p75_cost_per_unit_cr:,.2f} cr\n"
            f"Context: {project.description}\n"
            f"Return JSON: list of {{claim, evidence, figure}}."
        )
        schema = {"type": "array", "items": {
            "type": "object",
            "properties": {"claim": {"type": "string"}, "evidence": {"type": "string"}, "figure": {"type": "string"}},
            "required": ["claim", "evidence"],
        }}
        raw = self._generate_json(self.flash_model, prompt, schema)
        return [ArgumentItem(**item) for item in raw]

    def blue_team_arguments(self, project: Project, comparison: BenchmarkComparison) -> list[ArgumentItem]:
        prompt = (
            f"Argue the strongest EVIDENCE-GROUNDED case that this project's cost is justified.\n"
            f"Project: {project.name}, {project.state}, {project.sector.value}, FY{project.year}\n"
            f"Cost: ₹{project.cost_per_unit_cr:,.2f} cr/{project.outcome_unit}\n"
            f"Benchmark ({comparison.benchmark.terrain} terrain): median "
            f"₹{comparison.benchmark.median_cost_per_unit_cr:,.2f} cr\n"
            f"Context: {project.description}\n"
            f"Return JSON: list of {{claim, evidence, figure}}."
        )
        schema = {"type": "array", "items": {
            "type": "object",
            "properties": {"claim": {"type": "string"}, "evidence": {"type": "string"}, "figure": {"type": "string"}},
            "required": ["claim", "evidence"],
        }}
        raw = self._generate_json(self.flash_model, prompt, schema)
        return [ArgumentItem(**item) for item in raw]

    def council_verdict(
        self, project: Project, comparison: BenchmarkComparison,
        red_args: list[ArgumentItem], blue_args: list[ArgumentItem],
        transparency_score: int | None,
    ) -> tuple[int, str]:
        prompt = (
            f"Synthesize a final verdict from both sides below.\n"
            f"Deterministic benchmark ratio: {comparison.ratio:.2f}x median.\n"
            f"Transparency score (source agreement): {transparency_score}\n"
            f"Red Team (argues excessive): {[a.model_dump() for a in red_args]}\n"
            f"Blue Team (argues justified): {[a.model_dump() for a in blue_args]}\n"
            f"Return JSON: {{score: int 0-100, rationale: string <=120 words}}."
        )
        schema = {"type": "object", "properties": {
            "score": {"type": "integer"}, "rationale": {"type": "string"},
        }, "required": ["score", "rationale"]}
        raw = self._generate_json(self.pro_model, prompt, schema)
        return int(raw["score"]), raw["rationale"]


def get_llm_client() -> DebateLLMClient:
    if config.use_vertex_ai:
        return GeminiClient()
    return MockLLMClient()
