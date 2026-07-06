import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useI18n } from "../lib/i18n";
import { api, ProjectSummary, StatsResponse } from "../lib/api";
import { SearchBar } from "../components/SearchBar";
import { FilterChips } from "../components/FilterChips";
import { ProjectCard } from "../components/ProjectCard";
import { SkeletonCardGrid } from "../components/SkeletonLoader";

const SECTORS = [
  { label: "All States", value: "" },
  { label: "Roads", value: "roads" },
  { label: "Education", value: "education" },
  { label: "Health", value: "health" },
  { label: "Water", value: "water" },
  { label: "Energy", value: "energy" },
];

export function Home() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const [sector, setSector] = useState("");
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [searchResults, setSearchResults] = useState<ProjectSummary[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStats().then(setStats).finally(() => setLoading(false));
  }, []);

  const handleSearch = async (q: string) => {
    if (!q.trim()) {
      setSearchResults(null);
      return;
    }
    const res = await api.searchProjects({ q, sector: sector || undefined, limit: 12 });
    setSearchResults(res.results);
  };

  const displayed = searchResults ?? stats?.trending_projects ?? [];

  return (
    <div className="flex flex-col items-center text-center gap-6">
      <div className="mt-4">
        <h1 className="text-3xl sm:text-4xl font-bold text-ink-900">{t("app.tagline")}</h1>
        <p className="text-ink-600 mt-2 max-w-lg mx-auto">{t("app.subtagline")}</p>
      </div>

      <SearchBar onSearch={handleSearch} />

      <div className="w-full max-w-xl">
        <FilterChips
          options={SECTORS}
          active={sector}
          onSelect={(v) => {
            setSector(v);
            setSearchResults(null);
          }}
        />
      </div>

      <div className="w-full text-left mt-4">
        <h2 className="text-lg font-semibold text-ink-900 mb-3">
          {searchResults ? "Search results" : t("home.trending")}
        </h2>
        {loading ? (
          <SkeletonCardGrid />
        ) : displayed.length === 0 ? (
          <p className="text-ink-400 text-center py-8">{t("empty.noProjects")}</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {displayed.map((p) => (
              <ProjectCard key={p.project_id} project={p} />
            ))}
          </div>
        )}
      </div>

      <button
        onClick={() => navigate("/about")}
        className="text-sm text-teal-500 hover:underline mt-2"
      >
        {t("home.howScoringWorks")} →
      </button>
    </div>
  );
}
