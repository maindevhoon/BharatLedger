import { useI18n } from "../lib/i18n";

/** The responsible-AI surface (docs/UI_UX_DESIGN.md §4.5). Not filler — this is the in-product
 * answer to "could this be defamatory / cause harm?" and must stay visible, not buried. */
export function About() {
  const { t } = useI18n();

  return (
    <div className="space-y-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-ink-900">{t("about.title")}</h1>

      <section>
        <h2 className="font-semibold text-ink-900 mb-2">What this is — and is not</h2>
        <p className="text-sm text-ink-600 leading-relaxed">
          Bharat Ledger helps you reason about whether public spending is reasonable. It does{" "}
          <strong>not</strong> allege corruption, wrongdoing, or intent. Every score is a decision
          aid — a starting point for your own judgment, not a verdict.
        </p>
      </section>

      <section>
        <h2 className="font-semibold text-ink-900 mb-2">How the two scores are computed</h2>
        <p className="text-sm text-ink-600 leading-relaxed mb-2">
          <strong>Justification Score</strong> compares a project's cost per outcome unit (e.g.
          ₹ crore per km of road) against a benchmark for similar projects, adjusted for terrain
          and scope. An AI debate — one side arguing the cost is excessive, one arguing it is
          justified — produces the final score and a written rationale, so you can see the
          reasoning, not just the number.
        </p>
        <p className="text-sm text-ink-600 leading-relaxed">
          <strong>Transparency Score</strong> is calculated separately and independently: it
          measures how closely different official sources (Union Budget, state budgets, CAG
          audit reports) agree on the same project's figures. A project can be well-justified but
          have conflicting sources, or vice versa — these are two different questions, and we
          never combine them into a single number.
        </p>
      </section>

      <section>
        <h2 className="font-semibold text-ink-900 mb-2">How the debate works</h2>
        <p className="text-sm text-ink-600 leading-relaxed">
          A "Red Team" argues the cost is excessive, grounded in comparable benchmark data. A
          "Blue Team" argues the cost is justified, grounded in project context (terrain, scale,
          scope). A "Council" reviews both arguments plus the Transparency Score and produces the
          final Justification Score with a rationale. The full debate transcript is always
          available to read for yourself.
        </p>
      </section>

      <section>
        <h2 className="font-semibold text-ink-900 mb-2">Data sources & limitations</h2>
        <ul className="text-sm text-ink-600 leading-relaxed list-disc pl-5 space-y-1">
          <li>
            This prototype combines a small number of real government documents (including a CAG
            audit report) with synthetic, illustrative data calibrated to plausible magnitudes —
            not verified real-world figures for every project shown.
          </li>
          <li>Automated PDF extraction is early-stage and may not capture every figure correctly.</li>
          <li>Coverage currently focuses on a subset of states, sectors, and years.</li>
          <li>India is the first country supported; the platform is designed to extend to others.</li>
        </ul>
      </section>

      <section>
        <h2 className="font-semibold text-ink-900 mb-2">Language & accessibility</h2>
        <p className="text-sm text-ink-600 leading-relaxed">
          Available in English and Hindi, with more Indian languages planned. Every score is
          always paired with a text label — never color alone — so the tool remains usable
          regardless of color vision.
        </p>
      </section>
    </div>
  );
}
