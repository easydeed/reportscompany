import { NextResponse } from "next/server"
import { cookies } from "next/headers"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE

export async function GET() {
  const cookieStore = await cookies()
  const token = cookieStore.get("mr_token")?.value

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 })
  }

  try {
    const response = await fetch(`${API_BASE}/v1/admin/metrics/devices`, {
      headers: {
        Cookie: `mr_token=${token}`,
      },
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Admin metrics devices proxy error:", error)
    return NextResponse.json(
      { error: "Failed to fetch device breakdown" },
      { status: 500 }
    )
  }
}

