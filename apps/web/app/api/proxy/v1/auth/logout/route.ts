import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function POST(req: NextRequest) {
  try {
    const token = req.cookies.get("mr_token")?.value
    
    // Try to call backend logout if token exists
    if (token) {
      await fetch(`${API_BASE}/v1/auth/logout`, {
        method: "POST",
        headers: { Cookie: `mr_token=${token}` },
      }).catch(() => {})
    }

    // Clear the cookie by setting it to expire immediately
    const response = NextResponse.json({ success: true })
    response.cookies.set("mr_token", "", {
      expires: new Date(0),
      path: "/",
    })
    
    return response
  } catch (error) {
    console.error("[Auth Proxy] logout error:", error)
    // Still clear cookie even if backend call fails
    const response = NextResponse.json({ success: true })
    response.cookies.set("mr_token", "", {
      expires: new Date(0),
      path: "/",
    })
    return response
  }
}
