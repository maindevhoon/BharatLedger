import { useI18n } from "../lib/i18n";

export function VerdictBanner({ score, rationale }: { score: number; rationale: string }) {
  const { t } = useI18n();
  return (
    <div className="rounded-card bg-council-50 border-2 border-council p-5">
      <h3 className="font-semibold text-council mb-2">{t("debate.council")}</h3>
      <p className="text-lg font-bold text-ink-900 mb-1">{score}/100</p>
      <p className="text-sm text-ink-600 leading-relaxed">{rationale}</p>
    </div>
  );
}
