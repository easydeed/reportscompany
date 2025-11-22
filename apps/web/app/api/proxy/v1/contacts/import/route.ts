import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function POST(req: NextRequest) {
  const cookieHeader = req.headers.get("cookie") || ""

  // Stream the incoming multipart body directly to the API
  const res = await fetch(`${API_BASE}/v1/contacts/import`, {
    method: "POST",
    headers: {
      cookie: cookieHeader,
      // Do not set Content-Type here; let the browser/Next handle the boundary
    } as any,
    body: req.body,
  })

  const text = await res.text()
  return new NextResponse(text, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("content-type") || "application/json",
    },
  })
}


