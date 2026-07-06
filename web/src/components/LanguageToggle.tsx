import { useI18n } from "../lib/i18n";

export function LanguageToggle() {
  const { lang, setLang } = useI18n();
  return (
    <div className="flex rounded-btn border border-bl-border overflow-hidden text-sm">
      <button
        onClick={() => setLang("en")}
        className={`px-3 py-1 ${lang === "en" ? "bg-teal-500 text-white" : "bg-bl-surface text-ink-600"}`}
      >
        EN
      </button>
      <button
        onClick={() => setLang("hi")}
        className={`px-3 py-1 ${lang === "hi" ? "bg-teal-500 text-white" : "bg-bl-surface text-ink-600"}`}
      >
        हिं
      </button>
    </div>
  );
}
