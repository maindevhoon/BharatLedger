export function RationalePanel({ title, text }: { title: string; text: string }) {
  return (
    <div className="bg-bl-surface rounded-card border border-bl-border p-5">
      <h4 className="font-semibold text-ink-900 mb-2">{title}</h4>
      <p className="text-sm text-ink-600 leading-relaxed">{text}</p>
    </div>
  );
}
