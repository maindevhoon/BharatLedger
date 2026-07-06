import { RupeeAmount } from "./RupeeAmount";
import type { ConflictItem } from "../lib/api";

export function ConflictRow({ conflict }: { conflict: ConflictItem }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 py-2 border-b border-bl-border last:border-0 text-sm">
      <span className="text-ink-600 capitalize">{conflict.field.replace("_cr", "").replace("_", " ")}</span>
      <span className="text-ink-900">
        {conflict.source_a}: <RupeeAmount crore={conflict.value_a} /> vs {conflict.source_b}:{" "}
        <RupeeAmount crore={conflict.value_b} />{" "}
        <span className="text-review-600 font-medium">
          (Δ <RupeeAmount crore={conflict.delta_cr} />)
        </span>
      </span>
    </div>
  );
}
