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

    // If successful, forward the Set-Cookie header from the backend
    const res = NextResponse.json(data, { status: response.status });

    // Copy the mr_token cookie if present
    const setCookie = response.headers.get("set-cookie");
    if (setCookie) {
      res.headers.set("set-cookie", setCookie);
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

