import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";
import ExcelJS from "exceljs";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const source = searchParams.get("source") || "";
  const status = searchParams.get("status") || "";
  const job_type = searchParams.get("job_type") || "";
  const search = searchParams.get("search") || "";
  const locationParam = searchParams.get("location") || "";
  const locationTerm = locationParam
    .trim()
    .replace(/,/g, " ")
    .replace(/%/g, "")
    .replace(/_/g, "");

  let query = supabase
    .from("jobs")
    .select("title,company,location,job_type,salary,url,source,posted_at,status,scraped_at")
    .eq("is_hidden", false)
    .order("scraped_at", { ascending: false })
    .limit(500);

  if (search) {
    query = query.or(`title.ilike.%${search}%,company.ilike.%${search}%`);
  }
  if (locationTerm) {
    query = query.ilike("location", `%${locationTerm}%`);
  }
  if (source) query = query.eq("source", source);
  if (status) query = query.eq("status", status);
  if (job_type) query = query.eq("job_type", job_type);

  const { data, error } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  const workbook = new ExcelJS.Workbook();
  const sheet = workbook.addWorksheet("Jobs");

  sheet.columns = [
    { header: "Title", key: "title", width: 40 },
    { header: "Company", key: "company", width: 30 },
    { header: "Location", key: "location", width: 25 },
    { header: "Type", key: "job_type", width: 15 },
    { header: "Salary", key: "salary", width: 20 },
    { header: "Source", key: "source", width: 15 },
    { header: "Status", key: "status", width: 15 },
    { header: "Posted", key: "posted_at", width: 20 },
    { header: "Scraped", key: "scraped_at", width: 20 },
    { header: "URL", key: "url", width: 60 },
  ];

  sheet.getRow(1).font = { bold: true };
  sheet.getRow(1).fill = {
    type: "pattern",
    pattern: "solid",
    fgColor: { argb: "FF1a1a2e" },
  };
  sheet.getRow(1).font = { bold: true, color: { argb: "FFFFFFFF" } };

  data?.forEach((job) => sheet.addRow(job));

  const buffer = await workbook.xlsx.writeBuffer();
  return new NextResponse(buffer, {
    headers: {
      "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "Content-Disposition": `attachment; filename="jobs-${Date.now()}.xlsx"`,
    },
  });
}
