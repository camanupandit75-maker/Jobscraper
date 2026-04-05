"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  PROFILE_SITE_OPTIONS,
  type SearchProfile,
} from "@/types/searchProfile";

export default function ProfilesPage() {
  const [profiles, setProfiles] = useState<SearchProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formName, setFormName] = useState("");
  const [formKeywords, setFormKeywords] = useState("");
  const [formLocation, setFormLocation] = useState("");
  const [formSites, setFormSites] = useState<Set<string>>(new Set());
  const [formActive, setFormActive] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/profiles");
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to load profiles");
      setProfiles(data.profiles ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function toggleFormSite(site: string) {
    setFormSites((prev) => {
      const next = new Set(prev);
      if (next.has(site)) next.delete(site);
      else next.add(site);
      return next;
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const res = await fetch("/api/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: formName.trim(),
          keywords: formKeywords,
          location: formLocation.trim(),
          sites: Array.from(formSites),
          is_active: formActive,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Save failed");
      setFormName("");
      setFormKeywords("");
      setFormLocation("");
      setFormSites(new Set());
      setFormActive(true);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(p: SearchProfile) {
    const next = !p.is_active;
    try {
      const res = await fetch("/api/profiles", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: p.id, is_active: next }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Update failed");
      setProfiles((list) =>
        list.map((x) => (x.id === p.id ? { ...x, is_active: next } : x))
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this search profile?")) return;
    try {
      const res = await fetch(`/api/profiles?id=${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Delete failed");
      setProfiles((list) => list.filter((p) => p.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg)]">
      <header className="border-b border-[var(--border)] bg-[var(--surface)] px-4 py-4 md:px-8">
        <div className="mx-auto max-w-[1000px] flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="font-display text-2xl font-extrabold tracking-tight text-white">
              Search <span className="text-[var(--accent)]">Profiles</span>
            </h1>
            <p className="text-xs font-mono text-[var(--muted)] mt-1">
              Worker uses active profiles from Supabase when the table is non-empty.
            </p>
          </div>
          <Link
            href="/"
            className="rounded border border-[var(--border)] px-4 py-2 font-mono text-xs uppercase tracking-wider text-[var(--accent)] transition hover:border-[var(--accent)]"
          >
            ← Dashboard
          </Link>
        </div>
      </header>

      <main className="flex-1 mx-auto w-full max-w-[1000px] p-4 md:p-8 space-y-8">
        {error && (
          <div className="rounded border border-[var(--danger)] bg-[#2a1515] px-4 py-3 text-sm font-mono text-[var(--danger)]">
            {error}
          </div>
        )}

        <section className="rounded border border-[var(--border)] bg-[var(--surface)] p-5 md:p-6">
          <h2 className="font-display text-sm font-bold uppercase tracking-[0.15em] text-[var(--muted)] mb-4">
            Add profile
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[10px] uppercase tracking-widest text-[var(--muted)] mb-1">
                Profile name
              </label>
              <input
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                required
                className="w-full rounded border border-[var(--border)] bg-[#0a0a10] px-3 py-2 font-mono text-sm text-[var(--text)] focus:border-[var(--accent)] focus:outline-none"
                placeholder="e.g. CA India"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-widest text-[var(--muted)] mb-1">
                Keywords (comma separated)
              </label>
              <input
                value={formKeywords}
                onChange={(e) => setFormKeywords(e.target.value)}
                className="w-full rounded border border-[var(--border)] bg-[#0a0a10] px-3 py-2 font-mono text-sm text-[var(--text)] focus:border-[var(--accent)] focus:outline-none"
                placeholder="Chartered Accountant, CA, CFO"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-widest text-[var(--muted)] mb-1">
                Location
              </label>
              <input
                value={formLocation}
                onChange={(e) => setFormLocation(e.target.value)}
                className="w-full rounded border border-[var(--border)] bg-[#0a0a10] px-3 py-2 font-mono text-sm text-[var(--text)] focus:border-[var(--accent)] focus:outline-none"
                placeholder="India, UAE, Remote…"
              />
            </div>
            <div>
              <span className="block text-[10px] uppercase tracking-widest text-[var(--muted)] mb-2">
                Sites
              </span>
              <div className="flex flex-wrap gap-3">
                {PROFILE_SITE_OPTIONS.map((site) => (
                  <label
                    key={site}
                    className="flex items-center gap-2 font-mono text-xs text-[var(--text)] cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={formSites.has(site)}
                      onChange={() => toggleFormSite(site)}
                      className="accent-[var(--accent)]"
                    />
                    {site}
                  </label>
                ))}
              </div>
            </div>
            <label className="flex items-center gap-2 font-mono text-xs text-[var(--text)] cursor-pointer">
              <input
                type="checkbox"
                checked={formActive}
                onChange={(e) => setFormActive(e.target.checked)}
                className="accent-[var(--accent)]"
              />
              Active (worker runs this profile)
            </label>
            <button
              type="submit"
              disabled={saving}
              className="rounded border border-[var(--accent)] bg-transparent px-5 py-2.5 font-display text-sm font-semibold uppercase tracking-wider text-[var(--accent)] transition hover:bg-[var(--accent)] hover:text-[var(--bg)] disabled:opacity-50"
            >
              {saving ? "Saving…" : "Add profile"}
            </button>
          </form>
        </section>

        <section>
          <h2 className="font-display text-sm font-bold uppercase tracking-[0.15em] text-[var(--muted)] mb-4">
            Current profiles
          </h2>
          {loading ? (
            <p className="font-mono text-sm text-[var(--muted)]">Loading…</p>
          ) : profiles.length === 0 ? (
            <p className="font-mono text-sm text-[var(--muted)]">
              No rows in search_profiles. The worker will use{" "}
              <code className="text-[var(--accent2)]">config.py</code> until you add
              at least one active profile.
            </p>
          ) : (
            <ul className="space-y-4">
              {profiles.map((p) => (
                <li
                  key={p.id}
                  className="rounded border border-[var(--border)] bg-[var(--surface)] p-4 md:p-5"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                    <h3 className="font-display text-lg font-semibold text-white">
                      {p.name || "—"}
                    </h3>
                    <div className="flex flex-wrap items-center gap-2">
                      <label className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-[var(--muted)]">
                        <input
                          type="checkbox"
                          checked={!!p.is_active}
                          onChange={() => toggleActive(p)}
                          className="accent-[var(--accent)]"
                        />
                        Active
                      </label>
                      <button
                        type="button"
                        onClick={() => handleDelete(p.id)}
                        className="rounded border border-[var(--danger)] px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-[var(--danger)] transition hover:bg-[var(--danger)] hover:text-[var(--bg)]"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <dl className="grid gap-2 font-mono text-xs text-[var(--muted)]">
                    <div>
                      <dt className="text-[var(--border)] uppercase text-[10px] tracking-wider">
                        Keywords
                      </dt>
                      <dd className="text-[var(--text)] mt-0.5">
                        {(p.keywords ?? []).join(", ") || "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[var(--border)] uppercase text-[10px] tracking-wider">
                        Location
                      </dt>
                      <dd className="text-[var(--text)] mt-0.5">
                        {p.location || "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[var(--border)] uppercase text-[10px] tracking-wider">
                        Sites
                      </dt>
                      <dd className="text-[var(--text)] mt-0.5 flex flex-wrap gap-1.5 mt-1">
                        {(p.sites ?? []).length ? (
                          (p.sites ?? []).map((s) => (
                            <span
                              key={s}
                              className="rounded border border-[var(--border)] px-2 py-0.5 text-[10px] uppercase text-[var(--accent2)]"
                            >
                              {s}
                            </span>
                          ))
                        ) : (
                          "—"
                        )}
                      </dd>
                    </div>
                  </dl>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
