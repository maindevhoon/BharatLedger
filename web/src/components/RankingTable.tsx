import { useI18n } from "../lib/i18n";
import type { RankingRow } from "../lib/api";

function scoreColor(score: number): string {
  if (score >= 75) return "text-good-600 bg-good-50";
  if (score >= 45) return "text-warn-600 bg-warn-50";
  return "text-review-600 bg-review-50";
}

export function RankingTable({ rows }: { rows: RankingRow[] }) {
  const { t } = useI18n();
  return (
    <div className="bg-bl-surface rounded-card border border-bl-border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-bl-bg text-ink-600 text-left">
          <tr>
            <th className="px-4 py-3 font-medium">{t("rankings.rank")}</th>
            <th className="px-4 py-3 font-medium">{t("rankings.state")}</th>
            <th className="px-4 py-3 font-medium tabular-nums text-right">{t("rankings.costPerUnit")}</th>
            <th className="px-4 py-3 font-medium text-right">{t("rankings.efficiencyScore")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.state} className="border-t border-bl-border">
              <td className="px-4 py-3 tabular-nums text-ink-400">{row.rank}</td>
              <td className="px-4 py-3 font-medium text-ink-900">{row.state}</td>
              <td className="px-4 py-3 tabular-nums text-right text-ink-600">
                {row.median_cost_per_unit_cr.toFixed(2)}
              </td>
              <td className="px-4 py-3 text-right">
                <span className={`inline-block px-2 py-1 rounded-full font-medium tabular-nums ${scoreColor(row.efficiency_score)}`}>
                  {row.efficiency_score}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
