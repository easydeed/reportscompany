import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function GET(request: NextRequest) {
  const token = request.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { searchParams } = new URL(request.url)
  const queryString = searchParams.toString()
  const url = `${API_BASE}/v1/admin/emails${queryString ? `?${queryString}` : ""}`

  try {
    const response = await fetch(url, {
      headers: { Cookie: `mr_token=${token}` },
      cache: "no-store",
    })
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("[Admin Emails Proxy] Error:", error)
    return NextResponse.json({ error: "Failed to fetch admin emails" }, { status: 500 })
  }
}
