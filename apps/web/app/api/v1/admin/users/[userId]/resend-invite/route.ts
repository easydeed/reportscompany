import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  const token = req.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { userId } = await params

  try {
    const res = await fetch(`${API_BASE}/v1/admin/users/${userId}/resend-invite`, {
      method: "POST",
      headers: { Cookie: `mr_token=${token}` },
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (error) {
    console.error("[Admin Proxy] resend invite error:", error)
    return NextResponse.json({ error: "Failed to resend invite" }, { status: 500 })
  }
}
