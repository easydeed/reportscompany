// apps/web/app/api/proxy/v1/reports/route.ts
// Proxy for reports API endpoints

import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

export async function GET(req: NextRequest) {
  // Forward query params (e.g., ?limit=10&offset=0)
  const url = new URL(req.url);
  const search = url.search;

  const res = await fetch(`${API_BASE}/v1/reports${search}`, {
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

export async function POST(req: NextRequest) {
  const body = await req.json();
  // LR-024: the wizard's Idempotency-Key must reach the API, or a retry after
  // a lost answer creates a second report.
  const key = req.headers.get("idempotency-key");

  const res = await fetch(`${API_BASE}/v1/reports`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      cookie: req.headers.get("cookie") || "",
      ...(key ? { "Idempotency-Key": key } : {}),
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const text = await res.text();
  const replayed = res.headers.get("idempotent-replayed");

  return new NextResponse(text, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("content-type") || "application/json",
      ...(replayed ? { "Idempotent-Replayed": replayed } : {}),
    },
  });
}

