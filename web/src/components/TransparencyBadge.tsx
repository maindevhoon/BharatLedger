import { useI18n } from "../lib/i18n";
import type { TransparencyBand } from "../lib/api";

const BAND_STYLES: Record<TransparencyBand, string> = {
  consistent: "bg-good-50 text-good-600",
  minor_conflicts: "bg-warn-50 text-warn-600",
  sources_conflict: "bg-review-50 text-review-600",
  single_source: "bg-bl-bg text-ink-400 border border-bl-border",
};

/** Distinct visual shape from ScoreGauge so the two scores never look interchangeable
 * (docs/UI_UX_DESIGN.md §4.2). Single-source is visually distinct from a low score — absence
 * of conflicting evidence is not the same as confirmed consistency. */
export function TransparencyBadge({
  band,
  conflictCount = 0,
}: {
  band: TransparencyBand;
  conflictCount?: number;
}) {
  const { t } = useI18n();
  return (
    <div className={`inline-flex flex-col gap-1 px-4 py-3 rounded-card ${BAND_STYLES[band]}`}>
      <span className="font-semibold text-sm uppercase tracking-wide">{t(`transparency.${band}`)}</span>
      {band === "sources_conflict" || band === "minor_conflicts" ? (
        <span className="text-xs">
          {conflictCount} {conflictCount === 1 ? "figure" : "figures"} disagree across sources
        </span>
      ) : band === "single_source" ? (
        <span className="text-xs">No second source to cross-check against yet</span>
      ) : (
        <span className="text-xs">All sources report matching figures</span>
      )}
    </div>
  );
}
