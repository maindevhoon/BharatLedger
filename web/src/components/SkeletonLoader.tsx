export function SkeletonLoader({ className = "h-24" }: { className?: string }) {
  return <div className={`animate-pulse bg-bl-border/60 rounded-card ${className}`} />;
}

export function SkeletonCardGrid({ count = 3 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonLoader key={i} className="h-32" />
      ))}
    </div>
  );
}
