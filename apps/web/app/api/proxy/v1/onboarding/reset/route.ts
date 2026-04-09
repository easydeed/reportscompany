import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com';

/**
 * POST /api/proxy/v1/onboarding/reset
 * Reset onboarding progress (for re-onboarding)
 */
export async function POST(req: NextRequest) {
  const cookieHeader = req.headers.get('cookie') || '';

  try {
    const res = await fetch(`${API_BASE}/v1/onboarding/reset`, {
      method: 'POST',
      headers: {
        cookie: cookieHeader,
        'Content-Type': 'application/json',
      },
    });

    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: {
        'Content-Type': res.headers.get('content-type') || 'application/json',
      },
    });
  } catch (error) {
    console.error('[API Proxy] Failed to reset onboarding:', error);
    return NextResponse.json(
      { error: 'Failed to reset onboarding' },
      { status: 500 }
    );
  }
}
