// Proxy for leads CSV export endpoint
import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const search = url.search;

  const res = await fetch(`${API_BASE}/v1/leads/export/csv${search}`, {
    method: "GET",
    headers: {
      cookie: req.headers.get("cookie") || "",
    },
    cache: "no-store",
  });

  // For CSV, we need to pass through the response as-is
  const blob = await res.blob();
  
  return new NextResponse(blob, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("content-type") || "text/csv",
      "Content-Disposition": res.headers.get("content-disposition") || "attachment; filename=leads.csv",
    },
  });
}

