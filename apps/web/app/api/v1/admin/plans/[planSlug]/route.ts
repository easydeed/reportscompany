import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ planSlug: string }> }
) {
  const token = req.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { planSlug } = await params

  try {
    const body = await req.json()
    const res = await fetch(`${API_BASE}/v1/admin/plans/${planSlug}`, {
      method: "PATCH",
      headers: {
        Cookie: `mr_token=${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (error) {
    console.error("[Admin Proxy] update plan error:", error)
    return NextResponse.json({ error: "Failed to update plan" }, { status: 500 })
  }
}
