import { useEffect, useState } from "react";
import { useI18n } from "../lib/i18n";
import { api, RankingRow } from "../lib/api";
import { Dropdown } from "../components/Dropdown";
import { RankingTable } from "../components/RankingTable";
import { SkeletonLoader } from "../components/SkeletonLoader";

const SECTOR_OPTIONS = [
  { label: "Roads", value: "roads" },
  { label: "Education", value: "education" },
  { label: "Health", value: "health" },
  { label: "Water", value: "water" },
  { label: "Energy", value: "energy" },
];

const YEAR_OPTIONS = Array.from({ length: 9 }, (_, i) => 2016 + i).map((y) => ({
  label: `FY${y}-${String(y + 1).slice(-2)}`,
  value: String(y),
}));

export function Rankings() {
  const { t } = useI18n();
  const [sector, setSector] = useState("roads");
  const [year, setYear] = useState("2022");
  const [rows, setRows] = useState<RankingRow[] | null>(null);

  useEffect(() => {
    setRows(null);
    api.getRankings(sector, Number(year)).then(setRows);
  }, [sector, year]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-ink-900">{t("rankings.title")}</h1>
        <p className="text-sm text-ink-600 mt-1">{t("rankings.accelerationNote")}</p>
      </div>

      <div className="flex gap-4">
        <Dropdown label={t("rankings.sector")} value={sector} options={SECTOR_OPTIONS} onChange={setSector} />
        <Dropdown label={t("rankings.year")} value={year} options={YEAR_OPTIONS} onChange={setYear} />
      </div>

      {rows === null ? (
        <SkeletonLoader className="h-96" />
      ) : rows.length === 0 ? (
        <p className="text-ink-400 text-center py-8">{t("empty.noProjects")}</p>
      ) : (
        <RankingTable rows={rows} />
      )}
    </div>
  );
}
