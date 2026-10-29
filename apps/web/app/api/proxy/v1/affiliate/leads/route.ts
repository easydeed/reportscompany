import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

/** GET /v1/affiliate/leads — the book's homeowner leads: counts per agent and a feed, no contact details. */
export async function GET(request: NextRequest) {
  const token = request.cookies.get('mr_token')?.value;
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const qs = searchParams.toString();
  const url = `${API_BASE}/v1/affiliate/leads${qs ? `?${qs}` : ''}`;

  try {
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` },
      cache: 'no-store',
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('[API Proxy] Failed to fetch leads:', error);
    return NextResponse.json({ error: 'Failed to fetch leads' }, { status: 500 });
  }
}
