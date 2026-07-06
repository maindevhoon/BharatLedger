import { Link } from "react-router-dom";
import { useI18n } from "../lib/i18n";
import { RupeeAmount } from "./RupeeAmount";
import type { ProjectSummary } from "../lib/api";

const BAND_DOT: Record<string, string> = {
  well_justified: "bg-good-600",
  partially_justified: "bg-warn-600",
  needs_review: "bg-review-600",
};

export function ProjectCard({ project }: { project: ProjectSummary }) {
  const { t } = useI18n();
  return (
    <Link
      to={`/project/${project.project_id}`}
      className="block bg-bl-surface rounded-card border border-bl-border p-5 hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-ink-900 leading-snug">{project.name}</h3>
          <p className="text-sm text-ink-600 mt-1">
            {project.state} · {project.sector} · FY{project.year}
          </p>
        </div>
        {project.justification_band && (
          <span className={`w-3 h-3 rounded-full mt-1 shrink-0 ${BAND_DOT[project.justification_band]}`} />
        )}
      </div>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-sm text-ink-600">
          <RupeeAmount crore={project.sanctioned_cr} /> sanctioned
        </span>
        {project.justification_score !== null && (
          <span className="text-sm font-medium text-ink-900">
            {project.justification_score}/100
            {project.justification_band && (
              <span className="text-ink-400 font-normal"> · {t(`band.${project.justification_band}`)}</span>
            )}
          </span>
        )}
      </div>
    </Link>
  );
}
