import { NextResponse } from "next/server";

// This endpoint calls your Railway worker's HTTP trigger endpoint
// Set RAILWAY_TRIGGER_URL in your Vercel env vars to the Railway webhook URL
export async function POST() {
  const triggerUrl = process.env.RAILWAY_TRIGGER_URL;
  if (!triggerUrl) {
    return NextResponse.json({
      message: "No trigger URL configured. Scraper runs automatically.",
    });
  }
  try {
    await fetch(triggerUrl, { method: "POST" });
    return NextResponse.json({ success: true, message: "Scrape triggered!" });
  } catch {
    return NextResponse.json({ error: "Failed to trigger scrape" }, { status: 500 });
  }
}
