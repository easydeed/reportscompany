// Proxy for property report settings API endpoints
import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  const res = await fetch(`${API_BASE}/v1/property/reports/${id}/settings`, {
    method: "GET",
    headers: {
      cookie: req.headers.get("cookie") || "",
    },
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

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await req.json();

  const res = await fetch(`${API_BASE}/v1/property/reports/${id}/settings`, {
    method: "PATCH",
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

