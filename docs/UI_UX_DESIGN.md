# Bharat Ledger — India-First UI/UX Design System

> Companion to [`../PLAN.md`](../PLAN.md) and [`ARCHITECTURE.md`](./ARCHITECTURE.md). This document
> defines the design language, screen layouts, and component specs for the React frontend (`web/`).
> It is written so that (a) an implementer can build screens without guessing, and (b) the user's
> own supplied React components can be mapped onto named slots rather than discarded.
>
> **Design intent in one line:** it should feel like a trustworthy, modern Indian public-service
> product — calm, neutral, legible on a cheap phone over patchy 4G, and unmistakably *for India* —
> while being structured so more countries slot in later.

---

## 1. Design principles

1. **Neutral, non-partisan by construction.** This tool assesses *cost reasonableness*, not
   politics. The palette deliberately **avoids party-coded colors** (no saffron-dominant or
   green-dominant themes that read as BJP/Congress/regional-party alignment). Primary brand is a
   calm **indigo/teal**, with **amber** for caution and restrained green/red only inside data
   viz — never as page-level political signalling.
2. **Never color alone.** Every score, band, and flag carries a **text label** and often an icon.
   This serves accessibility (color-blind users, ~8% of Indian men) AND reinforces the
   responsible-AI stance: a red dot could be read as an accusation; "Needs review — cost is 1.8×
   the benchmark" cannot be misread.
3. **Mobile-first, low-bandwidth-first.** Most users arrive on a mid-range Android phone. Design the
   phone layout first, scale up to desktop. Skeleton loaders, lazy images, no heavy hero videos.
4. **Indian number sense.** Money is shown in **lakh/crore with Indian digit grouping**
   (`₹1,23,456 cr`, `₹12.5 lakh`), never `$1.2M`. This is a first-glance trust signal.
5. **Bilingual from day one.** English/Hindi toggle with i18n scaffolding; Devanagari-capable type.
   Structured so more Indian languages (Tamil, Bengali, Marathi, Telugu…) are added as locale files.
6. **Calm information density.** Budgets are intimidating; the UI's job is to *reduce* anxiety. Lots
   of whitespace, one primary idea per screen, progressive disclosure (summary → details → debate).

---

## 2. Design tokens

### 2.1 Color
```
/* Brand — calm, neutral, trustworthy (NOT party-coded) */
--bl-indigo-700:  #2B3A67   /* primary brand, headers */
--bl-indigo-600:  #34478A
--bl-teal-500:    #0E8F8F   /* primary action / links */
--bl-teal-050:    #E6F4F4   /* teal tint surfaces */

/* Neutrals — the page is mostly these */
--bl-ink-900:     #1A1C21   /* headings */
--bl-ink-600:     #4A4E57   /* body */
--bl-ink-400:     #8A8F99   /* secondary */
--bl-surface:     #FFFFFF
--bl-bg:          #F7F8FA   /* app background */
--bl-border:      #E5E7EB

/* Data-viz semantics — used ONLY inside scores/charts, always with a text label */
--bl-good-600:    #2E7D5B   /* well justified / consistent  */
--bl-good-050:    #E8F3EE
--bl-warn-600:    #B7791F   /* partially justified / minor  (amber, not red) */
--bl-warn-050:    #FBF3E2
--bl-review-600:  #B0413E   /* needs review / sources conflict (muted brick, not alarm-red) */
--bl-review-050:  #F7E9E8

/* Debate sides — intentionally cool/neutral, not red-vs-blue politics */
--bl-red-team:    #A65A4E   /* "argues excessive" — terracotta, muted */
--bl-red-050:     #F6EAE7
--bl-blue-team:   #3E6690   /* "argues justified" — slate blue, muted */
--bl-blue-050:    #E9EFF6
--bl-council:     #6B4E9E   /* synthesis — deep violet (neutral authority) */
--bl-council-050: #EEE9F6

/* APAC gradient — reserved for the top brand strip ONLY, echoing the deck */
--bl-apac-gradient: linear-gradient(90deg, #FF7A2F 0%, #FF477E 100%);
```
> Rationale on the "red/blue team" colors: they are muted terracotta/slate, chosen so the debate
> reads as two analysts, not two political camps. The alarm-red is deliberately downgraded to a
> muted brick and only ever appears with the words "Needs review".

### 2.2 Type
- **Font:** a Devanagari-capable, open-source family. Primary: **"Mukta"** or **"Hind"** (both
  designed for Devanagari + Latin, by Indian Type Foundry) for UI; fallback `Inter`, system-ui.
  Headings may use **"Tiro Devanagari"** for a more editorial feel if desired.
- **Scale (mobile → desktop):** display 28/36 · h1 22/28 · h2 18/22 · body 15/16 · caption 13.
- **Numerals:** tabular figures for all money/score columns so tables align.

### 2.3 Spacing / shape
- 4px base grid; card radius 16px; button radius 12px; soft shadow `0 1px 3px rgba(0,0,0,.08)`.
- Touch targets ≥ 44px. Content max-width 1120px on desktop; single-column on phone.

---

## 3. Global chrome

- **Top bar:** thin **APAC gradient** strip; left = "Bharat Ledger" wordmark (with a small
  ledger/scales glyph); center (desktop) = search; right = `LanguageToggle` (EN | हिं) + nav
  (Search · Rankings · About).
- **Bottom nav (mobile only):** Search · Rankings · About — thumb-reachable.
- **Footer:** one-line responsible-AI disclaimer (see §7) + "Data sources" link + country selector
  (India selected; others "coming soon").

---

## 4. Screens

Each screen: purpose, layout (mobile then desktop deltas), components used, and the exact copy tone.

### 4.1 Home / Search  — `pages/Home.tsx`
- **Purpose:** ask one question, invite one action.
- **Layout (mobile):**
  1. Hero headline: **"Is this public spending reasonable?"** subline *"Search any government
     project. See the reasoning, not just the number."*
  2. Big rounded search bar — placeholder *"Try 'Dwarka Expressway' or 'schools in Bihar'"*.
  3. Filter chips (horizontal scroll): All States · Roads · Education · Health · Water · Energy.
  4. **"Trending"** section: 3–6 `ProjectCard`s.
  5. A slim "How scoring works" strip linking to About (builds trust before they judge a score).
- **Desktop deltas:** hero centered, trending in a 3-up grid.
- **Components:** `SearchBar`, `FilterChips`, `ProjectCard`, `LanguageToggle`.

### 4.2 Project Score Card — `pages/Project.tsx`  ← most important screen
- **Purpose:** deliver the two scores + the reasoning, calmly and unmistakably separated.
- **Layout (mobile, top→bottom):**
  1. Breadcrumb + project name + metadata row (`RupeeAmount` sanctioned · State · Sector · FY).
  2. **Two side-by-side score cards** (stack on narrow phones):
     - **Justification** — `ScoreGauge` (0–100, banded color) + band label
       ("Partially justified") + the benchmark-ratio fact ("≈1.8× the median cost per km").
     - **Transparency** — `TransparencyBadge` ("Sources conflict" / "Consistent" / "Only one
       source") + a one-line count ("2 official sources report different figures").
     > These two are visually distinct blocks with a labeled divider — the UI must telegraph
     > "these are two different questions". Never a single blended score.
  3. **`RationalePanel`** — "Why this score" — 2–4 plain-language bullets citing figures.
  4. **Conflicts list** (if any) — `ConflictRow`s: "Sanctioned — Union Budget ₹9,000 cr vs CAG
     ₹9,250 cr (Δ ₹250 cr)".
  5. Primary button: **"Watch the AI debate →"** (to 4.3). Secondary: **"Share"** (generates a
     shareable card — social is the citizen-empowerment channel from agent.md §3).
- **Components:** `ScoreGauge`, `TransparencyBadge`, `RationalePanel`, `ConflictRow`, `RupeeAmount`,
  `ShareButton`.

### 4.3 Debate Replay — `pages/Debate.tsx`  ← the differentiator
- **Purpose:** make the multi-agent reasoning visible and legible; this is the "oh, that's clever"
  moment.
- **Layout:**
  1. Project header (compact).
  2. **Two columns** (stacked on mobile, side-by-side on desktop):
     - Left `DebateColumn` (terracotta): **"Red Team — argues the cost is high"**, argument cards
       each with claim + cited figure/benchmark.
     - Right `DebateColumn` (slate): **"Blue Team — argues the cost is justified"**, same shape.
  3. Full-width **`VerdictBanner`** (violet): **"Council verdict"** + Justification Score + the
     ≤120-word rationale.
  4. **Step-through control:** a "Play" affordance that reveals turns in sequence (Red → Blue →
     Council) for the live demo, plus a caption *"Powered by multi-agent reasoning on Vertex AI +
     ADK."*
  5. Optional (demo flag): **"Run live"** hits `POST /debate/live` and streams turns in real time.
- **Components:** `DebateColumn`, `ArgumentCard`, `VerdictBanner`, `PlayStepper`.

### 4.4 State Rankings — `pages/Rankings.tsx`
- **Purpose:** the comparative "how does my state do?" view; also the acceleration story's payoff.
- **Layout:**
  1. Controls: Sector dropdown · Year dropdown · (Country selector — India).
  2. **`IndiaChoropleth`** — states shaded by efficiency score (using the never-color-alone rule:
     tap a state → label with rank + ₹/unit). Muted sequential scale, not political colors.
  3. **`RankingTable`** — Rank · State · ₹ crore / unit · Efficiency score (color-coded cell **with
     the number**). Sortable; tabular numerals.
  4. Caption noting the ranking is recomputed over millions of rows via GPU-accelerated aggregation
     (ties the slide's acceleration claim to something the user can see).
- **Components:** `IndiaChoropleth`, `RankingTable`, `Dropdown`.
- **Fallback:** table ships first; choropleth is an enhancement (PLAN §Phase 6 fallback).

### 4.5 About / Methodology — `pages/About.tsx`  ← the responsible-AI surface
- **Purpose:** defend the project's integrity in-product. This is not filler; it is the answer to
  "could this be defamatory / cause harm?"
- **Content:**
  - **What this is / is not:** "Bharat Ledger helps you reason about whether public spending is
    reasonable. It does **not** allege corruption, wrongdoing, or intent. Scores are decision aids,
    not verdicts."
  - **How the two scores are computed** (plain-language version of ARCHITECTURE §3, incl. the
    benchmark ratio and the source-agreement formula).
  - **How the debate works** (Red/Blue/Council, and that a human should read the reasoning).
  - **Data sources & limitations** (synthetic-augmented at this stage; extraction is early; more
    states/countries coming).
  - **Language & accessibility** commitments.

---

## 5. Component library (specs — map the user's React components onto these)

> Each component is a named slot. If the user supplies an equivalent, adapt props to this contract
> rather than rebuilding. All components are country-aware via context (currency/locale), never
> hardcoded to India.

| Component | Key props | Notes |
|---|---|---|
| `ScoreGauge` | `value:0-100`, `band`, `label`, `caption` | circular/arc gauge; band → color token; **always renders the numeric value + text band**. |
| `TransparencyBadge` | `band`, `conflictCount`, `singleSource:bool` | pill; distinct visual from ScoreGauge so the two scores never look interchangeable. |
| `ProjectCard` | `project`, `justification`, `transparency` | list/grid card: name, state·sector·FY, mini gauge, transparency pill. |
| `RationalePanel` | `bullets:string[]`, `title` | "Why this score"; each bullet should contain a figure. |
| `ConflictRow` | `field`, `sourceA`, `valueA`, `sourceB`, `valueB`, `deltaCr` | renders one cross-source disagreement with `RupeeAmount`. |
| `DebateColumn` | `side:"red"|"blue"`, `heading`, `arguments[]` | muted terracotta/slate; heading states the stance in plain words. |
| `ArgumentCard` | `claim`, `evidence`, `figure` | one argument; figure is emphasized. |
| `VerdictBanner` | `score`, `band`, `rationale` | violet council banner; full width. |
| `RankingTable` | `rows:RankingRow[]`, `sortBy` | tabular numerals; color-coded cells **with numbers**. |
| `IndiaChoropleth` | `metric`, `rows`, `onSelectState` | SVG/topojson India map; muted sequential scale; tap → label. |
| `RupeeAmount` | `crore` or `raw`, `country` | Indian grouping + lakh/crore; the canonical money renderer. |
| `LanguageToggle` | `lang`, `onChange` | EN | हिं; swaps i18n locale. |
| `SearchBar`, `FilterChips`, `Dropdown`, `ShareButton`, `PlayStepper`, `SkeletonLoader` | — | supporting UI. |

### 5.1 `RupeeAmount` behaviour (get this exactly right)
- Input in ₹ crore (schema unit). Display rules:
  - ≥ 1 crore → `₹X,XX,XXX cr` (Indian grouping on the crore figure).
  - Between ₹1 lakh and ₹1 crore → convert and show `₹XX.X lakh`.
  - Provide a `title`/tooltip with the full rupee figure in Indian grouping.
- Uses `Intl.NumberFormat('en-IN')` (or `hi-IN`) for grouping; **do not** use default `en-US`.

---

## 6. Internationalization

- `web/src/i18n/en.json` and `hi.json`; keys for all static UI copy. `LanguageToggle` switches
  locale; number/`RupeeAmount` formatting follows locale (`en-IN` / `hi-IN`).
- Dynamic content (LLM rationale) is generated in the user's chosen language where feasible; for the
  first build, rationale may be English with UI chrome bilingual — note this as a known limitation.
- Structure locale files so adding Tamil/Bengali/etc. is a new file, not code changes.

---

## 7. Responsible-AI in the UI (enforced, not decorative)

- **Global footer disclaimer** on every screen: *"Scores are decision aids that assess cost
  reasonableness against benchmarks and source agreement. They are not allegations of wrongdoing."*
- **No accusatory vocabulary** in any static string or rendered LLM output (mirror the pipeline's
  banned-word gate; the frontend should also defensively avoid rendering any flagged text).
- **Every score paired with reasoning and a text label.** A bare number or a lone colored dot is a
  design bug.
- **Single-source ≠ low transparency.** UI must show "Only one source available" distinctly from
  "Sources conflict".
- The **About page (4.5)** is a required deliverable, not optional.

---

## 8. Motion & states

- **Loading:** `SkeletonLoader`s matching card/table shapes (no spinners on data-heavy views).
- **Debate step-through:** gentle fade/slide as each turn appears; respects
  `prefers-reduced-motion`.
- **Empty/error:** friendly, plain-language empty states ("No projects match yet — try a different
  state or sector"), never raw error codes.

---

## 9. Handoff checklist for the frontend implementer

- [ ] Tokens (§2) wired into Tailwind config as theme extensions.
- [ ] `RupeeAmount` uses `en-IN` grouping + lakh/crore; verified against `₹1,23,456 cr`.
- [ ] All five screens (§4) built and navigable; About page copy present.
- [ ] Every score renders value + band label + reasoning; no color-only signals.
- [ ] Justification and Transparency are visually distinct blocks; never merged.
- [ ] Language toggle swaps chrome copy and number locale.
- [ ] Mobile layout verified at ~360px width; bottom nav reachable; touch targets ≥44px.
- [ ] Footer responsible-AI disclaimer on every screen.
- [ ] User-supplied React components mapped onto §5 slots where provided.
