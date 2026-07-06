export function FilterChips({
  options,
  active,
  onSelect,
}: {
  options: { label: string; value: string }[];
  active: string;
  onSelect: (value: string) => void;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onSelect(opt.value)}
          className={`shrink-0 px-4 py-1.5 rounded-full text-sm border transition-colors ${
            active === opt.value
              ? "bg-teal-500 text-white border-teal-500"
              : "bg-bl-surface text-ink-600 border-bl-border hover:border-teal-500"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
