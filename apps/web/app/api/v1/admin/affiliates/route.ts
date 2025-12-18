import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function GET(req: NextRequest) {
  const token = req.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const url = new URL(req.url)
  const search = url.search

  try {
    const res = await fetch(`${API_BASE}/v1/admin/affiliates${search}`, {
      headers: { Cookie: `mr_token=${token}` },
      cache: "no-store",
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (error) {
    console.error("[Admin Proxy] affiliates error:", error)
    return NextResponse.json({ error: "Failed to fetch affiliates" }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const token = req.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const body = await req.json()
    const res = await fetch(`${API_BASE}/v1/admin/affiliates`, {
      method: "POST",
      headers: {
        Cookie: `mr_token=${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (error) {
    console.error("[Admin Proxy] create affiliate error:", error)
    return NextResponse.json({ error: "Failed to create affiliate" }, { status: 500 })
  }
}
