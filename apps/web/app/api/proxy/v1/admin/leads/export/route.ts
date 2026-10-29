import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

/** GET /v1/admin/leads/export — a CSV, passed through as bytes with its own
 *  content type and filename. The page called it with no proxy route (D-314). */
export async function GET(request: NextRequest) {
  const token = request.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const response = await fetch(`${API_BASE}/v1/admin/leads/export`, {
      headers: { Cookie: `mr_token=${token}` },
      cache: "no-store",
    })
    const headers = new Headers()
    for (const name of ["content-type", "content-disposition"]) {
      const value = response.headers.get(name)
      if (value) headers.set(name, value)
    }
    return new NextResponse(await response.arrayBuffer(), { status: response.status, headers })
  } catch (error) {
    console.error("[Admin Leads Export Proxy] Error:", error)
    return NextResponse.json({ error: "Failed to export leads" }, { status: 500 })
  }
}
