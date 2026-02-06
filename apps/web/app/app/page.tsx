import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { DashboardContent } from "@/components/dashboard/dashboard-content"

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

/**
 * Dashboard Page — Thin Server Component Shell
 * 
 * Auth is handled by middleware (checks cookie + expiry).
 * This page only does the affiliate redirect check (instant, from JWT).
 * DashboardContent is a client component that shows skeletons immediately
 * and fetches API data client-side.
 */
export default async function DashboardPage() {
  const cookieStore = await cookies()
  const token = cookieStore.get('mr_token')?.value

  // Affiliate redirect — decode JWT without try-catch wrapping redirect()
  // (Next.js redirect() works by throwing, so it must NOT be inside a catch)
  if (token) {
    const decoded = decodeJwtPayload(token)
    if (decoded?.account_type === 'INDUSTRY_AFFILIATE') {
      redirect('/app/affiliate')
    }
  }

  return <DashboardContent />
}
