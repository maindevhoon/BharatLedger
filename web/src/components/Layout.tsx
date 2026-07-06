import { Link, useLocation } from "react-router-dom";
import { useI18n } from "../lib/i18n";
import { LanguageToggle } from "./LanguageToggle";

export function Layout({ children }: { children: React.ReactNode }) {
  const { t } = useI18n();
  const location = useLocation();

  const navLink = (to: string, label: string) => (
    <Link
      to={to}
      className={`text-sm font-medium ${
        location.pathname === to ? "text-teal-500" : "text-ink-600 hover:text-teal-500"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <div className="min-h-screen flex flex-col">
      <header>
        <div className="h-1.5 bg-apac-gradient" />
        <div className="max-w-[1120px] mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-indigo-700">⚖ {t("app.name")}</span>
          </Link>
          <nav className="hidden sm:flex items-center gap-6">
            {navLink("/", t("nav.search"))}
            {navLink("/rankings", t("nav.rankings"))}
            {navLink("/about", t("nav.about"))}
          </nav>
          <LanguageToggle />
        </div>
      </header>

      <main className="flex-1 max-w-[1120px] w-full mx-auto px-4 py-6 pb-24 sm:pb-6">
        {children}
      </main>

      {/* Bottom nav — mobile only, thumb-reachable (docs/UI_UX_DESIGN.md §3) */}
      <nav className="sm:hidden fixed bottom-0 left-0 right-0 bg-bl-surface border-t border-bl-border flex justify-around py-2">
        <Link to="/" className="flex flex-col items-center text-xs text-ink-600">
          <span>🔍</span>{t("nav.search")}
        </Link>
        <Link to="/rankings" className="flex flex-col items-center text-xs text-ink-600">
          <span>📊</span>{t("nav.rankings")}
        </Link>
        <Link to="/about" className="flex flex-col items-center text-xs text-ink-600">
          <span>ℹ️</span>{t("nav.about")}
        </Link>
      </nav>

      <footer className="border-t border-bl-border py-4 px-4 text-center">
        <p className="text-xs text-ink-400 max-w-2xl mx-auto">{t("footer.disclaimer")}</p>
        <Link to="/about" className="text-xs text-teal-500 hover:underline mt-1 inline-block">
          {t("footer.dataSources")}
        </Link>
      </footer>
    </div>
  );
}
