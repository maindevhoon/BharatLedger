# Bharat Ledger — Demo Script

Curated walkthrough for the live demo, following the narrative in [`agent.md`](../agent.md) §9.
Screenshots referenced below are in [`screenshots/`](./screenshots/), captured end-to-end from
the running app (PLAN.md Phase 7).

## Setup

```bash
source .venv/bin/activate
uvicorn api.main:app --port 8000 &
cd web && npm run dev
```

Open `http://localhost:5173`.

## Walkthrough

1. **Open on the problem.** Mention: the CAG Report No. 19 of 2023 on Bharatmala Pariyojana
   Phase-I is 264 pages. No citizen will ever read it end to end — but it's the actual source
   for the demo's flagship project.

2. **Home screen** (`screenshots/1_home.png`). Search for "Dwarka" or click the flagship card
   directly. Point out: two independent scores per project card, never blended.

3. **Project Score Card** (`screenshots/2_project.png`) — `/project/in-hr-roads-dwarka-expressway-2018`.
   - Justification Score: **22/100 — Needs review**. Rationale cites the real CAG-audited
     figures directly: ₹250.77 cr/km actual vs ₹18.20 cr/km CCEA-approved benchmark (13.8x).
   - Transparency Score: **99 — Consistent**. Explicitly call out that this project has *both*
     a low Justification Score *and* a high Transparency Score — proving the two are genuinely
     independent, not just one score with two labels.

4. **Debate Replay** (`screenshots/3_debate.png`) — click "Watch the AI debate". This is the
   "how it actually works" reveal: Red Team cites the real overrun figures, Blue Team argues the
   14-lane elevated/urban-terrain premium, Council synthesizes both into the final score and
   rationale. Optionally click "Run live" to show the pipeline recompute in real time (note: the
   live path uses the same rule-based scoring engine as the cached batch — see
   `pipeline/agents/llm_client.py` — so its score may differ slightly from the hand-curated seed
   narrative shown by default; both are legitimate, just from different authoring passes).

5. **A low-transparency example.** Search "Kaleshwaram" — Transparency Score **58 — Sources
   conflict**, with itemized conflicts (sanctioned/disbursed/utilized figures differ across the
   two illustrative sources). This demonstrates the system catches data-quality issues
   independent of any cost judgment.

6. **State Rankings** (`screenshots/4_rankings.png`) — switch Sector/Year, point out the
   acceleration note: this table is the *output* of the NVIDIA cudf.pandas benchmark
   (`acceleration/cudf_benchmark.ipynb`), recomputed across a 6M-row synthetic district-level
   table in a fraction of the time stock pandas takes (see the notebook's speedup chart).

7. **About/Methodology** (`screenshots/5_about.png`) — close on the responsible-AI framing:
   this tool never issues a verdict of wrongdoing; it arms citizens with legible reasoning.

8. **Bilingual** (`screenshots/6_home_hindi.png`) — toggle EN/हिं on any screen to show the
   Hindi UI, reinforcing "built for India first."

## Known talking points if asked

- **"Is this real data?"** One flagship project (Dwarka Expressway) uses figures extracted
  directly from a real CAG audit report (`data/raw_pdfs/cag_report_19_2023_bharatmala.pdf`);
  the rest of the 859-project dataset is synthetic but calibrated to plausible magnitudes —
  stated plainly on the About page.
- **"Does this scale?"** Yes — the expensive multi-agent debate runs once per project, offline,
  and is cached; the live app only ever reads cached rows (zero LLM calls at serve time, except
  the optional demo-only "Run live" button).
- **"Why not just show one score?"** Because "is this reasonable" and "do sources agree" are
  different questions — conflating them would hide exactly the cases (like Kaleshwaram) where
  the real story is data quality, not cost.
