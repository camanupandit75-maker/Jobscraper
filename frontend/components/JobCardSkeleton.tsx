export function JobCardSkeleton({ index }: { index: number }) {
  return (
    <div
      style={{ animationDelay: `${index * 40}ms` }}
      className="animate-pulse rounded border border-[var(--border)] bg-[var(--surface)] p-4"
    >
      <div className="flex justify-between mb-3">
        <div className="h-5 w-20 rounded bg-[var(--border)]" />
        <div className="h-4 w-32 rounded bg-[var(--border)]" />
      </div>
      <div className="h-5 w-4/5 max-w-[280px] rounded bg-[var(--border)] mb-2" />
      <div className="h-4 w-3/5 max-w-[200px] rounded bg-[var(--border)] mb-4" />
      <div className="h-4 w-24 rounded bg-[var(--border)] mb-4" />
      <div className="flex gap-2">
        <div className="h-8 w-16 rounded bg-[var(--border)]" />
        <div className="h-8 w-20 rounded bg-[var(--border)]" />
        <div className="h-8 w-16 rounded bg-[var(--border)]" />
      </div>
    </div>
  );
}
