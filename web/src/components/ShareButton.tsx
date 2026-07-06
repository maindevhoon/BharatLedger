import { useState } from "react";
import { useI18n } from "../lib/i18n";

export function ShareButton({ title }: { title: string }) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    const url = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({ title, url });
        return;
      } catch {
        // user cancelled or share failed — fall through to clipboard
      }
    }
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleShare}
      className="px-4 py-2 rounded-btn border border-bl-border text-ink-600 text-sm font-medium hover:border-teal-500 hover:text-teal-500"
    >
      {copied ? "Link copied!" : t("project.share")}
    </button>
  );
}
