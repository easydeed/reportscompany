import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

/**
 * POST /api/v1/email/unsubscribe/one-click?email=...&token=...
 *
 * RFC 8058 one-click unsubscribe. The caller is the recipient's mail provider,
 * not a person — this is what Gmail and Yahoo invoke behind the native
 * "Unsubscribe" control next to the sender name, driven by the
 * List-Unsubscribe / List-Unsubscribe-Post headers set in
 * apps/worker/src/worker/email/send.py.
 *
 * The credential is in the query string because that is the only place a mail
 * provider will carry it: providers send a fixed `List-Unsubscribe=One-Click`
 * form body and never our JSON shape. The body is ignored.
 *
 * POST ONLY, and there is deliberately no GET export. Next.js answers an
 * unmatched method with 405, which is the behaviour we want: security
 * scanners, link prefetchers and corporate mail gateways routinely GET every
 * URL in a message. A GET-reachable one-click endpoint would unsubscribe
 * people who never clicked anything, indistinguishably from a real opt-out.
 * Do not add a GET handler here.
 *
 * The human-facing path is the footer link, which lands on /unsubscribed —
 * see ../route.ts. This endpoint returns no page; nobody is looking at it.
 */
export async function POST(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const email = searchParams.get("email");
  const token = searchParams.get("token");

  if (!email || !token) {
    return NextResponse.json(
      { error: "Missing email or token parameter" },
      { status: 400 }
    );
  }

  try {
    const response = await fetch(
      `${API_BASE}/v1/email/unsubscribe/one-click` +
        `?email=${encodeURIComponent(email)}&token=${encodeURIComponent(token)}`,
      { method: "POST" }
    );

    if (!response.ok) {
      console.error(
        `[Unsubscribe one-click] API returned ${response.status} for ${email}`
      );
      return NextResponse.json(
        { error: "Unsubscribe failed" },
        { status: response.status }
      );
    }

    return NextResponse.json({ message: "Email unsubscribed" }, { status: 200 });
  } catch (error) {
    console.error("[Unsubscribe one-click] error:", error);
    return NextResponse.json(
      { error: "Failed to process unsubscribe request" },
      { status: 500 }
    );
  }
}
