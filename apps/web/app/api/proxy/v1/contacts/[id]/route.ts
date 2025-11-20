import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com';

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const cookieHeader = req.headers.get('cookie') || '';
  const { id } = await params;
  
  const res = await fetch(`${API_BASE}/v1/contacts/${id}`, {
    headers: {
      cookie: cookieHeader,
    },
    cache: 'no-store',
  });

  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: {
      'Content-Type': res.headers.get('content-type') || 'application/json',
    },
  });
}

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const cookieHeader = req.headers.get('cookie') || '';
  const { id } = await params;
  const body = await req.text();
  
  const res = await fetch(`${API_BASE}/v1/contacts/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      cookie: cookieHeader,
    },
    body,
    cache: 'no-store',
  });

  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: {
      'Content-Type': res.headers.get('content-type') || 'application/json',
    },
  });
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const cookieHeader = req.headers.get('cookie') || '';
  const { id } = await params;
  
  const res = await fetch(`${API_BASE}/v1/contacts/${id}`, {
    method: 'DELETE',
    headers: {
      cookie: cookieHeader,
    },
    cache: 'no-store',
  });

  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: {
      'Content-Type': res.headers.get('content-type') || 'application/json',
    },
  });
}

