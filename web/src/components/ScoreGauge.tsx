import { useI18n } from "../lib/i18n";
import type { JustificationBand } from "../lib/api";

const BAND_COLORS: Record<JustificationBand, { ring: string; text: string; bg: string }> = {
  well_justified: { ring: "stroke-good-600", text: "text-good-600", bg: "bg-good-50" },
  partially_justified: { ring: "stroke-warn-600", text: "text-warn-600", bg: "bg-warn-50" },
  needs_review: { ring: "stroke-review-600", text: "text-review-600", bg: "bg-review-50" },
};

/** Justification Score gauge. ALWAYS renders the numeric value + a text band label — never
 * color alone (docs/UI_UX_DESIGN.md §1 rule #2 / §7). */
export function ScoreGauge({
  value,
  band,
  caption,
  size = 120,
}: {
  value: number;
  band: JustificationBand;
  caption?: string;
  size?: number;
}) {
  const { t } = useI18n();
  const colors = BAND_COLORS[band];
  const radius = size / 2 - 10;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - value / 100);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            className="stroke-bl-border" strokeWidth={10} fill="none"
          />
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            className={colors.ring} strokeWidth={10} fill="none"
            strokeDasharray={circumference} strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-ink-900">{value}</span>
          <span className="text-xs text-ink-400">/100</span>
        </div>
      </div>
      <div className={`px-3 py-1 rounded-full text-sm font-medium ${colors.bg} ${colors.text}`}>
        {t(`band.${band}`)}
      </div>
      {caption && <div className="text-xs text-ink-600 text-center max-w-[180px]">{caption}</div>}
    </div>
  );
}
