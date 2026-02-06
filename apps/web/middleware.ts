import { NextResponse, NextRequest } from "next/server"
import { jwtDecode } from "jwt-decode"

const CLOAK = process.env.ADMIN_CLOAK_404 === "1"

interface JWTPayload {
  sub: string
  user_id: string
  account_id: string
  role?: string
  account_type?: string
  exp: number
}

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

    // Decode JWT locally - NO external API call!
    try {
      const decoded = jwtDecode<JWTPayload>(token)
      
      // Check expiry
      if (decoded.exp * 1000 < Date.now()) {
        const response = NextResponse.redirect(new URL('/login', req.url))
        response.cookies.delete('mr_token')
        return response
      }

      // Admin route protection - check role from JWT payload directly
      if (pathname.startsWith("/app/admin")) {
        const role = decoded.role || "USER"
        if (role !== "ADMIN") {
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
      }

      return NextResponse.next()
    } catch {
      // Invalid token → login
      const response = NextResponse.redirect(new URL('/login', req.url))
      response.cookies.delete('mr_token')
      return response
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/app/:path*"],
}
