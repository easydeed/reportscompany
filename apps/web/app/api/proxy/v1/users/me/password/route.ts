import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com';

/**
 * POST /api/proxy/v1/users/me/password
 * Change user's password
 *
 * Requires:
 * - current_password: string
 * - new_password: string (min 8 chars)
 *
 * Side effects:
 * - Logs out other sessions by issuing new JWT
 */
export async function POST(req: NextRequest) {
  const cookieHeader = req.headers.get('cookie') || '';

  try {
    const body = await req.json();

    const res = await fetch(`${API_BASE}/v1/users/me/password`, {
      method: 'POST',
      headers: {
        cookie: cookieHeader,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const text = await res.text();

    // Forward Set-Cookie headers (new JWT token)
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
    console.error('[API Proxy] Failed to change password:', error);
    return NextResponse.json(
      { error: 'Failed to change password' },
      { status: 500 }
    );
  }
}
