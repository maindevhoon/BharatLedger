import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useI18n } from "../lib/i18n";
import { api, ProjectWithVerdict } from "../lib/api";
import { ScoreGauge } from "../components/ScoreGauge";
import { TransparencyBadge } from "../components/TransparencyBadge";
import { RationalePanel } from "../components/RationalePanel";
import { ConflictRow } from "../components/ConflictRow";
import { RupeeAmount } from "../components/RupeeAmount";
import { ShareButton } from "../components/ShareButton";
import { SkeletonLoader } from "../components/SkeletonLoader";

export function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { t } = useI18n();
  const [data, setData] = useState<ProjectWithVerdict | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    setData(null);
    setError(null);
    api.getProject(projectId).then(setData).catch((e) => setError(e.message));
  }, [projectId]);

  if (error) {
    return <p className="text-review-600 text-center py-12">{error}</p>;
  }
  if (!data) {
    return (
      <div className="space-y-4">
        <SkeletonLoader className="h-8 w-1/2" />
        <SkeletonLoader className="h-40" />
      </div>
    );
  }

  const { project, verdict } = data;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs text-ink-400">
          <Link to="/" className="hover:underline">
            Home
          </Link>{" "}
          / {project.state} / {project.sector}
        </p>
        <h1 className="text-2xl font-bold text-ink-900 mt-1">{project.name}</h1>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-600 mt-2">
          <span>{t("project.sanctioned")}: <RupeeAmount crore={project.sanctioned_cr} /></span>
          <span>{t("project.state")}: {project.state}</span>
          <span>{t("project.sector")}: {project.sector}</span>
          <span>{t("project.fy")}{project.year}-{String(project.year + 1).slice(-2)}</span>
        </div>
      </div>

      {verdict ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-bl-surface rounded-card border border-bl-border p-5 flex flex-col items-center">
              <h3 className="font-semibold text-ink-900 mb-3 self-start">{t("project.justification")}</h3>
              <ScoreGauge
                value={verdict.justification_score}
                band={verdict.justification_band}
                caption={`₹${project.cost_per_unit_cr.toFixed(2)} cr/${project.outcome_unit}`}
              />
            </div>
            <div className="bg-bl-surface rounded-card border border-bl-border p-5 flex flex-col items-center justify-center">
              <h3 className="font-semibold text-ink-900 mb-3 self-start">{t("project.transparency")}</h3>
              <TransparencyBadge
                band={verdict.transparency_band}
                conflictCount={verdict.transparency_conflicts.length}
              />
            </div>
          </div>

          <RationalePanel title={t("project.whyThisScore")} text={verdict.justification_rationale} />

          {verdict.transparency_conflicts.length > 0 && (
            <div className="bg-bl-surface rounded-card border border-bl-border p-5">
              <h4 className="font-semibold text-ink-900 mb-2">{t("project.conflicts")}</h4>
              {verdict.transparency_conflicts.map((c, i) => (
                <ConflictRow key={i} conflict={c} />
              ))}
            </div>
          )}

          <div className="flex gap-3">
            <Link
              to={`/debate/${project.project_id}`}
              className="px-5 py-3 rounded-btn bg-teal-500 text-white font-medium hover:bg-teal-500/90"
            >
              {t("project.watchDebate")} →
            </Link>
            <ShareButton title={project.name} />
          </div>
        </>
      ) : (
        <p className="text-ink-400 py-8 text-center">Not yet scored.</p>
      )}
    </div>
  );
}
