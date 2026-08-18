import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

/**
 * GET /api/v1/email/unsubscribe
 * 
 * Handle one-click unsubscribe from email links.
 * Does NOT require authentication - uses HMAC token for verification.
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const email = searchParams.get("email");
  const token = searchParams.get("token");

  // A person clicked a link in an email. Every outcome — including every
  // failure — renders /unsubscribed, which explains what happened and gives
  // them a way to reach a human. Returning raw JSON here showed recipients
  // {"detail":"Invalid unsubscribe token"} with no way forward.
  const landing = (status: "success" | "invalid" | "error") =>
    NextResponse.redirect(new URL(`/unsubscribed?status=${status}`, request.url));

  if (!email || !token) {
    return landing("invalid");
  }

  try {
    const response = await fetch(`${API_BASE}/v1/email/unsubscribe`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        token,
        reason: "user_request",
      }),
    });

    if (!response.ok) {
      // 400 is the API's "token did not verify" (routes/unsubscribe.py:77-81);
      // anything else is a fault on our side, and the two need different copy.
      console.error(
        `[Unsubscribe] API returned ${response.status} for ${email}`
      );
      return landing(response.status === 400 ? "invalid" : "error");
    }

    return landing("success");
  } catch (error) {
    console.error("Unsubscribe error:", error);
    return landing("error");
  }
}

/**
 * POST /api/v1/email/unsubscribe
 * 
 * Handle unsubscribe via POST (for forms).
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${API_BASE}/v1/email/unsubscribe`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Unsubscribe error:", error);
    return NextResponse.json(
      { error: "Failed to process unsubscribe request" },
      { status: 500 }
    );
  }
}

