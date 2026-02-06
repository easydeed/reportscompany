import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ accountId: string }> }
) {
  const token = request.cookies.get('mr_token')?.value;

  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { accountId } = await params;

  try {
    const response = await fetch(
      `${API_BASE}/v1/admin/accounts/${accountId}/plan-usage`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        cache: 'no-store',
      }
    );

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('[API Proxy] Failed to fetch account plan-usage:', error);
    return NextResponse.json(
      { error: 'Failed to fetch account plan-usage' },
      { status: 500 }
    );
  }
}
