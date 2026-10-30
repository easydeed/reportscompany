import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

// D-079: the account's own postal address, for the footer of the mail it sends.

function parseBackendResponse(text: string, status: number) {
  try {
    return NextResponse.json(JSON.parse(text), { status });
  } catch {
    return NextResponse.json({ error: 'Backend error', detail: text.slice(0, 500) }, { status });
  }
}

async function forward(request: NextRequest, method: 'GET' | 'PUT') {
  const token = request.cookies.get('mr_token')?.value;
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  try {
    const response = await fetch(`${API_BASE}/v1/account/postal-address`, {
      method,
      headers: { 'Authorization': `Bearer ${token}`, ...(method === 'PUT' ? { 'Content-Type': 'application/json' } : {}) },
      body: method === 'PUT' ? await request.text() : undefined,
      cache: 'no-store',
    });
    return parseBackendResponse(await response.text(), response.status);
  } catch (error) {
    console.error('[API Proxy] postal address:', error);
    return NextResponse.json({ error: 'Failed to reach the API', detail: String(error) }, { status: 500 });
  }
}

export async function GET(request: NextRequest) {
  return forward(request, 'GET');
}

export async function PUT(request: NextRequest) {
  return forward(request, 'PUT');
}
