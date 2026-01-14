import { NextResponse } from "next/server"
import { cookies } from "next/headers"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE

export async function GET(request: Request) {
  const cookieStore = await cookies()
  const token = cookieStore.get("mr_token")?.value

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 })
  }

  // Forward query parameters
  const { searchParams } = new URL(request.url)
  const queryString = searchParams.toString()
  const url = `${API_BASE}/v1/property/stats${queryString ? `?${queryString}` : ''}`

  try {
    const response = await fetch(url, {
      headers: {
        Cookie: `mr_token=${token}`,
      },
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Property stats proxy error:", error)
    return NextResponse.json(
      { error: "Failed to fetch property stats" },
      { status: 500 }
    )
  }
}

