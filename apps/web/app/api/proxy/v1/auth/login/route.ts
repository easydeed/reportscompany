import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com';

export async function POST(request: NextRequest) {
  const startTime = Date.now();
  console.log('[LOGIN PROXY] Starting login request...');
  
  try {
    const body = await request.json();
    
    console.log(`[LOGIN PROXY] Calling ${API_BASE}/v1/auth/login...`);
    const fetchStart = Date.now();
    const response = await fetch(`${API_BASE}/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    console.log(`[LOGIN PROXY] Backend responded in ${Date.now() - fetchStart}ms, status: ${response.status}`);
    
    const data = await response.json().catch(() => ({}));
    
    const nextResponse = NextResponse.json(data, {
      status: response.status,
    });
    
    // Set the cookie ourselves from the response body token.
    // We can't rely on forwarding Set-Cookie from server-side fetch —
    // Node.js Fetch API doesn't reliably expose Set-Cookie headers via .get().
    if (response.ok && data.access_token) {
      nextResponse.cookies.set('mr_token', data.access_token, {
        httpOnly: true,
        secure: true,
        sameSite: 'lax',
        maxAge: 3600,
        path: '/',
      });
      console.log(`[LOGIN PROXY] Cookie set successfully for mr_token`);
    } else {
      console.log(`[LOGIN PROXY] No token to set cookie — status: ${response.status}`);
    }
    
    const totalTime = Date.now() - startTime;
    console.log(`[LOGIN PROXY] Total proxy execution time: ${totalTime}ms`);
    
    return nextResponse;
  } catch (error) {
    console.error('[Login Proxy] Error:', error);
    return NextResponse.json(
      { detail: 'Login proxy error' },
      { status: 500 }
    );
  }
}

