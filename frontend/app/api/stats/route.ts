import { createClient } from "@supabase/supabase-js";
import { NextResponse } from "next/server";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);

export async function GET() {
  const startOfDay = new Date();
  startOfDay.setUTCHours(0, 0, 0, 0);

  const [total, newToday, bookmarked, applied, lastRun] = await Promise.all([
    supabase.from("jobs").select("id", { count: "exact", head: true }).eq("is_hidden", false),
    supabase
      .from("jobs")
      .select("id", { count: "exact", head: true })
      .eq("is_hidden", false)
      .gte("scraped_at", startOfDay.toISOString()),
    supabase.from("jobs").select("id", { count: "exact", head: true }).eq("is_bookmarked", true),
    supabase.from("jobs").select("id", { count: "exact", head: true }).eq("status", "applied"),
    supabase
      .from("scrape_runs")
      .select("id,ended_at,jobs_added,source,status,started_at")
      .order("started_at", { ascending: false })
      .limit(10),
  ]);

  return NextResponse.json({
    total: total.count ?? 0,
    newToday: newToday.count ?? 0,
    bookmarked: bookmarked.count ?? 0,
    applied: applied.count ?? 0,
    lastRuns: lastRun.data ?? [],
  });
}
