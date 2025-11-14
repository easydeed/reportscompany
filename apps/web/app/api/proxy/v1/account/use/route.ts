import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

export async function POST(request: NextRequest) {
  const token = request.cookies.get('mr_token')?.value;
  
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  
  try {
    const body = await request.json();
    
    const response = await fetch(`${API_BASE}/v1/account/use`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    const data = await response.json();
    
    // Forward Set-Cookie headers if backend sends them
    const headers = new Headers();
    const setCookie = response.headers.get('set-cookie');
    if (setCookie) {
      headers.set('set-cookie', setCookie);
    }
    
    return NextResponse.json(data, { status: response.status, headers });
  } catch (error) {
    console.error('[API Proxy] Failed to switch account:', error);
    return NextResponse.json(
      { error: 'Failed to switch account' },
      { status: 500 }
    );
  }
}

