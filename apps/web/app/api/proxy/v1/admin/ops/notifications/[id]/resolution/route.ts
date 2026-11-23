import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

// LR-027: record whether an alert was actually received, with evidence.
export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const token = req.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }
  const { id } = await params
  if (!/^\d+$/.test(id)) {
    return NextResponse.json({ error: "Invalid notification id" }, { status: 400 })
  }
  try {
    const body = await req.json()
    const res = await fetch(`${API_BASE}/v1/admin/ops/notifications/${id}/resolution`, {
      method: "POST",
      headers: { Cookie: `mr_token=${token}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (error) {
    console.error("[Admin Proxy] ops resolution error:", error)
    return NextResponse.json({ error: "Failed to record the resolution" }, { status: 500 })
  }
}
