import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${API_BASE}/v1/auth/accept-invite`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    const data = await response.json().catch(() => ({}));
    
    const res = NextResponse.json(data, { status: response.status });

    // Set the cookie ourselves from the response body token.
    // Node.js Fetch API doesn't reliably expose Set-Cookie headers via .get().
    if (response.ok && data.access_token) {
      res.cookies.set('mr_token', data.access_token, {
        httpOnly: true,
        secure: true,
        sameSite: 'lax',
        maxAge: 3600,
        path: '/',
      });
    }

    return res;
  } catch (error) {
    console.error('[API Proxy] Failed to accept invite:', error);
    return NextResponse.json(
      { error: 'Failed to accept invitation' },
      { status: 500 }
    );
  }
}
