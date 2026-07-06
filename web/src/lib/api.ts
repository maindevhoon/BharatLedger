/** Typed client for the FastAPI backend (api/main.py). Mirrors docs/ARCHITECTURE.md §5. */

const BASE = "/api/v1";

export type JustificationBand = "well_justified" | "partially_justified" | "needs_review";
export type TransparencyBand = "consistent" | "minor_conflicts" | "sources_conflict" | "single_source";

export interface ProjectSummary {
  project_id: string;
  country: string;
  state: string;
  sector: string;
  name: string;
  year: number;
  sanctioned_cr: number;
  cost_per_unit_cr: number;
  outcome_unit: string;
  justification_score: number | null;
  justification_band: JustificationBand | null;
  transparency_band: TransparencyBand | null;
}

export interface Project {
  project_id: string;
  country: string;
  state: string;
  sector: string;
  name: string;
  year: number;
  sanctioned_cr: number;
  disbursed_cr: number;
  utilized_cr: number;
  outcome_value: number;
  outcome_unit: string;
  description: string;
  cost_per_unit_cr: number;
}

export interface ConflictItem {
  field: string;
  source_a: string;
  value_a: number;
  source_b: string;
  value_b: number;
  delta_cr: number;
}

export interface ArgumentItem {
  claim: string;
  evidence: string;
  figure: string;
}

export interface DebateTurn {
  agent: "red" | "blue" | "council";
  stance: string | null;
  arguments: ArgumentItem[];
  verdict: string | null;
  score: number | null;
  rationale: string | null;
}

export interface DebateTranscript {
  turns: DebateTurn[];
}

export interface Verdict {
  project_id: string;
  justification_score: number;
  justification_rationale: string;
  transparency_score: number | null;
  transparency_conflicts: ConflictItem[];
  debate_transcript: DebateTranscript;
  scored_at: string;
  justification_band: JustificationBand;
  transparency_band: TransparencyBand;
}

export interface ProjectWithVerdict {
  project: Project;
  verdict: Verdict | null;
}

export interface RankingRow {
  country: string;
  sector: string;
  year: number;
  state: string;
  median_cost_per_unit_cr: number;
  rank: number;
  efficiency_score: number;
}

export interface PaginatedProjects {
  results: ProjectSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface StatsResponse {
  country: string;
  total_projects: number;
  total_scored: number;
  justification_band_counts: { well_justified: number; partially_justified: number; needs_review: number };
  trending_projects: ProjectSummary[];
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  searchProjects: (params: {
    q?: string; state?: string; sector?: string; year?: number; limit?: number; offset?: number;
  }) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") qs.set(k, String(v));
    });
    return getJson<PaginatedProjects>(`/projects?${qs.toString()}`);
  },

  getProject: (projectId: string) =>
    getJson<ProjectWithVerdict>(`/projects/${encodeURIComponent(projectId)}`),

  getDebate: (projectId: string) =>
    getJson<DebateTranscript>(`/projects/${encodeURIComponent(projectId)}/debate`),

  getRankings: (sector: string, year: number) =>
    getJson<RankingRow[]>(`/rankings?sector=${sector}&year=${year}`),

  getStats: () => getJson<StatsResponse>("/stats"),

  runLiveDebate: async (projectId: string): Promise<DebateTranscript> => {
    const res = await fetch(`${BASE}/projects/${encodeURIComponent(projectId)}/debate/live`, {
      method: "POST",
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed: ${res.status}`);
    }
    return res.json();
  },
};
