import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = request.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { id } = await params

  try {
    const response = await fetch(`${API_BASE}/v1/admin/reports/${id}/retry`, {
      method: "POST",
      headers: { Cookie: `mr_token=${token}` },
    })
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("[Admin Report Retry Proxy] Error:", error)
    return NextResponse.json({ error: "Failed to retry report" }, { status: 500 })
  }
}
