import AppLayoutClient from "../app-layout"
import { cookies } from 'next/headers'
import { jwtDecode } from "jwt-decode"

// Force dynamic rendering for all /app routes (uses cookies for auth)
export const dynamic = 'force-dynamic'

interface JWTPayload {
  sub: string
  user_id: string
  account_id: string
  role?: string
  account_type?: string
  exp: number
}

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  let isAdmin = false
  let isAffiliate = false
  let accountType = ""
  
  try {
    // Get cookies from the incoming request
    const cookieStore = await cookies()
    const token = cookieStore.get('mr_token')?.value
    
    if (token) {
      // Decode JWT locally - NO external API call!
      // This saves ~200-500ms (or 5-10s on cold start) per page load
      console.time('[PERF] layout-jwt-decode')
      try {
        const decoded = jwtDecode<JWTPayload>(token)
        
        // Check expiry
        if (decoded.exp * 1000 >= Date.now()) {
          isAdmin = decoded.role === "ADMIN"
          isAffiliate = decoded.account_type === "INDUSTRY_AFFILIATE"
          accountType = decoded.account_type || "REGULAR"
        }
      } catch (e) {
        // Invalid token - use defaults
        console.error("Failed to decode JWT:", e)
      }
      console.timeEnd('[PERF] layout-jwt-decode')
    }
  } catch (error) {
    // Cookie access error - use defaults
    console.error("Failed to access cookies:", error)
  }

  return <AppLayoutClient isAdmin={isAdmin} isAffiliate={isAffiliate} accountType={accountType}>{children}</AppLayoutClient>
}
