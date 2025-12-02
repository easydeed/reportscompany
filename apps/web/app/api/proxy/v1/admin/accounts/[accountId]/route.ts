import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ accountId: string }> }
) {
  const token = request.cookies.get('mr_token')?.value;

  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { accountId } = await params;
  const { searchParams } = new URL(request.url);
  const queryString = searchParams.toString();

  try {
    const response = await fetch(
      `${API_BASE}/v1/admin/accounts/${accountId}${queryString ? `?${queryString}` : ''}`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('[API Proxy] Failed to update account:', error);
    return NextResponse.json(
      { error: 'Failed to update account' },
      { status: 500 }
    );
  }
}
