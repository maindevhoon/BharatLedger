# Bharat Ledger — System Architecture

> Companion to [`../PLAN.md`](../PLAN.md) and [`../agent.md`](../agent.md). This document specifies
> the system design, data model, API contract, and agent behaviour precisely enough to implement
> from. When PLAN.md and this doc disagree, this doc wins on technical detail; agent.md wins on
> product intent and the responsible-AI framing.

---

## 1. System overview: two planes

Bharat Ledger separates a slow, expensive **offline plane** (the AI does the hard reasoning once
per project and caches it) from a fast, cheap **online plane** (users only read cached results).

```
                         OFFLINE PLANE (batch)                          ONLINE PLANE (live)
  ┌───────────────────────────────────────────────────────┐   ┌──────────────────────────────┐
  │  raw_pdfs/ ──► extract.py ──► structured figures        │   │  React (web/) ─┐             │
  │                    │                                    │   │                │ HTTP        │
  │                    ▼                                    │   │                ▼             │
  │            crosscheck.py ──► Transparency Score         │   │        FastAPI (api/)         │
  │                    │                                    │   │                │ read-only   │
  │  benchmarks ──►    ▼                                    │   │                ▼             │
  │            run_debate.py (ADK)                          │   │   data store (BigQuery │      │
  │              ├─ Red Team  (Gemini Flash)                │   │        or SQLite mirror)     │
  │              ├─ Blue Team (Gemini Flash)                │   │                ▲             │
  │              └─ Council   (Gemini Pro) ──► Justification │   └────────────────┼─────────────┘
  │                    │        Score + rationale + transcript                    │
  │                    ▼                                                          │
  │            batch_score.py ──► cache rows ───────────────────────────────────►│ (writes)
  │                                                                              │
  │  large flat table ──► cudf_benchmark.ipynb (Colab T4) ──► rankings table ────►│
  └───────────────────────────────────────────────────────┘
```

**Design consequence:** at serve time there is no LLM in the request path (except the optional
`/debate/live` demo endpoint). This is what makes "scales to millions of users cheaply" literally
true, and it is the answer to any judge who asks about cost/latency at scale.

---

## 2. Data model (canonical — `pipeline/schema.py`)

All entities below are defined once as pydantic models / dataclasses in `pipeline/schema.py` and
imported everywhere. SQLite tables and BigQuery tables mirror these exactly. Seed data and pipeline
output are the same shapes (so one can replace the other with no code change).

### 2.1 `Project`
| field | type | notes |
|---|---|---|
| `project_id` | str (PK) | stable slug, e.g. `in-hr-roads-dwarka-expressway-2023` |
| `country` | str | ISO-2, default `IN`. **Never hardcode India elsewhere — read this.** |
| `state` | str | e.g. `Haryana` |
| `sector` | str | enum: `roads`, `education`, `health`, `water`, `energy` |
| `name` | str | human-readable project name |
| `year` | int | fiscal year start, e.g. `2023` for FY23–24 |
| `sanctioned_cr` | float | ₹ crore |
| `disbursed_cr` | float | ₹ crore |
| `utilized_cr` | float | ₹ crore |
| `outcome_value` | float | physical output quantity |
| `outcome_unit` | str | `km`, `schools`, `beds`, `mld`, `mw` |
| `cost_per_unit_cr` | float | derived: `utilized_cr / outcome_value` |
| `description` | str | short context (terrain, scope) — feeds the debate |

### 2.2 `SourceDocument`
| field | type | notes |
|---|---|---|
| `doc_id` | str (PK) | |
| `project_id` | str (FK) | |
| `source_type` | str | `union_budget`, `state_budget`, `cag_report`, `synthetic` |
| `title` | str | |
| `url_or_path` | str | provenance |
| `claimed_sanctioned_cr` | float | as this document reports it |
| `claimed_disbursed_cr` | float | |
| `claimed_utilized_cr` | float | |
| `extracted_at` | str (ISO) | |
| `extraction_method` | str | `document_ai` or `pymupdf` |

> Cross-source conflicts arise when two `SourceDocument` rows for one `project_id` disagree on a
> claimed figure. That disagreement is the raw material for the Transparency Score.

### 2.3 `Benchmark`
| field | type | notes |
|---|---|---|
| `benchmark_id` | str (PK) | |
| `country` | str | |
| `sector` | str | |
| `outcome_unit` | str | |
| `terrain` | str | `plain`, `hilly`, `urban`, `coastal` — cost driver |
| `median_cost_per_unit_cr` | float | the "is this reasonable?" yardstick |
| `p25_cost_per_unit_cr` | float | |
| `p75_cost_per_unit_cr` | float | |
| `source_note` | str | where the benchmark came from |

### 2.4 `Verdict` (the cached output of the offline plane)
| field | type | notes |
|---|---|---|
| `project_id` | str (PK/FK) | one verdict per project |
| `justification_score` | int | 0–100 |
| `justification_band` | str | `well_justified` (75–100), `partially_justified` (45–74), `needs_review` (0–44) |
| `justification_rationale` | str | plain-language, calibrated, cites figures |
| `transparency_score` | int | 0–100 |
| `transparency_band` | str | `consistent`, `minor_conflicts`, `sources_conflict` |
| `transparency_conflicts` | json | list of `{field, source_a, value_a, source_b, value_b, delta_cr}` |
| `debate_transcript` | json | ordered turns, see §4.4 |
| `scored_at` | str (ISO) | |
| `model_versions` | json | `{red, blue, council}` model ids for auditability |

### 2.5 `RankingRow` (produced by the cudf notebook)
| field | type | notes |
|---|---|---|
| `country` · `sector` · `year` | | grouping key |
| `state` | str | |
| `median_cost_per_unit_cr` | float | |
| `rank` | int | 1 = most efficient (lowest cost/unit) |
| `efficiency_score` | int | 0–100, normalized within the group |

---

## 3. Scoring formulas (deterministic parts)

The LLM writes rationale and the final Justification Score, but two pieces are deterministic so they
are defensible and reproducible:

### 3.1 Transparency Score (fully deterministic — `crosscheck.py`)
For a project with ≥2 source documents, for each shared figure `f` in {sanctioned, disbursed,
utilized}:
```
rel_disagreement(f) = (max_source(f) - min_source(f)) / max(min_source(f), 1)
```
```
transparency_score = round(100 * (1 - clamp(mean(rel_disagreement over available f), 0, 1)))
```
Bands: `consistent` ≥ 85 · `minor_conflicts` 60–84 · `sources_conflict` < 60. Single-source projects
get `transparency_score = None` and band `single_source` (UI shows "only one source available",
not a low score — absence of conflict evidence is not the same as consistency).

### 3.2 Justification: deterministic prior + LLM adjustment
Compute a **benchmark ratio** first, as grounding fact given to the agents and shown in the UI:
```
ratio = project.cost_per_unit_cr / benchmark.median_cost_per_unit_cr   (matched on country+sector+terrain+unit)
```
- `ratio ≤ 1.1` → prior leans "well justified"
- `1.1 < ratio ≤ 1.8` → prior leans "partially justified"
- `ratio > 1.8` → prior leans "needs review"

The Council agent receives this ratio + both debates + the Transparency Score and returns the final
0–100 score. The prior exists so the LLM cannot wander far from the arithmetic without explicitly
justifying it in the rationale (e.g. terrain premium). **The number is always accompanied by
reasoning; never a bare score.**

---

## 4. Agents (ADK on Vertex AI)

All agents run in the **offline plane** via ADK. Model routing: **Gemini 2.5 Flash** for Extraction,
Red, Blue (volume); **Gemini 2.5 Pro** for Council (reasoning quality). Every agent prompt embeds
the responsible-AI constraint.

### 4.0 Shared system preamble (prepend to every agent)
```
You are an analyst for Bharat Ledger, a public-spending TRANSPARENCY tool. You help citizens
reason about whether government spending is reasonable. You are NOT an accuser and NOT a court.
Hard rules:
- Never use the words corrupt, corruption, scam, loot, fraud, stolen, embezzled, or synonyms.
- Never assert wrongdoing or intent. You assess reasonableness of COST against evidence only.
- Every claim must cite a specific figure, benchmark, or contextual factor you were given.
- If evidence is insufficient, say so plainly rather than speculate.
- Output must be calibrated: "exceeds the median benchmark by X%", "partially justified", etc.
```

### 4.1 Extraction Agent (`agents/extraction_agent.py`)
- **Input:** raw text/OCR of one source document + the target field list.
- **Job:** return structured `SourceDocument` figures as strict JSON. Prefer Document AI's parsed
  fields; use the LLM to disambiguate/normalize (units, ₹ crore vs lakh, fiscal-year labels).
- **Output:** JSON conforming to `SourceDocument`.

### 4.2 Red Team (`agents/red_team.py`) — argues the spend is EXCESSIVE
- **Input:** project figures, the benchmark ratio + comparable projects (from `Benchmark` and peer
  `Project` rows), any cost overruns/delays implied by disbursed-vs-utilized gaps.
- **Job:** make the strongest evidence-grounded case that the cost is high. Must cite comparables.
- **Output:** JSON `{stance:"excessive", arguments:[{claim, evidence, figure}], confidence}`.

### 4.3 Blue Team (`agents/blue_team.py`) — argues the spend is JUSTIFIED
- **Input:** same project + `description` (terrain, urban density, scope inclusions like tunnels/
  elevated sections), inflation over the project years, local cost factors.
- **Job:** strongest evidence-grounded case that the cost is reasonable given context.
- **Output:** JSON `{stance:"justified", arguments:[{claim, evidence, figure}], confidence}`.

### 4.4 Council (`agents/council.py`) — synthesizes → verdict
- **Input:** Red output, Blue output, the deterministic benchmark ratio, the Transparency Score.
- **Job:** weigh both sides, produce `justification_score` (0–100), `justification_band`, and a
  ≤120-word `justification_rationale` that references the strongest points from each side and the
  benchmark ratio. Must remain within the responsible-AI rules.
- **Output:** JSON verdict fields (see `Verdict`) **plus** `debate_transcript`:
```json
{
  "turns": [
    {"agent":"red","stance":"excessive","arguments":[...] },
    {"agent":"blue","stance":"justified","arguments":[...] },
    {"agent":"council","verdict":"partially_justified","score":68,"rationale":"..."}
  ]
}
```
This transcript is exactly what the Debate Replay screen renders.

### 4.5 Mock-LLM fallback
`run_debate.py` accepts an injected LLM client. If Vertex AI auth/quota is unavailable in-session,
a deterministic mock returns canned-but-plausible arguments keyed off the benchmark ratio, so the
schema, caching, and UI replay are fully exercised. Swap to real Gemini by changing the client.

---

## 5. API contract (`api/` — FastAPI, read-only)

Base URL `/api/v1`. All responses JSON. Data source selected by `USE_BIGQUERY` config; identical
shapes either way.

| Method | Path | Query | Returns |
|---|---|---|---|
| GET | `/projects` | `q, state, sector, year, country, limit, offset` | paginated `Project` summaries + both scores/bands |
| GET | `/projects/{project_id}` | — | full `Project` + `Verdict` (scores, bands, rationale, conflicts) |
| GET | `/projects/{project_id}/debate` | — | `debate_transcript` for replay |
| GET | `/rankings` | `sector, year, country` | ordered `RankingRow[]` |
| GET | `/stats` | `country` | homepage: counts, trending projects, score distribution |
| POST | `/projects/{project_id}/debate/live` | — | **demo-only**: re-runs the pipeline live and streams turns (guard behind a flag) |

- **CORS:** allow the web dev origin.
- **Errors:** RFC-7807-ish `{error, detail}`; 404 for unknown project.
- **Response models:** defined in `api/models.py`, mirroring §2. The frontend's TypeScript types are
  generated from / kept in sync with these.

---

## 6. Storage: BigQuery + SQLite mirror

- **Tables** (both stores): `projects`, `source_documents`, `benchmarks`, `verdicts`, `rankings`.
- **`api/db.py`** exposes one interface (`get_project`, `search_projects`, `get_debate`,
  `get_rankings`, `get_stats`) with two backends chosen by config. **Default = SQLite** so the demo
  runs with no network.
- **`load_bigquery.py`** pushes the same rows to BigQuery when `USE_BIGQUERY=true`. BigQuery is the
  production/scale story and the home of the cudf-produced `rankings` table; SQLite is the always-on
  demo mirror.
- **Why both:** judges reward a real BigQuery integration, but a live demo must never fail because a
  cloud call timed out. Same schema, two stores, config switch.

---

## 7. Acceleration (`acceleration/cudf_benchmark.ipynb`)

- **Where:** Google Colab, free **T4 GPU** runtime (macOS dev machine has no NVIDIA GPU; RAPIDS
  cannot run locally — this is a hard constraint, see PLAN §Phase 4).
- **What:** load the P1 large flat table (target 5–10M district-level rows), then run the *identical*
  aggregation twice:
  1. stock `pandas` (baseline timing),
  2. `%load_ext cudf.pandas` then re-run the same code (GPU timing).
  The aggregation = groupby(country, sector, year, state) → median cost/unit → rank → normalize to
  `efficiency_score`. Emit `rankings` as CSV for loading into the cache.
- **Output for the deck:** a timing table + bar chart (pandas vs cudf) showing the speedup (target
  ≥10×), and confirmation the two engines produce identical rankings (correctness, not just speed).
- **Serve-time independence:** the app reads the *pre-computed* rankings table; the GPU is only used
  to build it, never in the request path. A CPU-pandas code path exists as a fallback so nothing
  serve-time depends on a GPU.

---

## 8. Country abstraction (India first, not India only)

- Every `Project`/`Benchmark`/`RankingRow` carries `country`. Currency symbol, number grouping
  (Indian lakh/crore vs Western thousands/millions), and default language are resolved from a small
  `countries` config keyed by ISO-2. India (`IN`) ships first with `₹` + lakh/crore grouping +
  en/hi languages. Adding a country = adding a config entry + benchmarks + data, not a code rewrite.
- The frontend `RupeeAmount`/number formatter reads the active country's locale rules; it is not
  hardcoded to India even though India is the only populated country at launch.

---

## 9. Non-functional requirements

- **Idempotency:** `batch_score.py`, `load_bigquery.py`, and the notebook's export are safe to
  re-run; already-scored projects are skipped unless `--force`.
- **Auditability:** `Verdict.model_versions` records which model produced each part.
- **Responsible-AI enforcement:** a post-generation check scans rationale/arguments for the banned
  vocabulary list and flags any hit before caching. This is a correctness gate, not a nicety.
- **Offline-first demo:** with `USE_BIGQUERY=false` and no network, the full UI must render from
  SQLite + seed data.
- **Separation of scores:** Justification and Transparency are never combined into a single number
  at any layer (pipeline, API, or UI).
