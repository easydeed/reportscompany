import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  const token = req.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { userId } = await params

  try {
    const res = await fetch(`${API_BASE}/v1/admin/users/${userId}`, {
      headers: { Cookie: `mr_token=${token}` },
      cache: "no-store",
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (error) {
    console.error("[Admin Proxy] user detail error:", error)
    return NextResponse.json({ error: "Failed to fetch user" }, { status: 500 })
  }
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  const token = req.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { userId } = await params
  const url = new URL(req.url)
  const search = url.search

  try {
    const res = await fetch(`${API_BASE}/v1/admin/users/${userId}${search}`, {
      method: "PATCH",
      headers: { Cookie: `mr_token=${token}` },
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (error) {
    console.error("[Admin Proxy] user update error:", error)
    return NextResponse.json({ error: "Failed to update user" }, { status: 500 })
  }
}
