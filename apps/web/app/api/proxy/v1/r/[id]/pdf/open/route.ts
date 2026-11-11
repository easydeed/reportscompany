import { NextResponse } from "next/server"

/**
 * "Open your PDF report" (LR-022; Codex, #283).
 *
 * The link on the page points here, not at a signed R2 URL: a signed URL held
 * on an open page stops working when its signature does. Each open asks the
 * API's status route, which signs a new short-lived link to the SAME stored
 * PDF and never queues or renders anything, and redirects to it. Anything but
 * a ready PDF goes back to the report, where the button shows what to do.
 */
export const dynamic = "force-dynamic"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const back = NextResponse.redirect(new URL(`/r/${encodeURIComponent(id)}`, request.url), 303)
  back.headers.set("Cache-Control", "no-store")
  try {
    const response = await fetch(`${API_BASE}/v1/r/${encodeURIComponent(id)}/pdf/status`, { cache: "no-store" })
    const data = await response.json()
    if (response.ok && data?.status === "ready" && typeof data.pdf_url === "string" && data.pdf_url) {
      const to = NextResponse.redirect(data.pdf_url, 302)
      to.headers.set("Cache-Control", "no-store")
      return to
    }
  } catch (error) {
    console.error("PDF open proxy error:", error)
  }
  return back
}
