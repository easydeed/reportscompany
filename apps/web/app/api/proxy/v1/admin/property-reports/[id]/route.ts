import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = request.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { id } = await params

  try {
    const response = await fetch(`${API_BASE}/v1/admin/property-reports/${id}`, {
      headers: { Cookie: `mr_token=${token}` },
      cache: "no-store",
    })
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("[Admin Property Report Detail Proxy] Error:", error)
    return NextResponse.json({ error: "Failed to fetch" }, { status: 500 })
  }
}
