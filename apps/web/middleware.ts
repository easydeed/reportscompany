import { NextResponse, NextRequest } from "next/server"

const CLOAK = process.env.ADMIN_CLOAK_404 === "1"

/**
 * Decode a JWT payload without any external library.
 * Uses only atob() which is available in Edge Runtime.
 * Does NOT verify the signature — just reads the payload.
 */
function decodeJwtPayload(token: string): Record<string, any> | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    // Convert base64url → base64
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const json = atob(base64)
    return JSON.parse(json)
  } catch {
    return null
  }
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl
  const token = req.cookies.get("mr_token")?.value

  // Protect all /app/*
  if (pathname.startsWith("/app")) {
    if (!token) {
      console.log(`[MW] No mr_token cookie for ${pathname} → /login`)
      return NextResponse.redirect(new URL('/login', req.url))
    }

    // Decode JWT locally — no external library, no API call
    const decoded = decodeJwtPayload(token)

    if (!decoded) {
      console.error(`[MW] Failed to decode JWT for ${pathname} — clearing cookie`)
      const response = NextResponse.redirect(new URL('/login', req.url))
      response.cookies.delete('mr_token')
      return response
    }

    // Check expiry
    if (typeof decoded.exp === 'number' && decoded.exp * 1000 < Date.now()) {
      console.log(`[MW] Token expired for ${pathname} → /login`)
      const response = NextResponse.redirect(new URL('/login', req.url))
      response.cookies.delete('mr_token')
      return response
    }

    // Admin route protection
    if (pathname.startsWith("/app/admin")) {
      const role = (decoded.role || "USER").toUpperCase()
      if (role !== "ADMIN") {
        if (CLOAK) {
          const url = req.nextUrl.clone()
          url.pathname = "/404"
          return NextResponse.rewrite(url)
        } else {
          const url = req.nextUrl.clone()
          url.pathname = "/app"
          return NextResponse.redirect(url)
        }
      }
    }

    return NextResponse.next()
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/app/:path*"],
}
