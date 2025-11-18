// apps/web/app/api/proxy/v1/auth/register/route.ts

import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

export async function POST(req: NextRequest) {
  const body = await req.json();

  const res = await fetch(`${API_BASE}/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    credentials: "include", // important: let browser accept mr_token cookie
  });

  const text = await res.text();

  return new NextResponse(text, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("content-type") || "application/json",
      // Forward Set-Cookie if present
      ...(res.headers.get("set-cookie")
        ? { "Set-Cookie": res.headers.get("set-cookie")! }
        : {}),
    },
  });
}
