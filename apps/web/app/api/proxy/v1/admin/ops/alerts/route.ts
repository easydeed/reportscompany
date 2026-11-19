import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

// LR-027: open incidents and notifications needing reconciliation (platform admins only).
export async function GET(req: NextRequest) {
  const token = req.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }
  try {
    const res = await fetch(`${API_BASE}/v1/admin/ops/alerts`, {
      headers: { Cookie: `mr_token=${token}` },
      cache: "no-store",
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (error) {
    console.error("[Admin Proxy] ops alerts error:", error)
    return NextResponse.json({ error: "Failed to fetch alerts" }, { status: 500 })
  }
}
