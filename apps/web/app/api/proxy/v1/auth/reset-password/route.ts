import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const response = await fetch(`${API_BASE}/v1/auth/reset-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json().catch(() => ({}));

    const res = NextResponse.json(data, { status: response.status });

    // Set the cookie ourselves from the response body token.
    // Node.js Fetch API doesn't reliably expose Set-Cookie headers via .get().
    if (response.ok && data.access_token) {
      res.cookies.set("mr_token", data.access_token, {
        httpOnly: true,
        secure: true,
        sameSite: "lax",
        maxAge: 3600,
        path: "/",
      });
    }

    return res;
  } catch (error) {
    console.error("[Auth Proxy] reset-password error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
