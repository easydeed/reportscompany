import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

/** GET /v1/company/settings — the company's details and who is on the account. */
export async function GET(request: NextRequest) {
  const token = request.cookies.get('mr_token')?.value;
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const response = await fetch(`${API_BASE}/v1/company/settings`, {
      headers: { 'Authorization': `Bearer ${token}` },
      cache: 'no-store',
    });
    const text = await response.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      return NextResponse.json(
        { error: 'Backend returned non-JSON response', detail: text.slice(0, 500) },
        { status: response.status }
      );
    }
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('[API Proxy] Failed to fetch company settings:', error);
    return NextResponse.json({ error: 'Failed to fetch company settings' }, { status: 500 });
  }
}
