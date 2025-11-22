import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function GET(req: NextRequest) {
  const cookieHeader = req.headers.get("cookie") || ""

  const res = await fetch(`${API_BASE}/v1/contact-groups`, {
    headers: {
      cookie: cookieHeader,
    },
    cache: "no-store",
  })

  const text = await res.text()
  return new NextResponse(text, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("content-type") || "application/json",
    },
  })
}

export async function POST(req: NextRequest) {
  const cookieHeader = req.headers.get("cookie") || ""
  const body = await req.text()

  const res = await fetch(`${API_BASE}/v1/contact-groups`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      cookie: cookieHeader,
    },
    body,
    cache: "no-store",
  })

  const text = await res.text()
  return new NextResponse(text, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("content-type") || "application/json",
    },
  })
}


