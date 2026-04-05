import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);

export async function GET() {
  const { data, error } = await supabase
    .from("search_profiles")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ profiles: data ?? [] });
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { name, keywords, location, sites, is_active } = body;

  let kw: string[] = [];
  if (Array.isArray(keywords)) {
    kw = keywords.map((k) => String(k).trim()).filter(Boolean);
  } else if (typeof keywords === "string") {
    kw = keywords.split(",").map((s) => s.trim()).filter(Boolean);
  }

  let siteList: string[] = [];
  if (Array.isArray(sites)) {
    siteList = sites.map((s) => String(s).trim()).filter(Boolean);
  }

  const { data, error } = await supabase
    .from("search_profiles")
    .insert({
      name: name ?? null,
      keywords: kw.length ? kw : null,
      location: location ?? null,
      sites: siteList.length ? siteList : null,
      is_active: is_active !== false,
    })
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ profile: data });
}

/** Toggle or update is_active (and optional fields). */
export async function PATCH(req: NextRequest) {
  const body = await req.json();
  const { id, is_active, name, keywords, location, sites } = body;
  if (!id) {
    return NextResponse.json({ error: "Missing id" }, { status: 400 });
  }

  const updates: Record<string, unknown> = {};
  if (typeof is_active === "boolean") updates.is_active = is_active;
  if (name !== undefined) updates.name = name;
  if (keywords !== undefined) {
    updates.keywords = Array.isArray(keywords)
      ? keywords.map(String).filter(Boolean)
      : String(keywords)
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
  }
  if (location !== undefined) updates.location = location;
  if (sites !== undefined) {
    updates.sites = Array.isArray(sites) ? sites.map(String).filter(Boolean) : [];
  }

  if (Object.keys(updates).length === 0) {
    return NextResponse.json({ error: "No fields to update" }, { status: 400 });
  }

  const { data, error } = await supabase
    .from("search_profiles")
    .update(updates)
    .eq("id", id)
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ profile: data });
}

export async function DELETE(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const id = searchParams.get("id");
  if (!id) {
    return NextResponse.json({ error: "Missing id query parameter" }, { status: 400 });
  }

  const { error } = await supabase.from("search_profiles").delete().eq("id", id);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ success: true });
}
