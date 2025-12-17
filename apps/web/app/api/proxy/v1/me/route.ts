import { NextRequest, NextResponse } from 'next/server';

import { getApiBase } from '@/lib/get-api-base'

export async function GET(req: NextRequest) {
  try {
    const API_BASE = getApiBase()
    const cookieHeader = req.headers.get('cookie') || ''

    const res = await fetch(`${API_BASE}/v1/me`, {
      headers: {
        cookie: cookieHeader,
      },
      cache: 'no-store',
    })

    const text = await res.text()
    return new NextResponse(text, {
      status: res.status,
      headers: {
        'Content-Type': res.headers.get('content-type') || 'application/json',
      },
    })
  } catch (error) {
    console.error('[API Proxy] /v1/me failed:', error)
    return NextResponse.json(
      { error: 'Network error contacting API' },
      { status: 502 }
    )
  }
}

