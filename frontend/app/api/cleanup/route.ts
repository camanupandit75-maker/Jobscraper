import { createClient } from "@supabase/supabase-js";
import { NextResponse } from "next/server";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);

/**
 * Same rules as worker/pipeline/writer.cleanup_old_jobs:
 * - Hidden > 7d, not bookmarked, not applied
 * - Non-bookmarked, non-applied > 30d
 * Bookmarked or applied rows are never deleted.
 */
export async function POST() {
  const now = Date.now();
  const sevenDaysAgo = new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString();
  const thirtyDaysAgo = new Date(now - 30 * 24 * 60 * 60 * 1000).toISOString();

  const { data: hiddenRows, error: err1 } = await supabase
    .from("jobs")
    .delete()
    .eq("is_hidden", true)
    .lt("scraped_at", sevenDaysAgo)
    .eq("is_bookmarked", false)
    .neq("status", "applied")
    .select("id");

  if (err1) {
    return NextResponse.json({ error: err1.message }, { status: 500 });
  }

  const { data: staleRows, error: err2 } = await supabase
    .from("jobs")
    .delete()
    .eq("is_bookmarked", false)
    .neq("status", "applied")
    .lt("scraped_at", thirtyDaysAgo)
    .select("id");

  if (err2) {
    return NextResponse.json({ error: err2.message }, { status: 500 });
  }

  const hiddenDeleted = hiddenRows?.length ?? 0;
  const staleDeleted = staleRows?.length ?? 0;
  const total = hiddenDeleted + staleDeleted;

  return NextResponse.json({
    success: true,
    hiddenOlderThan7Days: hiddenDeleted,
    staleOlderThan30Days: staleDeleted,
    totalDeleted: total,
  });
}
