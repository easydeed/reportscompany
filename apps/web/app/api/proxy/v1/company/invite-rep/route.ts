import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

export async function POST(request: NextRequest) {
  const token = request.cookies.get('mr_token')?.value;
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await request.json();
    const response = await fetch(`${API_BASE}/v1/company/invite-rep`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const text = await response.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = { error: 'Backend error', detail: text.slice(0, 500) };
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('[API Proxy] invite-rep error:', error);
    return NextResponse.json(
      { error: 'Failed to invite rep', detail: String(error) },
      { status: 500 }
    );
  }
}
