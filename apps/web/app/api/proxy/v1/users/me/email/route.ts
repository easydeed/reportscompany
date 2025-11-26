import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com';

/**
 * PATCH /api/proxy/v1/users/me/email
 * Change user's email address
 *
 * Requires:
 * - new_email: string (valid email)
 * - current_password: string (for verification)
 */
export async function PATCH(req: NextRequest) {
  const cookieHeader = req.headers.get('cookie') || '';

  try {
    const body = await req.json();

    const res = await fetch(`${API_BASE}/v1/users/me/email`, {
      method: 'PATCH',
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
    console.error('[API Proxy] Failed to change email:', error);
    return NextResponse.json(
      { error: 'Failed to change email' },
      { status: 500 }
    );
  }
}
