import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

/**
 * POST /api/proxy/v1/branding/test-email
 * 
 * Proxy for sending test branded email.
 * 
 * Pass B4.2: Test Email Proxy
 */
export async function POST(request: NextRequest) {
  const cookieStore = await cookies();
  const token = cookieStore.get("mr_token")?.value;

  if (!token) {
    return NextResponse.json(
      { error: "Unauthorized", detail: "Please log in" },
      { status: 401 }
    );
  }

  try {
    const body = await request.json();

    const response = await fetch(`${API_BASE}/v1/branding/test-email`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Cookie: `mr_token=${token}`,
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(`[Test Email Proxy] Backend error: ${response.status}`, data);
      return NextResponse.json(
        { error: data.detail || "Failed to send test email" },
        { status: response.status }
      );
    }

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("[Test Email Proxy] Error:", error);
    return NextResponse.json(
      { error: "Test email failed", detail: String(error) },
      { status: 500 }
    );
  }
}

