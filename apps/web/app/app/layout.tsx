import AppLayoutClient from "../app-layout"
import { cookies } from 'next/headers'

// Force dynamic rendering for all /app routes (uses cookies for auth)
export const dynamic = 'force-dynamic'

/** Max time to wait for user info - fail fast to avoid blocking entire app shell */
const LAYOUT_API_TIMEOUT_MS = 5000

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  let isAdmin = false
  let isAffiliate = false
  let accountType = ""
  
  try {
    // Get the API base URL
    const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com'
    
    // Get cookies from the incoming request
    const cookieStore = await cookies()
    const token = cookieStore.get('mr_token')?.value
    
    if (token) {
      // Create abort controller for timeout protection
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), LAYOUT_API_TIMEOUT_MS)
      
      try {
        // Fetch user info with 5-minute cache to avoid re-fetching on every navigation
        const response = await fetch(`${API_BASE}/v1/me`, {
          headers: {
            'Cookie': `mr_token=${token}`,
          },
          signal: controller.signal, // Enable timeout abort
          next: {
            revalidate: 300, // 5 minute cache
            tags: ['user-profile'],
          },
        })
        
        if (response.ok) {
          const me = await response.json()
          isAdmin = me?.role === "ADMIN"
          isAffiliate = me?.account_type === "INDUSTRY_AFFILIATE"
          accountType = me?.account_type || "REGULAR"
        }
      } finally {
        clearTimeout(timeoutId)
      }
    }
  } catch (error) {
    // User not authenticated, API error, or timeout
    // Layout renders with default permissions - page content still loads
    if (error instanceof DOMException && error.name === 'AbortError') {
      console.error("Layout API call timed out - rendering with default permissions")
    } else {
      console.error("Failed to fetch user role:", error)
    }
  }

  return <AppLayoutClient isAdmin={isAdmin} isAffiliate={isAffiliate} accountType={accountType}>{children}</AppLayoutClient>
}

