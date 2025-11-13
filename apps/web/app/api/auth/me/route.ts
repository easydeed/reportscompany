import { cookies } from "next/headers"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!

export async function GET() {
  const cookieStore = await cookies()
  const token = cookieStore.get("mr_token")?.value
  if (!token) return new Response(JSON.stringify({ error: "unauthorized" }), { status: 401 })

  const res = await fetch(`${API_BASE}/v1/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  })
  const buf = await res.arrayBuffer()
  return new Response(buf, { status: res.status, statusText: res.statusText, headers: res.headers })
}

