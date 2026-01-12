// Proxy for property comparables API endpoint
import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

export async function POST(req: NextRequest) {
  const body = await req.json();

  const res = await fetch(`${API_BASE}/v1/property/comparables`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      cookie: req.headers.get("cookie") || "",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const text = await res.text();
  
  return new NextResponse(text, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("content-type") || "application/json",
    },
  });
}

