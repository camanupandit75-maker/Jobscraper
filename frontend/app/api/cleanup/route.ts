import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

/**
 * Default cleanup (no body / no beforeDate):
 * 1) is_hidden = true AND scraped_at < now - 7 days
 * 2) is_bookmarked = false AND status != 'applied' AND scraped_at < now - 30 days
 *
 * With { beforeDate: "YYYY-MM-DD" }:
 * Deletes non-bookmarked, non-applied jobs with scraped_at before that date (UTC midnight).
 */
export async function POST(req: NextRequest) {
  let beforeDate = "";
  try {
    const body = await req.json();
    if (body && typeof body.beforeDate === "string") {
      beforeDate = body.beforeDate.trim();
    }
  } catch {
    /* empty body */
  }

  if (beforeDate) {
    if (!DATE_RE.test(beforeDate)) {
      return NextResponse.json(
        { error: "beforeDate must be YYYY-MM-DD", deleted: 0 },
        { status: 400 }
      );
    }
    const cutoff = `${beforeDate}T00:00:00.000Z`;
    const { data, error } = await supabase
      .from("jobs")
      .delete()
      .eq("is_bookmarked", false)
      .neq("status", "applied")
      .lt("scraped_at", cutoff)
      .select("id");

    if (error) {
      return NextResponse.json({ error: error.message, deleted: 0 }, { status: 500 });
    }
    const deleted = data?.length ?? 0;
    return NextResponse.json({ deleted, beforeDate });
  }

  const now = Date.now();
  const sevenDaysAgo = new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString();
  const thirtyDaysAgo = new Date(now - 30 * 24 * 60 * 60 * 1000).toISOString();

  const { data: hiddenRows, error: err1 } = await supabase
    .from("jobs")
    .delete()
    .eq("is_hidden", true)
    .lt("scraped_at", sevenDaysAgo)
    .select("id");

  if (err1) {
    return NextResponse.json({ error: err1.message, deleted: 0 }, { status: 500 });
  }

  const { data: staleRows, error: err2 } = await supabase
    .from("jobs")
    .delete()
    .eq("is_bookmarked", false)
    .neq("status", "applied")
    .lt("scraped_at", thirtyDaysAgo)
    .select("id");

  if (err2) {
    return NextResponse.json({ error: err2.message, deleted: 0 }, { status: 500 });
  }

  const hiddenDeleted = hiddenRows?.length ?? 0;
  const staleDeleted = staleRows?.length ?? 0;
  const deleted = hiddenDeleted + staleDeleted;

  return NextResponse.json({
    deleted,
    hiddenOlderThan7Days: hiddenDeleted,
    staleOlderThan30Days: staleDeleted,
  });
}
