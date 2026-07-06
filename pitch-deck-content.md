# Bharat Ledger — Pitch Deck Content
### For: Google Cloud Gen AI Academy, APAC Edition — 11-slide template
### Track: "Create a data intelligence tool people would actually use"

Instructions for the AI filling this template: populate each of the 11 existing slides using the
content below. Keep the existing template branding, layout, and section headings intact — only
fill in the placeholder text/content areas, and generate the diagrams described where a slide
calls for one. Keep text concise and spacious; do not compress bullets into paragraphs.

---

## Slide 1 — Cover / Participant Details

- Participant Name: `[FILL IN — name / team name]`
- Problem Statement: **Create a data intelligence tool people would actually use**

---

## Slide 2 — Brief about the idea

**Suggested heading:** Bharat Ledger — Turning 60-Page Budget PDFs Into a 5-Second Verdict

**Body text:**
Indian government spending data is public — but it's buried in 50–60 page Union Budget, state
budget, and CAG audit PDFs that no ordinary citizen has the time or domain expertise to parse.
Bharat Ledger is a decision-intelligence dashboard that lets any citizen, student, or journalist
search a government project and instantly see two things: a **Justification Score** (is this
spend reasonable given terrain, scale, and comparable projects?) and a **Transparency Score**
(do official sources even agree on the numbers?). Both scores are produced by a multi-agent AI
pipeline that debates the evidence before reaching a verdict — and shows its reasoning, not just
a number.

---

## Slide 3 — Solution Explanation

**Suggested heading:** From 60 Pages of PDF to One Auditable Score

**How did you approach the problem using Google Cloud tech?**
- Ingestion & extraction agents (Vertex AI, Gemini 2.5 Flash) parse raw budget/CAG PDFs into
  structured claims (sanctioned, disbursed, utilized, outcomes)
- Structured data + cached verdicts stored in BigQuery
- Debate and verdict agents orchestrated with the **Agent Development Kit (ADK)** on Vertex AI —
  directly building on the hackathon's own ADK workshop track
- NVIDIA cudf.pandas accelerates state × sector × year aggregation for live ranking recomputation

**What real-world problem does it solve, and what's the impact?**
- Citizens/journalists currently have no way to judge if a claimed spend (e.g. "₹1,200cr highway
  widening") is reasonable — this requires engineering/economics literacy nobody has time for
- Impact: turns an unreadable document into a plain-language, comparable score in seconds — for
  citizens, students, journalists, and RTI researchers

**Core architecture/workflow — how data becomes a decision:**
PDF → Extraction Agent → Cross-Source Consistency Check → Red Team vs. Blue Team Debate →
Supreme Council Verdict → cached Justification + Transparency Scores → Dashboard

---

## Slide 4 — Opportunities

**Suggested heading:** Not Another Budget Tracker — An Auditable Reasoning Engine

**How is this different from existing ideas?**
- Existing budget-transparency sites show raw numbers with no judgment support — Bharat Ledger
  shows the reasoning, not just the figure
- Separates two signals nobody else separates: is it reasonable (Justification) vs. do sources
  even agree (Transparency) — a project can fail one without failing the other
- Positioned as decision-support, not a verdict machine — avoids the "corruption tracker" framing
  that invites backlash; arms citizens with legible evidence instead

**USP:**
- Judicial-style multi-agent debate (Red Team / Blue Team / Supreme Council, built with ADK) —
  every score ships with a visible, replayable rationale, not a black-box number
- Built for the actual bottleneck: nobody reads 60-page PDFs — we do it for them, at scale
- GPU-accelerated aggregation makes state-vs-state comparison interactive, not a static
  precomputed chart

---

## Slide 5 — Features

**Suggested heading:** What Bharat Ledger Does

- **Instant Justification Score** — 0–100 reasonableness score per project, with written rationale
- **Transparency/Confusion Score** — flags when sources disagree on basic facts
- **Multi-agent debate replay** — watch Red Team vs. Blue Team argue, then the Council's verdict
- **State-vs-state rankings** — spend-per-outcome (₹/km road, ₹/school) across states and years
- *(Roadmap)* **Photo-to-cost-check** — upload an infrastructure photo, get a benchmark
  cost-reasonableness check
- *(Roadmap)* **Citizen attention heatmap** — aggregated search interest fed back as a signal to
  government stakeholders

---

## Slide 6 — Process Flow / Use-Case Diagram

**Suggested heading:** From Search to Score in Seconds

**Diagram to generate (left-to-right flow, 4 boxes with icons):**
```
[Citizen searches a project]
        ↓
[Cached BigQuery lookup] ──(miss)──→ [Offline ADK pipeline: Extract → Cross-check → Debate → Verdict]
        ↓ (hit)                                          ↓
[Dashboard: Justification Score + Transparency Score + Rationale] ←──┘
        ↓
[User explores debate transcript / state rankings / shares finding]
```
Suggested icons: magnifying glass (search), database/lightning (cache), AI brain (pipeline),
gavel/scale (score), share icon (citizen action).

---

## Slide 7 — Wireframes / Mock Diagrams

**Suggested heading:** Product Walkthrough

**Screens to mock up:**
1. Search/home screen — search bar + trending projects + state filter
2. Project detail card — Justification Score (large gauge) + Transparency Score badge + one-line
   rationale
3. Debate replay view — two-column layout: Red Team argument | Blue Team argument, Council
   verdict banner below
4. State ranking table/leaderboard — sortable ₹/outcome-unit table, color-coded scores

**Fallback text if mockups aren't ready:**
Prototype includes four core screens: project search, score dashboard, live debate replay, and
state comparison rankings — see Slide 10 for snapshots.

---

## Slide 8 — Architecture Diagram

**Suggested heading:** System Architecture

**Layered diagram to generate (vertical stack, one colored band per layer):**
```
FRONTEND        → Dashboard (search, score cards, debate replay, rankings)
                     ↓
API/BACKEND     → Agent Development Kit (ADK) orchestration layer
                     ↓
AI MODEL LAYER  → Vertex AI — Gemini 2.5 Flash: Extraction Agent | Red Team | Blue Team | Council
                     ↓
DATA LAYER      → BigQuery (structured spend data, cached verdicts, debate transcripts)
                     ↓
ACCELERATION    → NVIDIA cudf.pandas (state × sector × year aggregation)
                     ↓
SOURCES         → Union Budget PDFs, State Budgets, CAG Reports (2–3 real + synthetic fill)
```
Use Google Cloud icons for Vertex AI/BigQuery/ADK, and the NVIDIA icon for the acceleration band.

---

## Slide 9 — Technologies / Google / NVIDIA Services

**Suggested heading:** Why This Stack

| Technology | Role | Why |
|---|---|---|
| Vertex AI (Gemini 2.5 Flash) | All agents (extraction, debate, verdict) | Cheap enough (~$0.30/1M input tokens) for thousands of debate calls within free credits; draws down GCP trial credit unlike direct AI Studio API |
| Agent Development Kit (ADK) | Multi-agent orchestration | Purpose-built for the debate → council pattern; directly builds on the hackathon's own ADK workshop |
| BigQuery | Structured data + cached verdicts | Scales to the full national budget dataset without re-running agents per request |
| NVIDIA cudf.pandas | State/sector/year aggregation | Turns multi-minute pandas joins into sub-second — enables live, interactive re-ranking instead of static charts |

**Scalability note:**
Caching verdicts in BigQuery means the live dashboard never waits on LLM inference — the
expensive multi-agent debate runs once offline per project, not per user request, making this
architecture cheap to scale to millions of users.

---

## Slide 10 — Prototype Snapshots

**Suggested heading:** Snapshots of the Prototype

**If real screenshots aren't ready, required list:**
1. Search/home screen
2. A project's Justification + Transparency score card
3. Debate replay view
4. State ranking leaderboard

---

## Slide 11 — Closing

**Suggested heading:** Thank You *(keep template branding as-is)*

**Optional tagline addition:** "Bharat Ledger — Build in APAC. Build for the world."

---

## Open items to confirm before finalizing
- Participant/team name (Slide 1)
- Whether real working screenshots will exist before submission, or Slide 10 stays as a
  fallback list
- Whether the two roadmap features (photo cost-check, attention heatmap) should be shown at all
  given they are not part of the committed first build
