import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function GET(request: NextRequest) {
  const token = request.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const response = await fetch(`${API_BASE}/v1/admin/stats/leads`, {
      headers: { Cookie: `mr_token=${token}` },
      cache: "no-store",
    })
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("[Admin Stats Leads Proxy] Error:", error)
    return NextResponse.json({ error: "Failed to fetch" }, { status: 500 })
  }
}
