import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com';

/**
 * POST /api/proxy/v1/onboarding/complete-step
 * Mark an onboarding step as complete
 */
export async function POST(req: NextRequest) {
  const cookieHeader = req.headers.get('cookie') || '';

  try {
    const body = await req.json();

    const res = await fetch(`${API_BASE}/v1/onboarding/complete-step`, {
      method: 'POST',
      headers: {
        cookie: cookieHeader,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: {
        'Content-Type': res.headers.get('content-type') || 'application/json',
      },
    });
  } catch (error) {
    console.error('[API Proxy] Failed to complete onboarding step:', error);
    return NextResponse.json(
      { error: 'Failed to complete step' },
      { status: 500 }
    );
  }
}
