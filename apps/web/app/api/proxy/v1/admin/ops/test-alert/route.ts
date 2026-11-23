import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

// LR-027: request a labelled test incident; the monitor opens it on its next run.
export async function POST(req: NextRequest) {
  const token = req.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }
  try {
    const res = await fetch(`${API_BASE}/v1/admin/ops/test-alert`, {
      method: "POST",
      headers: { Cookie: `mr_token=${token}` },
      cache: "no-store",
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (error) {
    console.error("[Admin Proxy] ops test-alert error:", error)
    return NextResponse.json({ error: "Failed to request a test alert" }, { status: 500 })
  }
}
