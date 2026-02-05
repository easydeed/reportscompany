import { NextResponse, NextRequest } from "next/server"
import { getApiBase } from "@/lib/get-api-base"

const CLOAK = process.env.ADMIN_CLOAK_404 === "1"
/** Max time to wait for admin check - fail fast to avoid blocking all admin pages */
const MIDDLEWARE_API_TIMEOUT_MS = 5000

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
      // Create abort controller for timeout protection
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), MIDDLEWARE_API_TIMEOUT_MS)
      
      try {
        const API_BASE = getApiBase()
        const res = await fetch(`${API_BASE}/v1/me`, {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store",
          signal: controller.signal, // Enable timeout abort
        })
        clearTimeout(timeoutId)
        
        if (!res.ok) throw new Error("identity failed")
        const me = await res.json()
        if ((me?.role || "USER") !== "ADMIN") {
          if (CLOAK) {
            // Cloak as 404 for non-admins
            const url = req.nextUrl.clone()
            url.pathname = "/404"
            return NextResponse.rewrite(url)
          } else {
            // Redirect to dashboard
            const url = req.nextUrl.clone()
            url.pathname = "/app"
            return NextResponse.redirect(url)
          }
        }
      } catch (error) {
        clearTimeout(timeoutId)
        // If timeout or network error, redirect to login for safety
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

