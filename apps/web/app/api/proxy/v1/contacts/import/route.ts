import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://reportscompany.onrender.com"

export async function POST(req: NextRequest) {
  const cookieHeader = req.headers.get("cookie") || ""

  let form: FormData
  try {
    form = await req.formData()
  } catch {
    return NextResponse.json({ detail: "Invalid multipart upload" }, { status: 400 })
  }
  const res = await fetch(`${API_BASE}/v1/contacts/import`, {
    method: "POST",
    headers: { cookie: cookieHeader },
    body: form,
  })

  const text = await res.text()
  return new NextResponse(text, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("content-type") || "application/json",
    },
  })
}
