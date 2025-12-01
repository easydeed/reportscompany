import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com';

/**
 * GET /api/proxy/v1/onboarding
 * Get current user's onboarding status
 */
export async function GET(req: NextRequest) {
  const cookieHeader = req.headers.get('cookie') || '';

  try {
    const res = await fetch(`${API_BASE}/v1/onboarding`, {
      headers: {
        cookie: cookieHeader,
      },
      cache: 'no-store',
    });

    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: {
        'Content-Type': res.headers.get('content-type') || 'application/json',
      },
    });
  } catch (error) {
    console.error('[API Proxy] Failed to fetch onboarding status:', error);
    return NextResponse.json(
      { error: 'Failed to fetch onboarding status' },
      { status: 500 }
    );
  }
}
