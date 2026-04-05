import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const search = searchParams.get("search") || "";
  const source = searchParams.get("source") || "";
  const status = searchParams.get("status") || "";
  const job_type = searchParams.get("job_type") || "";
  const page = parseInt(searchParams.get("page") || "1", 10);
  const limit = 50;
  const offset = (page - 1) * limit;

  // Avoid breaking PostgREST .or() comma-separated clauses if the user types ","
  const searchTerm = search.trim().replace(/,/g, " ");

  let query = supabase
    .from("jobs")
    .select("*", { count: "exact" })
    .neq("is_hidden", true)
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

  const { data, error, count } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ jobs: data, total: count, page, limit });
}

export async function PATCH(req: NextRequest) {
  const body = await req.json();
  const { id, ...updates } = body;
  const { error } = await supabase.from("jobs").update(updates).eq("id", id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ success: true });
}
