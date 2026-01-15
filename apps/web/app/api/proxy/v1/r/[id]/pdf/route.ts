import { NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const url = `${API_BASE}/v1/r/${id}/pdf`

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "User-Agent": request.headers.get("user-agent") || "",
        "X-Forwarded-For": request.headers.get("x-forwarded-for") || "",
      },
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("PDF generation proxy error:", error)
    return NextResponse.json(
      { error: "Failed to generate PDF" },
      { status: 500 }
    )
  }
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const url = `${API_BASE}/v1/r/${id}/pdf/status`

  try {
    const response = await fetch(url)
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("PDF status proxy error:", error)
    return NextResponse.json(
      { error: "Failed to check PDF status" },
      { status: 500 }
    )
  }
}

