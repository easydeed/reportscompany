import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com';

/**
 * GET /api/proxy/v1/users/me
 * Get current user's profile information
 */
export async function GET(req: NextRequest) {
  const cookieHeader = req.headers.get('cookie') || '';

  try {
    const res = await fetch(`${API_BASE}/v1/users/me`, {
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
    console.error('[API Proxy] Failed to fetch user profile:', error);
    return NextResponse.json(
      { error: 'Failed to fetch user profile' },
      { status: 500 }
    );
  }
}

/**
 * PATCH /api/proxy/v1/users/me
 * Update current user's profile information
 */
export async function PATCH(req: NextRequest) {
  const cookieHeader = req.headers.get('cookie') || '';

  try {
    const body = await req.json();

    const res = await fetch(`${API_BASE}/v1/users/me`, {
      method: 'PATCH',
      headers: {
        cookie: cookieHeader,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const text = await res.text();

    // Forward any Set-Cookie headers from the backend
    const response = new NextResponse(text, {
      status: res.status,
      headers: {
        'Content-Type': res.headers.get('content-type') || 'application/json',
      },
    });

    const setCookie = res.headers.get('set-cookie');
    if (setCookie) {
      response.headers.set('Set-Cookie', setCookie);
    }

    return response;
  } catch (error) {
    console.error('[API Proxy] Failed to update user profile:', error);
    return NextResponse.json(
      { error: 'Failed to update user profile' },
      { status: 500 }
    );
  }
}
