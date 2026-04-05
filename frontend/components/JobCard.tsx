"use client";

import { format } from "date-fns";
import clsx from "clsx";
import type { Job } from "@/types/job";

type Props = {
  job: Job;
  index: number;
  onBookmark: (job: Job) => void;
  onHide: (job: Job) => void;
};

function sourceClass(source: string) {
  const s = source?.toLowerCase() || "";
  const map: Record<string, string> = {
    remoteok: "source-remoteok",
    indeed: "source-indeed",
    naukri: "source-naukri",
    linkedin: "source-linkedin",
    wellfound: "source-wellfound",
    internshala: "source-internshala",
    glassdoor: "source-glassdoor",
  };
  return map[s] || "source-indeed";
}

export function JobCard({ job, index, onBookmark, onHide }: Props) {
  const posted =
    job.posted_at &&
    (() => {
      try {
        return format(new Date(job.posted_at), "MMM d, yyyy");
      } catch {
        return "—";
      }
    })();

  return (
    <article
      style={{ animationDelay: `${Math.min(index, 12) * 45}ms` }}
      className={clsx(
        "animate-fade-in opacity-0 rounded border border-[var(--border)] bg-[var(--surface)] p-4 shadow-lg",
        job.is_bookmarked && "border-l-4 border-l-[var(--accent)]"
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <span className={clsx("source-badge", sourceClass(String(job.source)))}>
          {job.source}
        </span>
        <div className="flex items-center gap-2 text-[10px] font-mono text-[var(--muted)] uppercase tracking-wide">
          <span>{job.job_type || "—"}</span>
          <span className="text-[var(--border)]">·</span>
          <span>{posted}</span>
        </div>
      </div>

      <h3 className="font-display text-base font-semibold text-white leading-snug mb-1">
        {job.title}
      </h3>
      <p className="text-sm text-[var(--muted)] mb-3">
        {job.company || "—"}
        {job.location ? ` · ${job.location}` : ""}
      </p>

      {job.salary ? (
        <p className="text-sm text-[var(--accent)] font-mono mb-4">{job.salary}</p>
      ) : (
        <div className="mb-4" />
      )}

      <div className="flex flex-wrap gap-2">
        <a
          href={job.url || "#"}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 rounded border border-[var(--border)] px-3 py-1.5 text-xs font-mono text-[var(--accent2)] transition hover:border-[var(--accent2)]"
        >
          Open ↗
        </a>
        <button
          type="button"
          onClick={() => onBookmark(job)}
          className={clsx(
            "rounded border px-3 py-1.5 text-xs font-mono transition",
            job.is_bookmarked
              ? "border-[var(--accent)] text-[var(--accent)]"
              : "border-[var(--border)] text-[var(--muted)] hover:border-[var(--accent)] hover:text-[var(--accent)]"
          )}
        >
          ♥ {job.is_bookmarked ? "Saved" : "Save"}
        </button>
        <button
          type="button"
          onClick={() => onHide(job)}
          className="rounded border border-[var(--border)] px-3 py-1.5 text-xs font-mono text-[var(--danger)] transition hover:border-[var(--danger)]"
        >
          ✕ Hide
        </button>
      </div>
    </article>
  );
}
