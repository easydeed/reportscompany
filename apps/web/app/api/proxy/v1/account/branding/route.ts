import { NextRequest, NextResponse } from "next/server"

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function PATCH(req: NextRequest) {
  const cookieHeader = req.headers.get("cookie") || ""
  const body = await req.text()

  const res = await fetch(`${API_BASE}/v1/account/branding`, {
    method: "PATCH",
    headers: {
      cookie: cookieHeader,
      "Content-Type": "application/json",
    },
    body,
  })

  const text = await res.text()
  return new NextResponse(text, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("content-type") || "application/json",
    },
  })
}
