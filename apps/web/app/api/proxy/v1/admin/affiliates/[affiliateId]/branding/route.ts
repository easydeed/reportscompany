import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ affiliateId: string }> }
) {
  const token = request.cookies.get('mr_token')?.value;
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { affiliateId } = await params;

  try {
    const body = await request.json();
    const response = await fetch(
      `${API_BASE}/v1/admin/affiliates/${affiliateId}/branding`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      }
    );

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('[API Proxy] Failed to update affiliate branding:', error);
    return NextResponse.json(
      { error: 'Failed to update branding' },
      { status: 500 }
    );
  }
}
