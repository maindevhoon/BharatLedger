/**
 * Indian rupee formatting — lakh/crore grouping, never Western thousands/millions.
 * docs/UI_UX_DESIGN.md §5.1. Country-aware via `locale` param (defaults to en-IN) rather than
 * hardcoded, per ARCHITECTURE.md §8's country-abstraction rule.
 */

export function formatCrore(crore: number, locale: string = "en-IN"): string {
  const fmt = (n: number, maxFrac = 0) =>
    new Intl.NumberFormat(locale, { maximumFractionDigits: maxFrac }).format(n);

  if (crore >= 1) {
    return `₹${fmt(crore, 2)} cr`;
  }
  if (crore >= 0.01) {
    // between ₹1 lakh and ₹1 crore -> show in lakh
    const lakh = crore * 100;
    return `₹${fmt(lakh, 1)} lakh`;
  }
  // below ₹1 lakh -> show the raw rupee figure
  const rupees = crore * 1_00_00_000;
  return `₹${fmt(rupees, 0)}`;
}

export function formatFullCrore(crore: number, locale: string = "en-IN"): string {
  const fmt = new Intl.NumberFormat(locale, { maximumFractionDigits: 2 });
  return `₹${fmt.format(crore)} crore`;
}
