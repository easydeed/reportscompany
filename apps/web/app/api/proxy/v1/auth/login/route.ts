import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${API_BASE}/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    const data = await response.text();
    
    // Forward Set-Cookie headers from backend
    const setCookieHeader = response.headers.get('set-cookie');
    const nextResponse = new NextResponse(data, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('content-type') || 'application/json',
      },
    });
    
    // If backend set a cookie, forward it
    if (setCookieHeader) {
      nextResponse.headers.set('Set-Cookie', setCookieHeader);
    }
    
    return nextResponse;
  } catch (error) {
    console.error('[Login Proxy] Error:', error);
    return NextResponse.json(
      { detail: 'Login proxy error' },
      { status: 500 }
    );
  }
}

