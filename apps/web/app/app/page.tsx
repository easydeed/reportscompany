import { DashboardOverview } from "@repo/ui"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, AlertTriangle } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { DashboardOnboarding } from "@/components/onboarding"

export const dynamic = 'force-dynamic'

async function fetchWithAuth(path: string, token: string) {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com'
  
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Cookie': `mr_token=${token}` },
      cache: 'no-store',
    })
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}

export default async function Overview() {
  const cookieStore = await cookies()
  const token = cookieStore.get('mr_token')?.value
  
  if (!token) {
    redirect('/login')
  }

  // Fetch ALL data in parallel - much faster than sequential
  const [me, data, planUsage] = await Promise.all([
    fetchWithAuth("/v1/me", token),
    fetchWithAuth("/v1/usage", token),
    fetchWithAuth("/v1/account/plan-usage", token),
  ])
  
  // Check if affiliate and redirect
  if (me?.account_type === "INDUSTRY_AFFILIATE") {
    redirect("/app/affiliate")
  }

  // Shape props for the component
  const kpis = {
    reports: data?.summary?.total_reports ?? 0,
    billable: data?.summary?.billable_reports ?? 0,
    schedules: data?.limits?.active_schedules ?? 0,
    avgRenderMs: data?.summary?.avg_ms ?? 0,
  }

  const reports30d = (data?.timeline ?? []).map((item: any) => ({
    date: item.date,
    value: item.count || 0,
  }))

  const emails30d: any[] = [] // TODO: wire when email events land

  const recent: any[] = [] // TODO: wire recent runs/emails

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
        <p className="text-[var(--app-muted)] mt-1">
          Your account activity and key metrics
        </p>
      </div>

      {/* Onboarding Checklist & Wizard */}
      <DashboardOnboarding />

      {/* Phase 29E: Usage Warning Banner */}
      {planUsage && planUsage.decision === 'ALLOW_WITH_WARNING' && (
        <Alert className="border-yellow-500/30 bg-yellow-500/10">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertTitle className="text-yellow-800">Approaching Limit</AlertTitle>
          <AlertDescription className="flex items-center justify-between text-yellow-700">
            <span>
              You're approaching your monthly report limit for the <strong>{planUsage.plan.plan_name}</strong> plan. {planUsage.info.message}
            </span>
            <Button asChild variant="outline" size="sm" className="ml-4 border-yellow-600 text-yellow-700 hover:bg-yellow-50">
              <Link href="/account/plan">View Plan</Link>
            </Button>
          </AlertDescription>
        </Alert>
      )}
      
      {planUsage && planUsage.decision === 'BLOCK' && (
        <Alert className="border-red-500/30 bg-red-500/10">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-800">Monthly Limit Reached</AlertTitle>
          <AlertDescription className="flex items-center justify-between text-red-700">
            <span>
              You've reached your monthly report limit for your current plan. New reports may be blocked until the period resets.
            </span>
            <Button asChild variant="outline" size="sm" className="ml-4 border-red-600 text-red-700 hover:bg-red-50">
              <Link href="/account/plan">View Plan</Link>
            </Button>
          </AlertDescription>
        </Alert>
      )}
      
      <DashboardOverview 
        kpis={kpis}
        reports30d={reports30d}
        emails30d={emails30d}
        recent={recent}
      />
    </div>
  )
}
