import AppLayoutClient from "../app-layout"
import { cookies } from 'next/headers'

// Force dynamic rendering for all /app routes (uses cookies for auth)
export const dynamic = 'force-dynamic'

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
      // Fetch user info with 5-minute cache to avoid re-fetching on every navigation
      const response = await fetch(`${API_BASE}/v1/me`, {
        headers: {
          'Cookie': `mr_token=${token}`,
        },
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
    }
  } catch (error) {
    // User not authenticated or API error
    console.error("Failed to fetch user role:", error)
  }

  return <AppLayoutClient isAdmin={isAdmin} isAffiliate={isAffiliate} accountType={accountType}>{children}</AppLayoutClient>
}

