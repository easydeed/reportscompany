// Proxy for property report QR regeneration endpoint
import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  const res = await fetch(`${API_BASE}/v1/property/reports/${id}/regenerate-qr`, {
    method: "POST",
    headers: {
      cookie: req.headers.get("cookie") || "",
    },
    cache: "no-store",
  });

  const text = await res.text();
  
  return new NextResponse(text, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("content-type") || "application/json",
    },
  });
}

