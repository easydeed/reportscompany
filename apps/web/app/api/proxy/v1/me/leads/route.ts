import { NextRequest, NextResponse } from 'next/server';
import { getApiBase } from '@/lib/get-api-base';

export async function GET(req: NextRequest) {
  try {
    const API_BASE = getApiBase();
    const cookieHeader = req.headers.get('cookie') || '';
    const searchParams = req.nextUrl.searchParams.toString();
    const url = searchParams 
      ? `${API_BASE}/v1/me/leads?${searchParams}` 
      : `${API_BASE}/v1/me/leads`;

    const res = await fetch(url, {
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
    console.error('[API Proxy] /v1/me/leads GET failed:', error);
    return NextResponse.json(
      { error: 'Network error contacting API' },
      { status: 502 }
    );
  }
}

