"""
Hand-curated flagship demo projects (PLAN.md §3 critical path + Phase 1).

These are the 5-8 recognizable, carefully-written projects the live demo actually shows —
convincing content even before the full ADK/Vertex AI pipeline runs at scale. One of them
(Dwarka Expressway) uses REAL figures extracted from a real government document
(data/raw_pdfs/cag_report_19_2023_bharatmala.pdf, CAG Report No. 19 of 2023, page 51) —
proof that the extraction target is real, not just illustrative.

The other five are ILLUSTRATIVE (clearly marked as such in their source_note / title) —
inspired by real, recognizable Indian infrastructure programmes, but with invented figures,
since we have not sourced/extracted a real document for each. This is stated as a known
limitation in docs/UI_UX_DESIGN.md's About/Methodology page (Phase 8).

The debate transcripts here are hand-written in the exact shape run_debate.py's ADK agents
will later produce (ARCHITECTURE.md §4.4) — this IS this session's "mock-LLM fallback"
(PLAN.md Phase 3 fallback) for these 6 flagship projects specifically, so the UI/demo works
end-to-end regardless of whether live Vertex AI calls are wired up in time.

All responsible-AI language rules (agent.md §3) apply: calibrated, evidence-cited, never
accusatory. Run `python3 -m pipeline.config` style check via batch_score.py's lint gate
before trusting this as final in later phases.

Run: python3 -m pipeline.generate_seed
"""
from __future__ import annotations

import json

from pipeline.config import config, contains_banned_language
from pipeline.crosscheck import compute_transparency
from pipeline.schema import (
    ArgumentItem, ConflictItem, DebateTranscript, DebateTurn, ExtractionMethod,
    ModelVersions, Project, Sector, SourceDocument, SourceType, Verdict,
)


def _arg(claim: str, evidence: str, figure: str = "") -> ArgumentItem:
    return ArgumentItem(claim=claim, evidence=evidence, figure=figure)


# --------------------------------------------------------------------------------------
# 1. Dwarka Expressway — REAL figures (CAG Report No. 19 of 2023, Bharatmala Pariyojana
#    Phase-I, para 3.5.2.2, p.51): civil cost ₹7,287.29 cr across 4 projects; per-km cost
#    ₹250.77 cr against the CCEA-approved norm of ₹18.20 cr/km for the corridor programme.
#    Length implied: 7287.29 / 250.77 ≈ 29.06 km.
# --------------------------------------------------------------------------------------

DWARKA_PROJECT = Project(
    project_id="in-hr-roads-dwarka-expressway-2018",
    country="IN",
    state="Haryana",
    sector=Sector.ROADS,
    name="Dwarka Expressway (NH-48 Delhi-Gurugram decongestion)",
    year=2018,
    sanctioned_cr=7287.29,
    disbursed_cr=6922.93,
    utilized_cr=6777.18,
    outcome_value=29.06,
    outcome_unit="km",
    description=(
        "14-lane urban expressway (8-lane elevated + 6-lane at-grade) built parallel to "
        "NH-48 to decongest Delhi-Gurugram traffic; dense NCR land acquisition and elevated "
        "structure across its length."
    ),
)

DWARKA_SOURCES = [
    SourceDocument(
        doc_id="in-hr-roads-dwarka-expressway-2018-doc1",
        project_id=DWARKA_PROJECT.project_id,
        source_type=SourceType.CAG_REPORT,
        title="CAG Report No. 19 of 2023 — Bharatmala Pariyojana Phase-I",
        url_or_path="data/raw_pdfs/cag_report_19_2023_bharatmala.pdf",
        claimed_sanctioned_cr=7287.29,
        claimed_disbursed_cr=6922.93,
        claimed_utilized_cr=6777.18,
        extraction_method=ExtractionMethod.MANUAL,  # hand-transcribed for the seed set; extract.py reproduces this in Phase 2
    ),
    SourceDocument(
        doc_id="in-hr-roads-dwarka-expressway-2018-doc2",
        project_id=DWARKA_PROJECT.project_id,
        source_type=SourceType.UNION_BUDGET,
        title="NHAI Sanction Order Summary (MoRTH, Jan-Mar 2018)",
        url_or_path="synthetic://union_budget/in-hr-roads-dwarka-expressway-2018",
        claimed_sanctioned_cr=7287.29,
        claimed_disbursed_cr=7050.00,  # modest natural reporting variance
        claimed_utilized_cr=6777.18,
        extraction_method=ExtractionMethod.MANUAL,
    ),
]

DWARKA_TRANSCRIPT = DebateTranscript(turns=[
    DebateTurn(
        agent="red", stance="excessive",
        arguments=[
            _arg(
                claim="Actual per-km cost is far above the programme's own approved norm.",
                evidence="CAG Report No. 19/2023 records this corridor at ₹250.77 cr/km "
                         "against the CCEA-approved Bharatmala norm of ₹18.20 cr/km for "
                         "comparable national highway corridors.",
                figure="13.8x the CCEA-approved benchmark",
            ),
            _arg(
                claim="The scale of overrun is unusual even among urban highway projects.",
                evidence="Within our urban-terrain benchmark band (median ≈ ₹20.8 cr/km, "
                         "p75 ≈ ₹27 cr/km), this project sits roughly 9-11x above the p75 mark.",
                figure="≈11x above the urban-terrain p75 benchmark",
            ),
        ],
    ),
    DebateTurn(
        agent="blue", stance="justified",
        arguments=[
            _arg(
                claim="This is a substantially larger structure than a typical highway km.",
                evidence="The corridor is a 14-lane facility (8-lane elevated viaduct + "
                         "6-lane at-grade road), not a standard at-grade highway — elevated "
                         "construction alone typically carries a multi-fold cost premium.",
                figure="8 of 14 lanes are elevated structure",
            ),
            _arg(
                claim="Land acquisition in this corridor is among the costliest in the country.",
                evidence="The alignment runs through dense NCR (Delhi-Gurugram) urban "
                         "territory, consistent with our urban-terrain benchmark already "
                         "pricing a 2.6x premium over plain terrain.",
                figure="urban terrain multiplier already applied: 2.6x plain",
            ),
        ],
    ),
    DebateTurn(
        agent="council",
        verdict="needs_review",
        score=22,
        rationale=(
            "Even after applying the largest terrain premium in our model (urban, 2.6x) and "
            "crediting the project's genuinely unusual scope (elevated 14-lane structure), "
            "the reported cost of ₹250.77 cr/km remains roughly 9-11x above the comparable "
            "urban-terrain benchmark band, and about 13.8x the programme's own approved norm "
            "per CAG's audit. The elevated/wide-corridor scope justifies a premium, but not "
            "one of this magnitude on the evidence available. This cost warrants closer "
            "public review; it is not, on its own, evidence of wrongdoing."
        ),
    ),
])

DWARKA_VERDICT_SCORE = 22

# --------------------------------------------------------------------------------------
# 2-6: illustrative flagship projects (invented figures, clearly marked)
# --------------------------------------------------------------------------------------

def _illustrative_source(project_id: str, idx: int, source_type: SourceType, title: str,
                          sanctioned: float, disbursed: float, utilized: float) -> SourceDocument:
    return SourceDocument(
        doc_id=f"{project_id}-doc{idx}",
        project_id=project_id,
        source_type=source_type,
        title=title,
        url_or_path=f"synthetic://{source_type.value}/{project_id}",
        claimed_sanctioned_cr=sanctioned,
        claimed_disbursed_cr=disbursed,
        claimed_utilized_cr=utilized,
        extraction_method=ExtractionMethod.MANUAL,
    )


KALESHWARAM_PROJECT = Project(
    project_id="in-tg-water-kaleshwaram-component-2019",
    country="IN", state="Telangana", sector=Sector.WATER,
    name="Kaleshwaram Lift Irrigation Scheme — Package 8 pump house component (illustrative)",
    year=2019, sanctioned_cr=4200.0, disbursed_cr=5450.0, utilized_cr=5100.0,
    outcome_value=380.0, outcome_unit="mld",
    description=(
        "Illustrative component of a large multi-stage lift irrigation scheme; high-capacity "
        "pump houses lifting water across a significant elevation gain. Figures below are "
        "invented for this prototype, inspired by widely-reported cost escalation on this "
        "real programme, and are not extracted from a specific source document."
    ),
)
KALESHWARAM_SOURCES = [
    _illustrative_source(KALESHWARAM_PROJECT.project_id, 1, SourceType.STATE_BUDGET,
                          "Telangana State Budget Document (illustrative)", 4200.0, 5450.0, 5100.0),
    _illustrative_source(KALESHWARAM_PROJECT.project_id, 2, SourceType.CAG_REPORT,
                          "State Audit Report excerpt (illustrative)", 4650.0, 8500.0, 8200.0),
]
KALESHWARAM_TRANSCRIPT = DebateTranscript(turns=[
    DebateTurn(agent="red", stance="excessive", arguments=[
        _arg("Reported utilized spend is well above the sanctioned amount with no revised sanction shown in these sources.",
             "Utilized figures across the two illustrative sources range from ₹5,100 cr to ₹8,200 cr against sanctioned figures of ₹4,200-4,650 cr.",
             "up to ≈1.95x the lower reported sanction"),
        _arg("Cost per MLD is above the water-sector benchmark for this terrain.",
             "At the higher reported utilized figure, cost/MLD sits above our plain-terrain p75 benchmark.",
             "≈1.9x median plain-terrain benchmark"),
    ]),
    DebateTurn(agent="blue", stance="justified", arguments=[
        _arg("Lift irrigation with a large elevation gain carries genuinely higher energy and civil costs than gravity-fed schemes.",
             "High-lift pump house components are not directly comparable to standard plain-terrain water benchmarks.",
             "lift-scheme cost structure not fully captured by terrain benchmark"),
    ]),
    DebateTurn(agent="council", verdict="needs_review", score=29, rationale=(
        "The two illustrative sources disagree substantially on sanctioned, disbursed, and "
        "utilized figures alike (utilized ranges from ₹5,100 cr to ₹8,200 cr), which sharply "
        "limits confidence in any single figure here. Even at the lower reported figure, cost "
        "per MLD exceeds the plain-terrain benchmark band, and the lift-scheme cost premium "
        "argument is plausible but not quantified in evidence available here. This combination "
        "of substantial source disagreement and above-benchmark cost warrants closer public "
        "review of the underlying records."
    )),
])

PMGSY_PROJECT = Project(
    project_id="in-br-roads-pmgsy-rural-2021",
    country="IN", state="Bihar", sector=Sector.ROADS,
    name="PMGSY Rural Road Connectivity Package (illustrative)",
    year=2021, sanctioned_cr=210.0, disbursed_cr=205.0, utilized_cr=198.0,
    outcome_value=42.0, outcome_unit="km",
    description="Illustrative plain-terrain rural road connectivity package under PMGSY-style norms; standard construction conditions.",
)
PMGSY_SOURCES = [
    _illustrative_source(PMGSY_PROJECT.project_id, 1, SourceType.UNION_BUDGET,
                          "Union Budget PMGSY allocation summary (illustrative)", 210.0, 205.0, 198.0),
    _illustrative_source(PMGSY_PROJECT.project_id, 2, SourceType.STATE_BUDGET,
                          "Bihar State Budget rural roads statement (illustrative)", 212.0, 204.0, 199.0),
]
PMGSY_TRANSCRIPT = DebateTranscript(turns=[
    DebateTurn(agent="red", stance="excessive", arguments=[
        _arg("No material overrun found relative to the plain-terrain benchmark.",
             "Cost per km sits within the p25-p75 band for plain-terrain road construction.",
             "within normal benchmark range"),
    ]),
    DebateTurn(agent="blue", stance="justified", arguments=[
        _arg("Standard plain-terrain construction with no unusual scope.",
             "Sanctioned, disbursed, and utilized figures are close together across both sources, consistent with routine execution.",
             "cost/km within 5% of benchmark median"),
    ]),
    DebateTurn(agent="council", verdict="well_justified", score=88, rationale=(
        "Cost per km falls close to the plain-terrain benchmark median, and both sources "
        "report closely matching figures. No unusual scope or terrain factor is claimed or "
        "needed to explain the cost. This spend appears reasonable on the evidence available."
    )),
])

DISTRICT_HOSPITAL_PROJECT = Project(
    project_id="in-kl-health-district-hospital-2022",
    country="IN", state="Kerala", sector=Sector.HEALTH,
    name="District Hospital Capacity Expansion (illustrative)",
    year=2022, sanctioned_cr=145.0, disbursed_cr=140.0, utilized_cr=133.0,
    outcome_value=220.0, outcome_unit="beds",
    description="Illustrative coastal-terrain district hospital bed capacity expansion, including new ward blocks and equipment.",
)
DISTRICT_HOSPITAL_SOURCES = [
    _illustrative_source(DISTRICT_HOSPITAL_PROJECT.project_id, 1, SourceType.STATE_BUDGET,
                          "Kerala State Health Budget statement (illustrative)", 145.0, 140.0, 133.0),
    _illustrative_source(DISTRICT_HOSPITAL_PROJECT.project_id, 2, SourceType.CAG_REPORT,
                          "State health infrastructure audit excerpt (illustrative)", 146.0, 141.0, 134.0),
]
DISTRICT_HOSPITAL_TRANSCRIPT = DebateTranscript(turns=[
    DebateTurn(agent="red", stance="excessive", arguments=[
        _arg("Cost per bed is moderately above the coastal-terrain median.",
             "Utilized cost per bed sits above the benchmark median but within the p75 band.",
             "≈1.2x median coastal-terrain benchmark"),
    ]),
    DebateTurn(agent="blue", stance="justified", arguments=[
        _arg("New ward construction includes equipment costs not always captured in bare per-bed benchmarks.",
             "Scope includes new ward blocks and medical equipment, which the project description states explicitly.",
             "equipment + new-build scope"),
    ]),
    DebateTurn(agent="council", verdict="partially_justified", score=66, rationale=(
        "Cost per bed is moderately above the coastal-terrain benchmark median but within the "
        "normal p75 range, and the stated scope (new construction plus equipment) plausibly "
        "explains part of the premium. Both sources report closely matching figures. This "
        "spend is partially justified by scope; the remaining gap above the median is not "
        "fully explained by the evidence here."
    )),
])

SCHOOL_MISSION_PROJECT = Project(
    project_id="in-mp-education-school-mission-2020",
    country="IN", state="Madhya Pradesh", sector=Sector.EDUCATION,
    name="School Infrastructure Mission Package (illustrative)",
    year=2020, sanctioned_cr=95.0, disbursed_cr=93.0, utilized_cr=91.0,
    outcome_value=28.0, outcome_unit="schools",
    description="Illustrative plain-terrain school construction/upgrade package across multiple districts.",
)
SCHOOL_MISSION_SOURCES = [
    _illustrative_source(SCHOOL_MISSION_PROJECT.project_id, 1, SourceType.UNION_BUDGET,
                          "Union Budget education transfer statement (illustrative)", 95.0, 93.0, 91.0),
]
SCHOOL_MISSION_TRANSCRIPT = DebateTranscript(turns=[
    DebateTurn(agent="red", stance="excessive", arguments=[
        _arg("Cost per school is close to but slightly above the plain-terrain median.",
             "Utilized cost per school sits just above the benchmark median.",
             "≈1.1x median plain-terrain benchmark"),
    ]),
    DebateTurn(agent="blue", stance="justified", arguments=[
        _arg("Slight premium is consistent with routine multi-district execution costs.",
             "No unusual scope claimed; the small premium over median is within normal variation.",
             "within p25-p75 benchmark band"),
    ]),
    DebateTurn(agent="council", verdict="well_justified", score=79, rationale=(
        "Cost per school is close to the plain-terrain benchmark median, with only a small "
        "premium that falls within the normal p25-p75 range. Only one source document is "
        "available for this project, so the transparency assessment is limited to a single "
        "source rather than confirmed cross-source agreement."
    )),
])

SOLAR_PARK_PROJECT = Project(
    project_id="in-rj-energy-solar-park-2023",
    country="IN", state="Rajasthan", sector=Sector.ENERGY,
    name="Solar Power Park Capacity Addition (illustrative)",
    year=2023, sanctioned_cr=520.0, disbursed_cr=505.0, utilized_cr=480.0,
    outcome_value=95.0, outcome_unit="mw",
    description="Illustrative plain-terrain utility-scale solar park capacity addition.",
)
SOLAR_PARK_SOURCES = [
    _illustrative_source(SOLAR_PARK_PROJECT.project_id, 1, SourceType.UNION_BUDGET,
                          "Union Budget renewable energy allocation (illustrative)", 520.0, 505.0, 480.0),
    _illustrative_source(SOLAR_PARK_PROJECT.project_id, 2, SourceType.STATE_BUDGET,
                          "Rajasthan State Energy Budget statement (illustrative)", 518.0, 503.0, 479.0),
]
SOLAR_PARK_TRANSCRIPT = DebateTranscript(turns=[
    DebateTurn(agent="red", stance="excessive", arguments=[
        _arg("No overrun found; cost per MW is below the plain-terrain median.",
             "Utilized cost per MW sits below the benchmark median for this sector and terrain.",
             "≈0.78x median plain-terrain benchmark"),
    ]),
    DebateTurn(agent="blue", stance="justified", arguments=[
        _arg("Below-median cost is consistent with recent declines in utility-scale solar construction costs.",
             "Both sources closely agree on all three figures, with no unusual scope claimed.",
             "cost/MW well within efficient range"),
    ]),
    DebateTurn(agent="council", verdict="well_justified", score=92, rationale=(
        "Cost per MW sits notably below the plain-terrain benchmark median, and both sources "
        "closely agree on sanctioned, disbursed, and utilized figures. This spend appears "
        "efficient relative to the benchmark, with no evidence of overrun or source conflict."
    )),
])


ALL_SEED = [
    (DWARKA_PROJECT, DWARKA_SOURCES, DWARKA_TRANSCRIPT),
    (KALESHWARAM_PROJECT, KALESHWARAM_SOURCES, KALESHWARAM_TRANSCRIPT),
    (PMGSY_PROJECT, PMGSY_SOURCES, PMGSY_TRANSCRIPT),
    (DISTRICT_HOSPITAL_PROJECT, DISTRICT_HOSPITAL_SOURCES, DISTRICT_HOSPITAL_TRANSCRIPT),
    (SCHOOL_MISSION_PROJECT, SCHOOL_MISSION_SOURCES, SCHOOL_MISSION_TRANSCRIPT),
    (SOLAR_PARK_PROJECT, SOLAR_PARK_SOURCES, SOLAR_PARK_TRANSCRIPT),
]


def _council_turn(transcript: DebateTranscript) -> DebateTurn:
    return next(t for t in transcript.turns if t.agent == "council")


def build_all() -> list[dict]:
    out = []
    lint_failures = []

    for project, sources, transcript in ALL_SEED:
        transparency_score, conflicts = compute_transparency(project.project_id, sources)
        council = _council_turn(transcript)

        verdict = Verdict(
            project_id=project.project_id,
            justification_score=council.score,
            justification_rationale=council.rationale,
            transparency_score=transparency_score,
            transparency_conflicts=conflicts,
            debate_transcript=transcript,
            model_versions=ModelVersions(
                red="hand-authored-seed-v1", blue="hand-authored-seed-v1",
                council="hand-authored-seed-v1", extraction="manual",
            ),
        )

        # responsible-AI language guard (PLAN.md §5.1) — check every piece of generated text
        texts_to_check = [verdict.justification_rationale] + [
            arg.claim + " " + arg.evidence
            for turn in transcript.turns for arg in turn.arguments
        ]
        for text in texts_to_check:
            hits = contains_banned_language(text)
            if hits:
                lint_failures.append((project.project_id, hits, text))

        out.append({
            "project": project.model_dump(mode="json"),
            "source_documents": [s.model_dump(mode="json") for s in sources],
            "verdict": verdict.model_dump(mode="json"),
        })

    if lint_failures:
        raise ValueError(f"Responsible-AI language guard failed: {lint_failures}")

    return out


def main() -> None:
    records = build_all()
    config.seed_dir.mkdir(parents=True, exist_ok=True)
    out_path = config.seed_dir / "seed_projects.json"
    out_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"Wrote {len(records)} flagship seed projects -> {out_path}")
    for r in records:
        p, v = r["project"], r["verdict"]
        print(f"  - {p['name']!r}: justification={v['justification_score']} "
              f"transparency={v['transparency_score']}")


if __name__ == "__main__":
    main()
