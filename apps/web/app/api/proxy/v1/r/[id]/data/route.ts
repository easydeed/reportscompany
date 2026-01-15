import { NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const url = `${API_BASE}/v1/r/${id}/data`

  try {
    const response = await fetch(url, {
      headers: {
        "User-Agent": request.headers.get("user-agent") || "",
        "X-Forwarded-For": request.headers.get("x-forwarded-for") || "",
      },
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Mobile report data proxy error:", error)
    return NextResponse.json(
      { error: "Failed to fetch report data" },
      { status: 500 }
    )
  }
}

