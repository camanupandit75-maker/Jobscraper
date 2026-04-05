"use client";

import type { JobFilters } from "@/types/job";
import { useState } from "react";

type Props = {
  filters: JobFilters;
};

function buildQuery(f: JobFilters): string {
  const p = new URLSearchParams();
  if (f.search.trim()) p.set("search", f.search.trim());
  if (f.source) p.set("source", f.source);
  if (f.status) p.set("status", f.status);
  if (f.job_type) p.set("job_type", f.job_type);
  const q = p.toString();
  return q ? `?${q}` : "";
}

export function ExportButton({ filters }: Props) {
  const [loading, setLoading] = useState(false);

  async function handleExport() {
    setLoading(true);
    try {
      const res = await fetch(`/api/export${buildQuery(filters)}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || "Export failed");
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `jobs-${Date.now()}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleExport}
      disabled={loading}
      className="w-full rounded border border-[var(--accent)] bg-transparent px-4 py-2.5 font-display text-sm font-semibold uppercase tracking-wider text-[var(--accent)] transition hover:bg-[var(--accent)] hover:text-[var(--bg)] disabled:opacity-50"
    >
      {loading ? "Exporting…" : "Export Excel"}
    </button>
  );
}
