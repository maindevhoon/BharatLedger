import { useState } from "react";
import { useI18n } from "../lib/i18n";

export function SearchBar({ onSearch, initialValue = "" }: { onSearch: (q: string) => void; initialValue?: string }) {
  const { t } = useI18n();
  const [value, setValue] = useState(initialValue);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSearch(value);
      }}
      className="flex gap-2 w-full max-w-xl"
    >
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={t("home.searchPlaceholder")}
        className="flex-1 px-4 py-3 rounded-btn border border-bl-border bg-bl-surface text-ink-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
      />
      <button
        type="submit"
        className="px-5 py-3 rounded-btn bg-teal-500 text-white font-medium hover:bg-teal-500/90"
      >
        {t("home.searchButton")}
      </button>
    </form>
  );
}
