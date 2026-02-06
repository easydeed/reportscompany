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
      console.log(`[MW] No mr_token cookie found for ${pathname} → redirecting to /login`)
      return NextResponse.redirect(new URL('/login', req.url))
    }

    // Decode JWT locally — no external API call
    try {
      const decoded = jwtDecode<JWTPayload>(token)
      
      // Check expiry
      if (decoded.exp * 1000 < Date.now()) {
        console.log(`[MW] Token expired (exp=${decoded.exp}, now=${Math.floor(Date.now()/1000)}) for ${pathname} → /login`)
        const response = NextResponse.redirect(new URL('/login', req.url))
        response.cookies.delete('mr_token')
        return response
      }

      // Admin route protection
      if (pathname.startsWith("/app/admin")) {
        const role = decoded.role || "USER"
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
    } catch (err) {
      // Log the actual error — this is critical for debugging
      console.error(`[MW] JWT decode FAILED for ${pathname}:`, err)
      console.error(`[MW] Token starts with: ${token.substring(0, 20)}...`)
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
