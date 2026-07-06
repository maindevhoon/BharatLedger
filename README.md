# Bharat Ledger

Turning 60-page government budget PDFs into a 5-second, auditable spend-reasonableness score.

## What it is

Bharat Ledger lets anyone search a government infrastructure project and instantly see two
independent scores:

- **Justification Score** (0–100) — is the cost reasonable given terrain, scale, and comparable
  benchmarks? Produced by an adversarial AI debate: one side argues the cost is excessive, one
  argues it is justified, and a third synthesizes both into a score with a written rationale.
- **Transparency Score** (0–100) — do official sources actually agree on the figures? Computed
  deterministically from cross-source disagreement, entirely independent of the Justification
  Score — a project can be well-justified with conflicting sources, or vice versa.

Every score ships with the reasoning behind it — never a bare number. The flagship example
(Dwarka Expressway) uses figures extracted directly from a real CAG audit report.

## Architecture

Two planes. **Offline** (batch, cached): source PDFs are parsed into structured figures, checked
for cross-source consistency, then run through a Red Team / Blue Team / Council debate that
produces the final score and rationale — all written to a cache. **Online** (live): the API only
ever reads that cache, so there's no LLM call in the normal request path and the app scales to
many users at near-zero marginal cost.

```
PDFs → Extraction → Cross-Check → Red/Blue Debate → Council Verdict → cache (SQLite/BigQuery)
                                                                            │
React UI ← FastAPI (read-only) ─────────────────────────────────────────────┘
```

A separate NVIDIA cudf.pandas notebook (`acceleration/cudf_benchmark.ipynb`, run on a GPU
runtime) recomputes the state efficiency rankings across a multi-million-row dataset and feeds
the result back into the same cache.

## Quickstart

The app runs entirely offline by default — no cloud credentials required.

```bash
# Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Build the dataset
python3 -m pipeline.generate_synthetic
python3 -m pipeline.generate_seed
python3 -m pipeline.build_db
python3 -m pipeline.batch_score

# API
uvicorn api.main:app --reload --port 8000

# Frontend (separate terminal)
cd web
npm install
npm run dev
```

Open `http://localhost:5173` and search "Dwarka" for the flagship example.

## Going live on Google Cloud

Set `USE_VERTEX_AI=true` (and `USE_DOCUMENT_AI=true` if desired) in `.env`, authenticate with
`gcloud auth application-default login`, and re-run `batch_score.py` — no code changes needed;
the debate agents swap from a rule-based fallback to real Gemini calls via the same client
interface.

## Repository layout

| Path | What |
|---|---|
| `pipeline/` | Data generation, PDF extraction, cross-source consistency check, and the debate pipeline (offline plane) |
| `pipeline/agents/` | Red Team / Blue Team / Council agents, with a rule-based fallback client and a real Gemini client behind one interface |
| `acceleration/` | NVIDIA cudf.pandas acceleration benchmark |
| `api/` | FastAPI app (online plane, read-only) |
| `web/` | React frontend |
| `data/` | Seed and synthetic datasets, plus the source PDFs backing the flagship project |

## Known limitations

- One real government document (a CAG audit report) backs the flagship Dwarka Expressway
  project; the remainder of the dataset is synthetic, calibrated to plausible magnitudes rather
  than verified real-world figures.
- PDF extraction uses a keyword/regex fallback; it is accurate when scoped to a document
  section but can mismatch in large multi-project reports without a narrower scope. Document AI
  is the more robust path for production use.
- The debate pipeline defaults to a deterministic rule-based client; enabling Vertex AI requires
  Google Cloud credentials as described above.
- The NVIDIA acceleration benchmark requires a CUDA-capable GPU (e.g. via Google Colab) and is
  not run automatically as part of the app.
- Coverage is India-first; the schema and formatting are built to extend to other countries.
