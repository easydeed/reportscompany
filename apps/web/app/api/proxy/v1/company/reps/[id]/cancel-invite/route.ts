import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

/** POST /v1/company/reps/{id}/cancel-invite (#224). */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = request.cookies.get('mr_token')?.value;
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { id } = await params;

  try {
    const body = await request.text();
    const response = await fetch(`${API_BASE}/v1/company/reps/${encodeURIComponent(id)}/cancel-invite`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: body || undefined,
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
    console.error('[API Proxy] cancel-invite error:', error);
    return NextResponse.json({ error: 'Failed to cancel-invite', detail: String(error) }, { status: 500 });
  }
}
