import { NextResponse, NextRequest } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl
  const token = req.cookies.get("mr_token")?.value

  // Protect all /app/*
  if (pathname.startsWith("/app")) {
    if (!token) {
      const url = req.nextUrl.clone()
      url.pathname = "/login"
      url.searchParams.set("next", pathname)
      return NextResponse.redirect(url)
    }

    // Extra check for admin paths
    if (pathname.startsWith("/app/admin")) {
      try {
        const res = await fetch(`${API_BASE}/v1/me`, {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store",
        })
        if (!res.ok) throw new Error("me failed")
        const me = await res.json()
        if ((me?.role || "USER") !== "ADMIN") {
          const url = req.nextUrl.clone()
          url.pathname = "/app" // Redirect non-admins to dashboard
          return NextResponse.redirect(url)
        }
      } catch {
        const url = req.nextUrl.clone()
        url.pathname = "/login"
        url.searchParams.set("next", pathname)
        return NextResponse.redirect(url)
      }
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/app/:path*"],
}

