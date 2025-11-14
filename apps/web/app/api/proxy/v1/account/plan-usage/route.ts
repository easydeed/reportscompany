import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com';

export async function GET(request: NextRequest) {
  try {
    // Forward cookies directly to API (including mr_token)
    const cookieHeader = request.headers.get('cookie') || '';
    
    const response = await fetch(`${API_BASE}/v1/account/plan-usage`, {
      headers: {
        cookie: cookieHeader,
      },
      cache: 'no-store',
    });
    
    // Mirror backend response status and body
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      const data = await response.json();
      return NextResponse.json(data, { status: response.status });
    } else {
      // Non-JSON response
      const text = await response.text();
      console.error(`[API Proxy] Non-JSON response (${response.status}):`, text);
      return NextResponse.json(
        { error: `Backend returned ${response.status}` },
        { status: response.status }
      );
    }
  } catch (error) {
    console.error('[API Proxy] Network error fetching plan usage:', error);
    return NextResponse.json(
      { error: 'Network error contacting API' },
      { status: 500 }
    );
  }
}

