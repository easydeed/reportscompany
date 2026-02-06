import { cookies } from 'next/headers'
import { jwtDecode } from "jwt-decode"
import { redirect } from 'next/navigation'
import { DashboardContent } from "@/components/dashboard/dashboard-content"

export const dynamic = 'force-dynamic'

interface JWTPayload {
  account_type?: string
}

/**
 * Dashboard Page — Thin Server Component Shell
 * 
 * This page renders instantly because:
 * 1. JWT check is local (no API call) - just decodes the cookie
 * 2. DashboardContent is a client component that shows skeletons immediately
 * 3. API data fetches happen client-side AFTER the page shell renders
 * 
 * Previous version blocked on 3 API calls server-side, causing 8-10 second TTFB.
 * Now the shell renders in <100ms and data fills in progressively.
 */
export default async function DashboardPage() {
  // Check affiliate redirect from JWT (instant, no API call)
  const cookieStore = await cookies()
  const token = cookieStore.get('mr_token')?.value
  
  if (!token) {
    redirect('/login')
  }

  try {
    const decoded = jwtDecode<JWTPayload>(token)
    if (decoded.account_type === 'INDUSTRY_AFFILIATE') {
      redirect('/app/affiliate')
    }
  } catch {
    // Invalid token — middleware should have caught this, but redirect to login just in case
    redirect('/login')
  }

  // Render the client component which handles its own data fetching
  return <DashboardContent />
}
