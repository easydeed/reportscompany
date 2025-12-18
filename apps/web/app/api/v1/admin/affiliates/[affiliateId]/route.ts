import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ affiliateId: string }> }
) {
  const token = req.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { affiliateId } = await params

  try {
    const res = await fetch(`${API_BASE}/v1/admin/affiliates/${affiliateId}`, {
      headers: { Cookie: `mr_token=${token}` },
      cache: "no-store",
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (error) {
    console.error("[Admin Proxy] affiliate detail error:", error)
    return NextResponse.json({ error: "Failed to fetch affiliate" }, { status: 500 })
  }
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ affiliateId: string }> }
) {
  const token = req.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { affiliateId } = await params
  const url = new URL(req.url)
  const search = url.search

  try {
    const res = await fetch(`${API_BASE}/v1/admin/affiliates/${affiliateId}${search}`, {
      method: "PATCH",
      headers: { Cookie: `mr_token=${token}` },
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (error) {
    console.error("[Admin Proxy] affiliate update error:", error)
    return NextResponse.json({ error: "Failed to update affiliate" }, { status: 500 })
  }
}
