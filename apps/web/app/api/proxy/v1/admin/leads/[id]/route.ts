import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

/** DELETE /v1/admin/leads/{id}. The admin leads page's delete action called
 *  this path with no proxy route behind it, so it 404'd (D-314). */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = request.cookies.get("mr_token")?.value
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { id } = await params

  try {
    const response = await fetch(`${API_BASE}/v1/admin/leads/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: { Cookie: `mr_token=${token}` },
    })
    const data = await response.json().catch(() => ({}))
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("[Admin Lead Delete Proxy] Error:", error)
    return NextResponse.json({ error: "Failed to delete lead" }, { status: 500 })
  }
}
