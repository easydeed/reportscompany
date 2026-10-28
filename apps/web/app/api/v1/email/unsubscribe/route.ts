import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

/**
 * GET /api/v1/email/unsubscribe — the footer link in a scheduled email.
 *
 * IT DOES NOT UNSUBSCRIBE. It sends the reader to /unsubscribed with the
 * address and token, where one tap on "Unsubscribe" POSTs them back here.
 *
 * Why: security scanners, link checkers and corporate mail gateways (Microsoft
 * Safe Links, Mimecast, Proofpoint) open every link in a message before a person
 * sees it. When this GET did the unsubscribe, a scanner opening the footer
 * removed the contact — someone who never asked, from an agent's list, with
 * nothing recording that it was not them. A GET must be safe to repeat and
 * change nothing; the change is the POST below, which scanners do not send.
 *
 * RFC 8058 one-click (`./one-click/route.ts`) stays a direct POST: that is a mail
 * provider acting on the recipient's explicit click, and the standard requires
 * it to need no further step.
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const email = searchParams.get("email");
  const token = searchParams.get("token");

  const landing = new URL("/unsubscribed", request.url);
  if (!email || !token) {
    landing.searchParams.set("status", "invalid");
    return NextResponse.redirect(landing);
  }
  landing.searchParams.set("status", "confirm");
  landing.searchParams.set("email", email);
  landing.searchParams.set("token", token);
  return NextResponse.redirect(landing);
}

/**
 * POST /api/v1/email/unsubscribe — the confirm button on /unsubscribed.
 *
 * The only web path that records an opt-out from the footer link. Forwards
 * `{email, token, reason}` to the API, which verifies the token.
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

    if (!response.ok) {
      // The line an operator searches the logs for: an opt-out that did not
      // land. 400 is "the token did not verify"; anything else is ours.
      console.error(
        `[Unsubscribe] API returned ${response.status} for ${body?.email}`
      );
    }
    const data = await response.json().catch(() => ({}));
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Unsubscribe error:", error);
    return NextResponse.json(
      { error: "Failed to process unsubscribe request" },
      { status: 500 }
    );
  }
}

