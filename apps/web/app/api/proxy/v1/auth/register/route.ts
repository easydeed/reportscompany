// apps/web/app/api/proxy/v1/auth/register/route.ts

import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const res = await fetch(`${API_BASE}/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json().catch(() => ({}));

    const nextResponse = NextResponse.json(data, { status: res.status });

    // Set the cookie ourselves from the response body token.
    // Node.js Fetch API doesn't reliably expose Set-Cookie headers via .get().
    if (res.ok && data.access_token) {
      nextResponse.cookies.set("mr_token", data.access_token, {
        httpOnly: true,
        secure: true,
        sameSite: "lax",
        maxAge: 7 * 24 * 60 * 60, // 7 days for new users (matches backend)
        path: "/",
      });
    }

    return nextResponse;
  } catch (error) {
    console.error("[Auth Proxy] register error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
