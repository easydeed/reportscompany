import { NextRequest, NextResponse } from 'next/server';
import { idempotentCreateUnavailable } from '../_idempotent';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

export async function GET(request: NextRequest) {
  const token = request.cookies.get('mr_token')?.value;
  
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  
  try {
    const { searchParams } = new URL(request.url);
    const qs = searchParams.toString();
    const response = await fetch(`${API_BASE}/v1/schedules${qs ? `?${qs}` : ''}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      cache: 'no-store',
    });
    
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('[API Proxy] Failed to fetch schedules:', error);
    return NextResponse.json(
      { error: 'Failed to fetch schedules' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  const token = request.cookies.get('mr_token')?.value;
  
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  
  try {
    const body = await request.json();
    // LR-024 (design rev 3): a keyed create goes only to the route that
    // honours the key. An API without it answers 404 there and runs nothing.
    const key = request.headers.get('idempotency-key');

    const response = await fetch(`${API_BASE}${key ? '/v1/idempotent/schedules' : '/v1/schedules'}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...(key ? { 'Idempotency-Key': key } : {}),
      },
      body: JSON.stringify(body),
    });

    if (key && response.status === 404) return idempotentCreateUnavailable();

    const data = await response.json();
    const replayed = response.headers.get('idempotent-replayed');
    return NextResponse.json(data, {
      status: response.status,
      headers: replayed ? { 'Idempotent-Replayed': replayed } : undefined,
    });
  } catch (error) {
    console.error('[API Proxy] Failed to create schedule:', error);
    return NextResponse.json(
      { error: 'Failed to create schedule' },
      { status: 500 }
    );
  }
}

