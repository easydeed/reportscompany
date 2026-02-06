import AppLayoutClient from "../app-layout"
import { cookies } from 'next/headers'

// Force dynamic rendering for all /app routes (uses cookies for auth)
export const dynamic = 'force-dynamic'

/**
 * Decode a JWT payload without any external library.
 * Returns null if the token is invalid.
 */
function decodeJwtPayload(token: string): Record<string, any> | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const json = atob(base64)
    return JSON.parse(json)
  } catch {
    return null
  }
}

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  let isAdmin = false
  let isAffiliate = false
  let accountType = ""
  
  try {
    const cookieStore = await cookies()
    const token = cookieStore.get('mr_token')?.value
    
    if (token) {
      const decoded = decodeJwtPayload(token)
      if (decoded) {
        // Check expiry
        if (typeof decoded.exp !== 'number' || decoded.exp * 1000 >= Date.now()) {
          isAdmin = decoded.role === "ADMIN"
          isAffiliate = decoded.account_type === "INDUSTRY_AFFILIATE"
          accountType = decoded.account_type || "REGULAR"
        }
      }
    }
  } catch (error) {
    console.error("Failed to access cookies in layout:", error)
  }

  return <AppLayoutClient isAdmin={isAdmin} isAffiliate={isAffiliate} accountType={accountType}>{children}</AppLayoutClient>
}
