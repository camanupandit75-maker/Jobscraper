import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);

/** Match worker job_hash for Latin scripts: lowercase, alphanumeric only. */
function normalizeDedupeSegment(s: string | null | undefined): string {
  return (s ?? "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]/g, "");
}

type JobRow = {
  title?: string | null;
  company?: string | null;
  hash?: string | null;
  scraped_at?: string | null;
};

/**
 * Query is ordered by scraped_at desc. Keep first row per hash and per normalized title+company.
 */
function dedupeJobsForResponse<T extends JobRow>(rows: T[] | null): T[] {
  if (!rows?.length) return [];
  const seenHash = new Set<string>();
  const seenTitleCompany = new Set<string>();
  const out: T[] = [];
  for (const row of rows) {
    const h = row.hash?.trim() ?? "";
    if (h && seenHash.has(h)) continue;
    const tc = `${normalizeDedupeSegment(row.title)}|${normalizeDedupeSegment(row.company)}`;
    if (seenTitleCompany.has(tc)) continue;
    if (h) seenHash.add(h);
    seenTitleCompany.add(tc);
    out.push(row);
  }
  return out;
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const search = searchParams.get("search") || "";
  const locationParam = searchParams.get("location") || "";
  const source = searchParams.get("source") || "";
  const status = searchParams.get("status") || "";
  const job_type = searchParams.get("job_type") || "";
  const page = Math.max(1, parseInt(searchParams.get("page") || "1", 10) || 1);
  const rawLimit = parseInt(searchParams.get("limit") || "100", 10);
  const limit = Math.min(100, Math.max(1, Number.isFinite(rawLimit) ? rawLimit : 100));
  const offset = (page - 1) * limit;

  // Avoid breaking PostgREST .or() comma-separated clauses if the user types ","
  const searchTerm = search.trim().replace(/,/g, " ");
  // ILIKE wildcards: strip % and _ so user input cannot broaden the pattern
  const locationTerm = locationParam
    .trim()
    .replace(/,/g, " ")
    .replace(/%/g, "")
    .replace(/_/g, "");

  let query = supabase
    .from("jobs")
    .select("*", { count: "exact" })
    .eq("is_hidden", false)
    .order("scraped_at", { ascending: false })
    .range(offset, offset + limit - 1);

  if (searchTerm) {
    query = query.or(
      `title.ilike.%${searchTerm}%,company.ilike.%${searchTerm}%,description.ilike.%${searchTerm}%`
    );
  }
  if (source) query = query.eq("source", source);
  if (status) query = query.eq("status", status);
  if (job_type) query = query.eq("job_type", job_type);
  if (locationTerm) {
    query = query.ilike("location", `%${locationTerm}%`);
  }

  const { data, error, count } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  const jobs = dedupeJobsForResponse(data);
  return NextResponse.json({ jobs, total: count, page, limit });
}

export async function PATCH(req: NextRequest) {
  const body = await req.json();
  const { id, ...updates } = body;
  const { error } = await supabase.from("jobs").update(updates).eq("id", id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ success: true });
}
