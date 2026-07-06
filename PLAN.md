# Bharat Ledger — Master Build Plan

> **Purpose of this document.** This is the authoritative, phase-wise implementation plan for
> Bharat Ledger. It is written to be handed to an implementer (human or an AI coding agent such as
> Claude Sonnet) who has NOT been part of the design conversation. Everything needed to build is
> either here or linked from here. Read [`agent.md`](./agent.md) first for the product concept and
> the responsible-AI framing; read [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) for system
> design and [`docs/UI_UX_DESIGN.md`](./docs/UI_UX_DESIGN.md) for the design system.

---

## 0. TL;DR for the implementer

- **What we are building:** a web app where any Indian citizen can search a government project and
  instantly see two auditable scores — a **Justification Score** (is this spend reasonable?) and a
  **Transparency Score** (do official sources even agree on the numbers?) — each backed by a
  replayable multi-agent AI debate. Plus state-vs-state efficiency rankings.
- **Who it is for:** citizens, students, journalists, RTI researchers. India first, built so more
  countries can be added later without a rewrite.
- **The one non-negotiable design rule:** this is a **decision-support and transparency tool, not a
  verdict/corruption machine.** All copy, all agent prompts, all outputs use calibrated language
  ("partially justified", "sources conflict by ₹X") and never accusatory language ("corrupt",
  "scam", "loot"). See `agent.md` §3. If any generated text violates this, it is a bug.
- **Stack:** React + Vite + Tailwind (frontend) · FastAPI (read-only API) · BigQuery + local SQLite
  mirror (data) · Vertex AI Gemini via **ADK** (agents) · Document AI (+PyMuPDF fallback) for PDF
  extraction · NVIDIA **cudf.pandas** on Google Colab T4 (acceleration benchmark).
- **Time box:** designed to reach demo-ready in **one long session**, with an explicit critical
  path (§3) that guarantees deck screenshots even if later phases slip.

---

## 1. Architectural spine (two planes)

The single most important structural idea. Everything else hangs off this.

```
┌─────────────────────────── OFFLINE PLANE (batch, slow, expensive) ───────────────────────────┐
│  Real + synthetic PDFs ─► Extraction ─► Cross-Check ─► Red/Blue Debate ─► Council Verdict     │
│                                    │                                              │            │
│                                    ▼                                              ▼            │
│                          Transparency Score                            Justification Score     │
│                                    └───────────────┬──────────────────────────────┘           │
│                                                    ▼                                           │
│                                    Cache to BigQuery (verdicts, transcripts, scores)           │
│                                    + cudf.pandas builds the rankings table                     │
└────────────────────────────────────────────────────────────────────────────────────────────┘
                                                     │  (writes cached rows only)
                                                     ▼
┌─────────────────────────── ONLINE PLANE (live, fast, cheap) ─────────────────────────────────┐
│  React UI ─► FastAPI (read-only) ─► reads cached verdicts/rankings ─► renders instantly        │
│  (ONE optional "watch debate live" button re-runs the pipeline on demand, for the demo only)   │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Why this matters for judging:** the expensive multi-agent debate runs **once per project, offline**.
Live users only ever read a cached row, so the system scales to millions of users at trivial cost.
State this explicitly in the pitch.

---

## 2. Repository layout (target)

```
TruthIndia/
├── agent.md                     # product concept + responsible-AI framing (exists)
├── pitch-deck-content.md        # slide content (exists)
├── PLAN.md                      # this file
├── README.md                    # P8 — how to run everything
├── docs/
│   ├── ARCHITECTURE.md          # system design, schema, API contract, agent specs
│   └── UI_UX_DESIGN.md          # India-first design system + screen specs
├── data/
│   ├── raw_pdfs/                # 2–3 real government PDFs + synthetic PDFs
│   ├── synthetic/               # generated CSVs (projects, benchmarks, outcomes)
│   ├── bharat_ledger.sqlite     # local mirror of BigQuery (demo runs offline)
│   └── seed/                    # curated demo projects (hand-tuned for the live demo)
├── pipeline/                    # OFFLINE PLANE
│   ├── config.py                # env, project id, model names, paths
│   ├── schema.py                # dataclasses / pydantic models for every entity
│   ├── generate_synthetic.py    # synthetic data generator (calibrated to real magnitudes)
│   ├── extract.py               # Document AI / PyMuPDF → structured figures
│   ├── crosscheck.py            # cross-source consistency → Transparency Score
│   ├── agents/                  # ADK agents
│   │   ├── extraction_agent.py
│   │   ├── red_team.py
│   │   ├── blue_team.py
│   │   └── council.py
│   ├── run_debate.py            # orchestrates Red/Blue/Council for one project
│   ├── batch_score.py           # runs the whole offline plane over all projects → cache
│   └── load_bigquery.py         # push cached rows to BigQuery (+ mirror to SQLite)
├── acceleration/
│   └── cudf_benchmark.ipynb     # Colab T4 notebook: pandas vs cudf.pandas + builds rankings
├── api/                         # ONLINE PLANE
│   ├── main.py                  # FastAPI app
│   ├── db.py                    # read cached rows (BigQuery in prod, SQLite for demo)
│   └── models.py                # response schemas (mirror docs/ARCHITECTURE.md contract)
└── web/                         # React frontend (see docs/UI_UX_DESIGN.md)
    ├── src/
    │   ├── components/          # ScoreGauge, TransparencyBadge, ProjectCard, ...
    │   ├── pages/               # Home, Project, Debate, Rankings, About
    │   ├── lib/                 # rupee formatting, i18n, api client
    │   └── i18n/                # en.json, hi.json
    └── ...
```

---

## 3. CRITICAL PATH TO DEMO SCREENSHOTS (protect this above all else)

If time runs short in the session, **this ordered chain is what must survive** — it is the minimum
that produces real, deck-ready screenshots for Slides 7 and 10 and a working live demo:

1. **P1 synthetic data** (skip real-PDF sourcing if needed) → seed SQLite directly.
2. **A handful (5–8) of hand-curated demo projects** with realistic pre-written scores/rationale in
   `data/seed/` — so the UI has convincing content even if the live pipeline isn't finished.
3. **P5 FastAPI** read-only over SQLite.
4. **P6 React UI** — the five screens rendering the seeded data.
5. **Screenshots** of Home, Project card, Debate replay, Rankings → Slides 7 & 10.

Everything else (real Document AI extraction, live ADK debate on Vertex AI, the cudf benchmark on
Colab) is **real and should be built**, but is demonstrated at small scale and is NOT on the
screenshot critical path. `batch_score.py` must be able to write the same row shape that the seed
data uses, so seed → real is a drop-in swap, not a rewrite.

> **Rule for the implementer:** the seed data and the pipeline output MUST share one schema
> (`pipeline/schema.py`). Never let the demo depend on the cloud being up.

---

## 4. Phases

Each phase lists: **Goal · Deliverables · Key files · Acceptance criteria · Depends on · Effort ·
Fallback.** Effort is relative (S/M/L) for one session, not wall-clock hours.

### Phase 0 — Foundations & environment
- **Goal:** repo scaffolding, config, and a verified path to Google Cloud, so no later phase blocks
  on setup.
- **Deliverables:**
  - Directory tree from §2 created (empty stubs where needed).
  - `pipeline/config.py`: reads `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, model names,
    `USE_BIGQUERY` (bool; default false → use SQLite), all paths. No secrets in code.
  - `pipeline/schema.py`: the canonical data models (see ARCHITECTURE §schema). Everything imports
    types from here.
  - `.env.example`, `requirements.txt` (pipeline+api), `web/package.json` deps chosen.
  - `README.md` stub with run order.
- **Acceptance:** `python -c "import pipeline.config, pipeline.schema"` succeeds; `gcloud config list`
  shows a project OR the doc records that GCP is deferred and SQLite path is default.
- **Depends on:** nothing.
- **Effort:** S.
- **Fallback:** if `gcloud` auth is unavailable in-session, set `USE_BIGQUERY=false` and proceed
  entirely on SQLite; note it in README. GCP wiring becomes a documented post-session step.

### Phase 1 — Data layer (synthetic + real, schema, seed)
- **Goal:** a populated data store the rest of the system reads from.
- **Deliverables:**
  - `generate_synthetic.py`: produces projects across all 28 states × sectors (Roads, Education,
    Health, Water, Energy) × years (e.g. 2016–2024), with sanctioned/disbursed/utilized amounts,
    physical outcomes (km, schools, beds), and **intentional cross-source conflicts** on a subset
    (needed to exercise the Transparency Score). Amounts calibrated to realistic magnitudes
    (₹ crore). Also emit a **large** flat table (target 5–10M rows at district granularity) purely
    to feed the cudf benchmark.
  - 2–3 real government PDFs downloaded into `data/raw_pdfs/` (Union Budget expenditure vol, one
    state budget, one CAG report) — for genuine extraction in P2.
  - `data/seed/`: 5–8 hand-curated flagship demo projects (e.g. a real, recognizable expressway or
    metro line) with realistic scores + rationale, matching `schema.py`.
  - SQLite built and populated; BigQuery load script written (runs only if `USE_BIGQUERY=true`).
- **Acceptance:** SQLite has ≥ 500 projects + the large benchmark table; `data/seed/` renders a
  believable Project card; a query for rankings returns sensible ₹/km ordering.
- **Depends on:** P0.
- **Effort:** M.
- **Fallback:** if real PDFs can't be sourced quickly, generate 2–3 **synthetic PDFs** that mimic
  budget-document layout (so P2 extraction is still exercised); note substitution in README.

### Phase 2 — Extraction + Cross-Check (→ Transparency Score)
- **Goal:** turn source documents into structured figures and compute the Transparency Score.
- **Deliverables:**
  - `extract.py`: Document AI form/OCR parse of a PDF → structured claims (sanctioned, disbursed,
    utilized, outcome, dates, project id). **PyMuPDF + regex fallback** if Document AI is
    unavailable, behind the same function signature.
  - `crosscheck.py`: given ≥2 source rows for the same project, compute a **Transparency Score
    (0–100)** from figure agreement (see ARCHITECTURE for the formula), plus a list of specific
    conflicts ("Source A: ₹1,200cr vs Source B: ₹950cr").
- **Acceptance:** running extraction on a real PDF yields at least a few correct structured figures;
  a project with seeded conflicts gets a low Transparency Score and an itemized conflict list; a
  clean project scores high.
- **Depends on:** P1.
- **Effort:** M.
- **Fallback:** Document AI off → PyMuPDF path. If a specific PDF is too messy to parse in time,
  fall back to the synthetic structured rows for that project but keep ≥1 real PDF working
  end-to-end as proof.

### Phase 3 — Multi-agent debate pipeline (→ Justification Score) — the differentiator
- **Goal:** the judicial-style Red/Blue/Council pipeline on ADK + Vertex AI, producing cached
  verdicts.
- **Deliverables:**
  - `agents/red_team.py`, `blue_team.py`, `council.py`, `extraction_agent.py` — ADK agents with the
    prompt scaffolds from ARCHITECTURE §agents. Red argues excessive (grounded in benchmark rows),
    Blue argues justified (grounded in terrain/scale/inflation context), Council synthesizes both +
    the Transparency Score into a **Justification Score (0–100) + written rationale**, retaining the
    full transcript.
  - `run_debate.py`: one project → full transcript + verdict object.
  - `batch_score.py`: iterate projects → write verdict rows to cache (SQLite always; BigQuery if
    enabled). Idempotent; re-runnable; skips already-scored projects.
  - Model routing: Gemini 2.5 **Flash** for Red/Blue (high volume), **Pro** for Council (quality).
- **Acceptance:** for ≥5 projects, `batch_score.py` writes verdicts with non-trivial, calibrated
  rationale that references actual figures; language passes the responsible-AI check (no accusatory
  terms); transcript is replayable by the UI.
- **Depends on:** P1, P2 (needs benchmarks + Transparency Score as debate inputs). GCP auth for the
  live path.
- **Effort:** L.
- **Fallback:** if Vertex AI quota/auth blocks live calls in-session, run the pipeline against a
  **mocked LLM** (deterministic canned arguments) so the code path, schema, caching, and UI replay
  all work; swap to real Gemini when auth is ready. The seed data covers the demo either way.

### Phase 4 — NVIDIA cudf.pandas acceleration (evidence for the pitch)
- **Goal:** concrete, self-generated acceleration evidence + the rankings table.
- **Deliverables:**
  - `acceleration/cudf_benchmark.ipynb`: loads the large flat table from P1, runs the identical
    state×sector×year groupby/join/rank in (a) stock pandas and (b) `cudf.pandas` (via
    `%load_ext cudf.pandas`), times both, prints the speedup, and **writes the resulting `rankings`
    table** back out (CSV → loaded to the cache). Runs on **Google Colab free T4** (macOS has no
    NVIDIA GPU — this is mandatory, not optional).
  - A saved timing comparison (table + bar chart) for the deck's acceleration slide.
- **Acceptance:** notebook runs top-to-bottom on Colab T4; shows a clear speedup (target ≥10×) on a
  multi-million-row aggregation; the rankings it produces match what the API serves.
- **Depends on:** P1 (needs the large table).
- **Effort:** M.
- **Fallback:** if Colab GPU is unavailable at demo time, keep the saved screenshot from a prior run
  as the evidence; the rankings table also has a CPU-pandas code path so the app never depends on
  the GPU at serve time.

### Phase 5 — Backend API (online plane)
- **Goal:** a thin, fast, read-only API over the cache.
- **Deliverables:**
  - `api/main.py` (FastAPI) with endpoints per ARCHITECTURE §API contract: `GET /projects` (search
    + filters), `GET /projects/{id}` (scores + rationale + metadata), `GET /projects/{id}/debate`
    (transcript for replay), `GET /rankings` (state leaderboard by sector/year), `GET /stats`
    (homepage trending). Plus ONE `POST /projects/{id}/debate/live` (optional demo-only live re-run).
  - `api/db.py`: single data-access layer; BigQuery in prod, SQLite for demo, selected by config.
  - CORS enabled for the web dev server. Response models in `api/models.py`.
- **Acceptance:** `uvicorn api.main:app` serves; every endpoint returns seed/real data; OpenAPI docs
  load; search + filters + rankings return correct shapes the frontend expects.
- **Depends on:** P1 (data), ideally P3 (verdicts) but works on seed data alone.
- **Effort:** M.
- **Fallback:** none needed — this is low-risk. If BigQuery isn't wired, SQLite path is the default.

### Phase 6 — Frontend (React, India-first) — the biggest phase
- **Goal:** the five screens, built on a proper India-first design system, rendering real API data.
- **Deliverables (screens):** Home/Search · Project Score Card (twin gauges) · Debate Replay
  (Red/Blue/Council step-through) · State Rankings (table + India choropleth) · About/Methodology
  (the responsible-AI page). Full specs in `docs/UI_UX_DESIGN.md`.
- **Deliverables (system):** design tokens (neutral, non-partisan palette), `RupeeAmount` (lakh/crore
  Indian grouping), i18n scaffold with `en.json`/`hi.json` + language toggle, Devanagari-capable
  font, mobile-first responsive layouts, skeleton loaders, the component library
  (`ScoreGauge`, `TransparencyBadge`, `ProjectCard`, `RationalePanel`, `DebateColumn`,
  `VerdictBanner`, `RankingTable`, `IndiaChoropleth`, `LanguageToggle`).
- **Acceptance:** all five screens navigable; scores/rationale/debate/rankings render from the API;
  rupee amounts format the Indian way; language toggle switches static copy; layout holds on a phone
  viewport; every score has a **text label**, never color alone.
- **Depends on:** P5 (API). Can start against seed data before P3 finishes.
- **Effort:** L (largest).
- **Fallback:** if the choropleth is time-consuming, ship the ranking **table** first (choropleth is
  an enhancement). The user is supplying some React components — integrate those to save time; map
  them to the component specs in UI_UX_DESIGN.md.

### Phase 7 — Integration & demo assets
- **Goal:** one coherent, demoable system + the actual deck screenshots.
- **Deliverables:** end-to-end run (batch_score → API → UI) on the seed + a few real projects; the
  curated demo script (which project to search, where to click "watch debate live"); captured
  **screenshots** for Slide 7 (2×2 wireframe grid) and Slide 10 (prototype snapshots); the cudf
  timing image for the acceleration slide.
- **Acceptance:** a clean run-through matches the `agent.md` §9 demo narrative start to finish;
  screenshots are legible and on-brand.
- **Depends on:** P5, P6 (and P3/P4 where available).
- **Effort:** M.
- **Fallback:** if the live debate button isn't ready, demo the cached transcript replay (visually
  identical to the audience); note it.

### Phase 8 — Polish, responsible-AI surface, submission
- **Goal:** make it credible and submission-ready.
- **Deliverables:** About/Methodology page content (how scores are computed, explicit "this is not
  an accusation of wrongdoing" statement, data sources, limitations) · `README.md` (full run order,
  architecture diagram, env setup) · final deck screenshot handoff · a short "known limitations"
  note (synthetic data scope, early-stage extraction).
- **Acceptance:** a newcomer can clone, follow README, and run the demo; the responsible-AI framing
  is visible in-product, not just in the pitch.
- **Depends on:** all prior.
- **Effort:** S–M.
- **Fallback:** trim README to the minimum run commands if time is short; the Methodology page copy
  is the higher priority because it defends the project against the "is this defamatory?" question.

---

## 5. Cross-cutting requirements (apply to every phase)

1. **Responsible-AI language guard.** No accusatory vocabulary anywhere in generated or static text.
   Consider a tiny lint list (`corrupt`, `scam`, `loot`, `fraud`, `stolen`, ...) checked in
   `batch_score.py` output; flag violations. Scores are framed as reasoning aids.
2. **One schema, two stores.** `pipeline/schema.py` is the single source of truth; SQLite and
   BigQuery hold the same shapes; seed data and pipeline output are interchangeable.
3. **Never demo-depend on the cloud.** SQLite + seed data must render the full UI with the network
   off. Cloud is the scale story, not the demo dependency.
4. **Country abstraction.** Every project row carries a `country` field (default `IN`); currency and
   number formatting are keyed off it. India is the first country, not the only possible one — no
   hardcoded "India" assumptions in schema or formatting utilities.
5. **Two scores stay separate.** Justification and Transparency are computed, stored, and displayed
   independently. The UI must never merge them into one number.
6. **Idempotent batch jobs.** `batch_score.py` and loaders are safe to re-run.

---

## 6. Definition of Done (session-level)

- [x] React app runs locally and shows all five screens with real data from the API.
- [x] At least 5 projects carry a real (or mock-LLM, if auth deferred) debate transcript + both
      scores, replayable in the Debate screen. (All 859 projects scored; mock-LLM client used —
      Vertex AI auth deferred per user choice, see README "Going live on Google Cloud".)
- [x] At least one **real** government PDF is extracted end-to-end by `extract.py`. (CAG Report
      No. 19 of 2023, Dwarka Expressway figures — ₹7,287.29 cr, ₹250.77 cr/km vs ₹18.20 cr/km
      CCEA benchmark — all reproduced directly from the raw PDF text.)
- [x] `cudf_benchmark.ipynb` produces a timing comparison + the rankings table (on Colab T4).
      (Notebook written and validated as well-formed; actual execution requires the user to run
      it on a live Colab GPU session — cannot be executed from this environment.)
- [x] Deck screenshots for Slides 7 and 10 captured and legible. (`docs/screenshots/`, captured
      via Playwright against the real running app, zero console errors.)
- [x] Responsible-AI framing is visible in-product (About/Methodology) and no accusatory language
      appears in any output. (Lint gate enforced in `batch_score.py` and `generate_seed.py`;
      About page live at `/about`.)
- [x] README lets a newcomer reproduce the demo offline (SQLite path).

---

## 7. Open items to confirm before/while building

- GCP project id + region to put in `.env` (deferred per user; SQLite default until provided).
- Whether the user's supplied React components replace or augment the component specs in
  `docs/UI_UX_DESIGN.md` (map them when they arrive).
- Which 2–3 real PDFs to source (Union Budget expenditure volume + one state budget + one CAG
  report is the recommended trio).
- Final list of the 5–8 flagship demo projects for `data/seed/`.
