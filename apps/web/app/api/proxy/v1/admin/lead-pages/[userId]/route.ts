import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  const token = request.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { userId } = await params
  const { searchParams } = new URL(request.url)
  const queryString = searchParams.toString()
  const url = `${API_BASE}/v1/admin/lead-pages/${userId}${queryString ? `?${queryString}` : ""}`

  try {
    const response = await fetch(url, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
    })
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("[Admin Lead Pages Toggle Proxy] Error:", error)
    return NextResponse.json({ error: "Failed to update" }, { status: 500 })
  }
}
