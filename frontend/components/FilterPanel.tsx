"use client";

import type { JobFilters } from "@/types/job";

const SOURCES = [
  { value: "", label: "All sources" },
  { value: "remoteok", label: "RemoteOK" },
  { value: "indeed", label: "Indeed" },
  { value: "naukri", label: "Naukri" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "wellfound", label: "Wellfound" },
  { value: "internshala", label: "Internshala" },
  { value: "glassdoor", label: "Glassdoor" },
];

const STATUSES = [
  { value: "", label: "All statuses" },
  { value: "new", label: "New" },
  { value: "applied", label: "Applied" },
];

const JOB_TYPES = [
  { value: "", label: "All types" },
  { value: "full-time", label: "Full-time" },
  { value: "part-time", label: "Part-time" },
  { value: "remote", label: "Remote" },
  { value: "contract", label: "Contract" },
];

type Props = {
  filters: JobFilters;
  debouncedSearch: string;
  debouncedLocation: string;
  onSearchChange: (v: string) => void;
  onFilterChange: (key: keyof JobFilters, value: string) => void;
};

export function FilterPanel({
  filters,
  debouncedSearch,
  debouncedLocation,
  onSearchChange,
  onFilterChange,
}: Props) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-[10px] uppercase tracking-widest text-[var(--muted)] mb-1.5">
          Search
        </label>
        <input
          type="search"
          value={filters.search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Title or company…"
          className="w-full rounded border border-[var(--border)] bg-[#0a0a10] px-3 py-2 font-mono text-sm text-[var(--text)] placeholder:text-[var(--muted)] focus:border-[var(--accent)] focus:outline-none"
        />
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
        <div>
          <label className="block text-[10px] uppercase tracking-widest text-[var(--muted)] mb-1.5">
            Source
          </label>
          <select
            value={filters.source}
            onChange={(e) => onFilterChange("source", e.target.value)}
            className="w-full rounded border border-[var(--border)] bg-[#0a0a10] px-3 py-2 font-mono text-xs text-[var(--text)] focus:border-[var(--accent)] focus:outline-none"
          >
            {SOURCES.map((o) => (
              <option key={o.value || "all"} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-[10px] uppercase tracking-widest text-[var(--muted)] mb-1.5">
            Type
          </label>
          <select
            value={filters.job_type}
            onChange={(e) => onFilterChange("job_type", e.target.value)}
            className="w-full rounded border border-[var(--border)] bg-[#0a0a10] px-3 py-2 font-mono text-xs text-[var(--text)] focus:border-[var(--accent)] focus:outline-none"
          >
            {JOB_TYPES.map((o) => (
              <option key={o.value || "all-t"} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-[10px] uppercase tracking-widest text-[var(--muted)] mb-1.5">
            Status
          </label>
          <select
            value={filters.status}
            onChange={(e) => onFilterChange("status", e.target.value)}
            className="w-full rounded border border-[var(--border)] bg-[#0a0a10] px-3 py-2 font-mono text-xs text-[var(--text)] focus:border-[var(--accent)] focus:outline-none"
          >
            {STATUSES.map((o) => (
              <option key={o.value || "all-s"} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-[10px] uppercase tracking-widest text-[var(--muted)] mb-1.5">
            Location
          </label>
          <input
            type="text"
            value={filters.location}
            onChange={(e) => onFilterChange("location", e.target.value)}
            placeholder="India, Dubai, Remote…"
            className="w-full rounded border border-[var(--border)] bg-[#0a0a10] px-3 py-2 font-mono text-xs text-[var(--text)] placeholder:text-[var(--muted)] focus:border-[var(--accent)] focus:outline-none"
          />
        </div>
      </div>

      {(debouncedSearch !== filters.search ||
        debouncedLocation !== filters.location) && (
        <p className="text-[10px] text-[var(--muted)] font-mono">
          {debouncedSearch !== filters.search && debouncedLocation !== filters.location
            ? "Updating search and location…"
            : debouncedSearch !== filters.search
              ? "Updating search…"
              : "Updating location…"}
        </p>
      )}
    </div>
  );
}
