# Bharat Ledger

> Turning 60-page government budget PDFs into a 5-second, auditable verdict.

Built for the Google Cloud Gen AI Academy (APAC Edition) hackathon, track: **"Create a data
intelligence tool people would actually use."** See [`agent.md`](./agent.md) for the full product
concept and responsible-AI framing, [`PLAN.md`](./PLAN.md) for the phase-wise build plan, and
[`docs/`](./docs/) for architecture and design system detail.

## What it is

A dashboard where any citizen can search a government project and instantly see:
- **Justification Score** (0–100) — is the cost reasonable given terrain, scale, and comparable
  benchmarks? Produced by a judicial-style AI debate (Red Team argues excessive, Blue Team
  argues justified, a Council synthesizes both into a score + written rationale).
- **Transparency Score** (0–100) — do official sources even agree on the figures? Computed
  deterministically from cross-source disagreement, independent of the Justification Score.

Both scores ship with the full reasoning behind them — never a bare number. See
[`docs/DEMO_SCRIPT.md`](./docs/DEMO_SCRIPT.md) for a guided walkthrough with screenshots.

## Status

All 8 build phases complete for this session:

- [x] Phase 0 — Foundations & environment
- [x] Phase 1 — Data layer (859 projects: 853 synthetic + 6 hand-curated flagship, incl. one
      real project extracted from an actual CAG audit report)
- [x] Phase 2 — Extraction + Cross-Check (PyMuPDF-based; proven against a real 264-page PDF)
- [x] Phase 3 — Multi-agent debate pipeline (all 859 projects scored)
- [x] Phase 4 — NVIDIA cudf.pandas acceleration notebook (ready to run on Colab T4)
- [x] Phase 5 — Backend API (FastAPI, all endpoints tested)
- [x] Phase 6 — Frontend (React, 5 screens, bilingual EN/Hindi, India-first design system)
- [x] Phase 7 — Integration & demo assets (screenshots in `docs/screenshots/`)
- [x] Phase 8 — Polish & submission (this document)

## Architecture (one paragraph)

Two planes. **Offline** (batch, cached): PDFs → extraction → cross-source consistency check
(Transparency Score) → Red Team vs. Blue Team debate → Council verdict (Justification Score),
all written to a cache. **Online** (live, cheap): React → FastAPI → reads the cache only — no
LLM call in the normal request path, so the app scales to many users at near-zero marginal
cost. Full detail in [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

```
PDFs → Extraction → Cross-Check → Red/Blue Debate → Council Verdict → cache (SQLite/BigQuery)
                                                                            │
React UI ← FastAPI (read-only) ─────────────────────────────────────────────┘
```

## Quickstart (fully offline — no GCP credentials needed)

The app runs entirely offline by default: `USE_BIGQUERY=false`, `USE_VERTEX_AI=false`,
`USE_DOCUMENT_AI=false` in `.env`. All data is generated locally and served from SQLite.

```bash
# 1. Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # defaults already point at SQLite + mock scoring, no edits required

# 2. Build the dataset (takes ~1-2 minutes; the large table is ~6M rows)
python3 -m pipeline.generate_synthetic   # 853 synthetic projects + benchmarks + large district table
python3 -m pipeline.generate_seed        # 6 hand-curated flagship projects (incl. real Dwarka Expressway data)
python3 -m pipeline.build_db             # builds data/bharat_ledger.sqlite from the above
python3 -m pipeline.batch_score          # scores all synthetic projects via the debate pipeline

# 3. Run the API
uvicorn api.main:app --reload --port 8000

# 4. Run the frontend (separate terminal)
cd web
npm install
npm run dev
```

Open `http://localhost:5173`. Try searching "Dwarka" for the flagship real-data example.

## Going live on Google Cloud (optional)

```bash
gcloud auth application-default login
gcloud services enable documentai.googleapis.com --project personal-hackthon-tests
```

Then set `USE_VERTEX_AI=true` (and `USE_DOCUMENT_AI=true` if desired) in `.env` and re-run
`batch_score.py` — no code changes needed; `pipeline/agents/llm_client.py` swaps from the
rule-based mock to real Gemini calls via the same interface. `aiplatform.googleapis.com` and
`bigquery.googleapis.com` are already enabled on the `personal-hackthon-tests` project.

To run the NVIDIA acceleration benchmark: open `acceleration/cudf_benchmark.ipynb` in **Google
Colab** with a **T4 GPU runtime** (mandatory — RAPIDS/cudf cannot run on the local macOS dev
machine used for the rest of this project). Upload `data/synthetic/district_flat_large.parquet`
when prompted. The notebook produces a timing comparison and the authoritative `rankings` table.

## Repository layout

See [`PLAN.md`](./PLAN.md) §2 for the full target layout. Key entry points:

| Path | What |
|---|---|
| `pipeline/generate_synthetic.py` | Synthetic dataset generator (859 projects, benchmarks, large district table) |
| `pipeline/generate_seed.py` | 6 hand-curated flagship projects incl. real CAG-extracted data |
| `pipeline/extract.py` | PDF → structured figures (PyMuPDF; proven against a real 264-page government PDF) |
| `pipeline/crosscheck.py` | Deterministic Transparency Score |
| `pipeline/run_debate.py` / `batch_score.py` | The Red/Blue/Council debate pipeline (offline plane) |
| `pipeline/agents/llm_client.py` | Mock (default) vs. real Gemini client — same interface either way |
| `acceleration/cudf_benchmark.ipynb` | NVIDIA cudf.pandas acceleration benchmark (run on Colab T4) |
| `api/main.py` | FastAPI app (online plane, read-only) |
| `web/` | React frontend |
| `docs/ARCHITECTURE.md` | System design, data model, API contract, agent specs |
| `docs/UI_UX_DESIGN.md` | India-first design system + screen specs |
| `docs/DEMO_SCRIPT.md` | Guided walkthrough with screenshots |

## Known limitations (stated plainly, also visible in-app on the About page)

- One real government document (CAG Report No. 19 of 2023, Bharatmala Pariyojana Phase-I) backs
  the flagship Dwarka Expressway project; the remaining 853 synthetic projects are calibrated to
  plausible magnitudes, not verified real-world figures.
- PDF extraction (PyMuPDF/regex) is a fallback path — proven correct when scoped to a specific
  document section (see `pipeline/extract.py`'s `__main__` demo), but a bare whole-document
  keyword search can match the wrong project in a large multi-project report. Document AI
  (not yet enabled on the GCP project) is the more robust real-world path.
- Vertex AI / ADK live calls are deferred this session (no Application Default Credentials
  configured yet) — all 859 projects were scored via the deterministic rule-based mock client,
  which follows the same reasoning shape a real Gemini call would (ARCHITECTURE.md §4), but is
  not itself an LLM.
- The NVIDIA cudf.pandas benchmark requires manually running the notebook on Google Colab (T4
  GPU) — it cannot be executed from this environment (no NVIDIA GPU on macOS).
- Coverage is India-only at launch; the schema and formatting utilities are built to extend to
  other countries without a rewrite (`country` field throughout, locale-aware number formatting).
# BharatLedger
