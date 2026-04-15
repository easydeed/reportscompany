import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

function parseBackendResponse(text: string, status: number) {
  try {
    return NextResponse.json(JSON.parse(text), { status });
  } catch {
    return NextResponse.json(
      { error: 'Backend error', detail: text.slice(0, 500) },
      { status }
    );
  }
}

export async function GET(request: NextRequest) {
  const token = request.cookies.get('mr_token')?.value;
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const response = await fetch(`${API_BASE}/v1/company/branding`, {
      headers: { 'Authorization': `Bearer ${token}` },
      cache: 'no-store',
    });
    const text = await response.text();
    return parseBackendResponse(text, response.status);
  } catch (error) {
    console.error('[API Proxy] Failed to fetch company branding:', error);
    return NextResponse.json(
      { error: 'Failed to fetch company branding', detail: String(error) },
      { status: 500 }
    );
  }
}

export async function PATCH(request: NextRequest) {
  const token = request.cookies.get('mr_token')?.value;
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await request.json();
    const response = await fetch(`${API_BASE}/v1/company/branding`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    const text = await response.text();
    return parseBackendResponse(text, response.status);
  } catch (error) {
    console.error('[API Proxy] Failed to update company branding:', error);
    return NextResponse.json(
      { error: 'Failed to update company branding', detail: String(error) },
      { status: 500 }
    );
  }
}
