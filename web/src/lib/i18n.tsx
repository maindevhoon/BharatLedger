import React, { createContext, useContext, useState } from "react";
import en from "../i18n/en.json";
import hi from "../i18n/hi.json";

type Lang = "en" | "hi";
const DICTS: Record<Lang, Record<string, string>> = { en, hi };

interface I18nContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    const stored = localStorage.getItem("bl_lang");
    return stored === "hi" ? "hi" : "en";
  });

  const setLangPersist = (l: Lang) => {
    localStorage.setItem("bl_lang", l);
    setLang(l);
  };

  const t = (key: string) => DICTS[lang][key] ?? DICTS.en[key] ?? key;

  return (
    <I18nContext.Provider value={{ lang, setLang: setLangPersist, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}

/** Locale string for Intl.NumberFormat, keyed off the active language — not hardcoded to one
 * country's convention (docs/UI_UX_DESIGN.md §6 / ARCHITECTURE.md §8 country abstraction). */
export function localeForLang(lang: Lang): string {
  return lang === "hi" ? "hi-IN" : "en-IN";
}
