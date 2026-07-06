import { formatCrore, formatFullCrore } from "../lib/rupee";
import { useI18n, localeForLang } from "../lib/i18n";

/** The canonical money renderer (docs/UI_UX_DESIGN.md §5.1). Always Indian lakh/crore
 * grouping, never Western thousands/millions. */
export function RupeeAmount({ crore }: { crore: number }) {
  const { lang } = useI18n();
  const locale = localeForLang(lang);
  return <span title={formatFullCrore(crore, locale)}>{formatCrore(crore, locale)}</span>;
}
