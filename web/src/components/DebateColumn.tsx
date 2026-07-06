import { useI18n } from "../lib/i18n";
import type { ArgumentItem } from "../lib/api";

const SIDE_STYLES = {
  red: { bg: "bg-redteam-50", border: "border-redteam", heading: "text-redteam" },
  blue: { bg: "bg-blueteam-50", border: "border-blueteam", heading: "text-blueteam" },
};

export function DebateColumn({
  side,
  arguments: args,
}: {
  side: "red" | "blue";
  arguments: ArgumentItem[];
}) {
  const { t } = useI18n();
  const styles = SIDE_STYLES[side];
  return (
    <div className={`rounded-card border-2 ${styles.border} ${styles.bg} p-5 flex-1`}>
      <h3 className={`font-semibold mb-3 ${styles.heading}`}>
        {t(side === "red" ? "debate.redTeam" : "debate.blueTeam")}
      </h3>
      <div className="space-y-3">
        {args.map((arg, i) => (
          <ArgumentCard key={i} argument={arg} />
        ))}
      </div>
    </div>
  );
}

function ArgumentCard({ argument }: { argument: ArgumentItem }) {
  return (
    <div className="bg-bl-surface rounded-lg p-3 text-sm">
      <p className="font-medium text-ink-900">{argument.claim}</p>
      <p className="text-ink-600 mt-1">{argument.evidence}</p>
      {argument.figure && (
        <p className="text-ink-400 text-xs mt-1 font-mono">{argument.figure}</p>
      )}
    </div>
  );
}
