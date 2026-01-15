import { NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const url = `${API_BASE}/v1/r/${id}/analytics`

  try {
    const body = await request.json()
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "User-Agent": request.headers.get("user-agent") || "",
        "X-Forwarded-For": request.headers.get("x-forwarded-for") || "",
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Analytics proxy error:", error)
    return NextResponse.json(
      { error: "Failed to track analytics" },
      { status: 500 }
    )
  }
}

