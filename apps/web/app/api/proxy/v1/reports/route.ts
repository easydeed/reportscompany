// apps/web/app/api/proxy/v1/reports/route.ts
// Proxy for reports API endpoints

import { NextRequest, NextResponse } from "next/server";
import { idempotentCreateUnavailable } from "../_idempotent";

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
  // LR-024 (design rev 3): a keyed create goes only to the route that honours
  // the key. An API without it answers 404 there and runs nothing, so a keyed
  // request can never create an unkeyed duplicate.
  const key = req.headers.get("idempotency-key");

  const res = await fetch(`${API_BASE}${key ? "/v1/idempotent/reports" : "/v1/reports"}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      cookie: req.headers.get("cookie") || "",
      ...(key ? { "Idempotency-Key": key } : {}),
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (key && res.status === 404) return idempotentCreateUnavailable();

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

