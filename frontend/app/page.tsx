"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { JobCard } from "@/components/JobCard";
import { JobCardSkeleton } from "@/components/JobCardSkeleton";
import { FilterPanel } from "@/components/FilterPanel";
import { StatsBar } from "@/components/StatsBar";
import { ExportButton } from "@/components/ExportButton";
import { ScrapeStatusBadge } from "@/components/ScrapeStatusBadge";
import type { Job, JobFilters, ScrapeRun } from "@/types/job";

const LIMIT = 50;

export default function DashboardPage() {
  const [filters, setFilters] = useState<JobFilters>({
    search: "",
    source: "",
    status: "",
    job_type: "",
  });
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(1);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    newToday: 0,
    bookmarked: 0,
    applied: 0,
  });
  const [lastRuns, setLastRuns] = useState<ScrapeRun[]>([]);
  const [triggerMessage, setTriggerMessage] = useState<string | null>(null);
  const [triggerLoading, setTriggerLoading] = useState(false);
  const [cleanupMessage, setCleanupMessage] = useState<string | null>(null);
  const [cleanupLoading, setCleanupLoading] = useState(false);
  const [jobsRefreshNonce, setJobsRefreshNonce] = useState(0);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch("/api/stats");
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setStats({
        total: data.total ?? 0,
        newToday: data.newToday ?? 0,
        bookmarked: data.bookmarked ?? 0,
        applied: data.applied ?? 0,
      });
      setLastRuns(data.lastRuns ?? []);
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(filters.search), 300);
    return () => clearTimeout(t);
  }, [filters.search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, filters.source, filters.status, filters.job_type]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const params = new URLSearchParams();
      if (debouncedSearch.trim()) params.set("search", debouncedSearch.trim());
      if (filters.source) params.set("source", filters.source);
      if (filters.status) params.set("status", filters.status);
      if (filters.job_type) params.set("job_type", filters.job_type);
      params.set("page", String(page));
      try {
        const res = await fetch(`/api/jobs?${params.toString()}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        if (!cancelled) {
          setJobs(data.jobs ?? []);
          setTotal(data.total ?? 0);
        }
      } catch (e) {
        console.error(e);
        if (!cancelled) {
          setJobs([]);
          setTotal(0);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [
    debouncedSearch,
    filters.source,
    filters.status,
    filters.job_type,
    page,
    jobsRefreshNonce,
  ]);

  function onFilterChange(key: keyof JobFilters, value: string) {
    setFilters((f) => ({ ...f, [key]: value }));
  }

  async function patchJob(id: string, updates: Partial<Job>) {
    const res = await fetch("/api/jobs", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, ...updates }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Update failed");
    }
  }

  async function handleBookmark(job: Job) {
    const next = !job.is_bookmarked;
    try {
      await patchJob(job.id, { is_bookmarked: next });
      setJobs((prev) =>
        prev.map((j) => (j.id === job.id ? { ...j, is_bookmarked: next } : j))
      );
      fetchStats();
    } catch (e) {
      console.error(e);
    }
  }

  async function handleHide(job: Job) {
    try {
      await patchJob(job.id, { is_hidden: true });
      setJobs((prev) => prev.filter((j) => j.id !== job.id));
      setTotal((t) => Math.max(0, t - 1));
      fetchStats();
    } catch (e) {
      console.error(e);
    }
  }

  async function handleTrigger() {
    setTriggerLoading(true);
    setTriggerMessage(null);
    try {
      const res = await fetch("/api/trigger", { method: "POST" });
      const data = await res.json();
      setTriggerMessage(data.message || data.error || "Done.");
    } catch {
      setTriggerMessage("Request failed.");
    } finally {
      setTriggerLoading(false);
    }
  }

  async function handleCleanup() {
    setCleanupLoading(true);
    setCleanupMessage(null);
    try {
      const res = await fetch("/api/cleanup", { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        setCleanupMessage(data.error || "Cleanup failed.");
        return;
      }
      setCleanupMessage(
        `Removed ${data.totalDeleted ?? 0} job(s) (${data.hiddenOlderThan7Days ?? 0} hidden >7d, ${data.staleOlderThan30Days ?? 0} stale >30d).`
      );
      await fetchStats();
      setJobsRefreshNonce((n) => n + 1);
    } catch {
      setCleanupMessage("Cleanup request failed.");
    } finally {
      setCleanupLoading(false);
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / LIMIT));
  const lastEnded = lastRuns[0]?.ended_at;
  const lastStatus = lastRuns[0]?.status;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-[var(--border)] bg-[var(--surface)] px-4 py-4 md:px-8">
        <div className="mx-auto max-w-[1400px] flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-display text-2xl md:text-3xl font-extrabold tracking-tight text-white">
              JOBR<span className="text-[var(--accent)]">∆</span>DAR
            </h1>
            <ScrapeStatusBadge endedAt={lastEnded} status={lastStatus} />
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/profiles"
              className="rounded border border-[var(--border)] px-4 py-2 font-mono text-xs uppercase tracking-wider text-[var(--accent)] transition hover:border-[var(--accent)]"
            >
              ⚙ Profiles
            </Link>
            {triggerMessage && (
              <span className="text-xs font-mono text-[var(--muted)] max-w-[220px]">
                {triggerMessage}
              </span>
            )}
            <button
              type="button"
              onClick={handleTrigger}
              disabled={triggerLoading}
              className="rounded border border-[var(--border)] px-4 py-2 font-mono text-xs uppercase tracking-wider text-[var(--text)] transition hover:border-[var(--accent2)] hover:text-[var(--accent2)] disabled:opacity-50"
            >
              {triggerLoading ? "…" : "Run scrape"}
            </button>
          </div>
        </div>
      </header>

      <div className="flex-1 flex flex-col lg:flex-row mx-auto w-full max-w-[1400px]">
        <aside className="w-full lg:w-64 shrink-0 border-b lg:border-b-0 lg:border-r border-[var(--border)] bg-[#0a0a12] p-4 md:p-6 space-y-6">
          <StatsBar stats={stats} lastRuns={lastRuns} />
          <div>
            <h2 className="font-display text-sm font-bold uppercase tracking-[0.15em] text-[var(--muted)] mb-3">
              Export
            </h2>
            <ExportButton filters={filters} />
          </div>
          <div>
            <h2 className="font-display text-sm font-bold uppercase tracking-[0.15em] text-[var(--muted)] mb-3">
              Maintenance
            </h2>
            {cleanupMessage && (
              <p className="text-[10px] font-mono text-[var(--muted)] mb-2 leading-relaxed">
                {cleanupMessage}
              </p>
            )}
            <button
              type="button"
              onClick={handleCleanup}
              disabled={cleanupLoading}
              className="w-full rounded border border-[var(--border)] px-4 py-2.5 font-mono text-xs uppercase tracking-wider text-[var(--text)] transition hover:border-[var(--danger)] hover:text-[var(--danger)] disabled:opacity-50"
            >
              {cleanupLoading ? "…" : "🗑 Clean old jobs"}
            </button>
          </div>
        </aside>

        <main className="flex-1 p-4 md:p-6 min-w-0">
          <div className="mb-6 rounded border border-[var(--border)] bg-[var(--surface)] p-4">
            <FilterPanel
              filters={filters}
              debouncedSearch={debouncedSearch}
              onSearchChange={(v) => setFilters((f) => ({ ...f, search: v }))}
              onFilterChange={onFilterChange}
            />
          </div>

          {loading ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <JobCardSkeleton key={i} index={i} />
              ))}
            </div>
          ) : jobs.length === 0 ? (
            <div className="rounded border border-dashed border-[var(--border)] bg-[var(--surface)]/50 py-20 text-center">
              <p className="font-display text-lg text-[var(--muted)]">No jobs match your filters.</p>
              <p className="mt-2 text-sm font-mono text-[var(--muted)]">
                Adjust filters or wait for the next scrape run.
              </p>
            </div>
          ) : (
            <>
              <div className="grid gap-4 sm:grid-cols-2">
                {jobs.map((job, i) => (
                  <JobCard
                    key={job.id}
                    job={job}
                    index={i}
                    onBookmark={handleBookmark}
                    onHide={handleHide}
                  />
                ))}
              </div>

              {totalPages > 1 && (
                <div className="mt-8 flex flex-wrap items-center justify-center gap-2 font-mono text-xs">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="rounded border border-[var(--border)] px-3 py-1.5 disabled:opacity-30 hover:border-[var(--accent)]"
                  >
                    Prev
                  </button>
                  <span className="text-[var(--muted)] px-2">
                    Page {page} / {totalPages}
                  </span>
                  <button
                    type="button"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    className="rounded border border-[var(--border)] px-3 py-1.5 disabled:opacity-30 hover:border-[var(--accent)]"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
