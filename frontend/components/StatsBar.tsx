import { format } from "date-fns";
import type { ScrapeRun } from "@/types/job";

type Stats = {
  total: number;
  newToday: number;
  bookmarked: number;
  applied: number;
};

type Props = {
  stats: Stats;
  lastRuns: ScrapeRun[];
};

export function StatsBar({ stats, lastRuns }: Props) {
  const rows = [
    { label: "Total jobs", value: stats.total },
    { label: "New today", value: stats.newToday },
    { label: "Bookmarked", value: stats.bookmarked },
    { label: "Applied", value: stats.applied },
  ];

  const displayRuns = lastRuns.slice(0, 5);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display text-sm font-bold uppercase tracking-[0.15em] text-[var(--muted)] mb-3">
          Stats
        </h2>
        <ul className="space-y-3">
          {rows.map((r) => (
            <li
              key={r.label}
              className="flex justify-between gap-4 border-b border-[var(--border)] pb-2 last:border-0"
            >
              <span className="text-[var(--muted)] text-xs">{r.label}</span>
              <span className="font-mono text-[var(--accent)] tabular-nums">{r.value}</span>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h2 className="font-display text-sm font-bold uppercase tracking-[0.15em] text-[var(--muted)] mb-3">
          Recent runs
        </h2>
        {displayRuns.length === 0 ? (
          <p className="text-[var(--muted)] text-xs">No scrape history yet.</p>
        ) : (
          <ul className="space-y-2">
            {displayRuns.map((run) => (
              <li
                key={run.id ?? `${run.source}-${run.started_at}`}
                className="rounded border border-[var(--border)] bg-[#0a0a10] px-3 py-2 text-xs"
              >
                <div className="flex justify-between gap-2">
                  <span className="rounded border border-[var(--border)] px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-[var(--accent2)]">
                    {run.source || "—"}
                  </span>
                  <span
                    className={
                      run.status === "error"
                        ? "text-[var(--danger)]"
                        : "text-[var(--success)]"
                    }
                  >
                    +{run.jobs_added ?? 0}
                  </span>
                </div>
                <p className="mt-1 text-[var(--muted)] font-mono text-[10px]">
                  {run.ended_at
                    ? format(new Date(run.ended_at), "MMM d, HH:mm")
                    : "—"}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
