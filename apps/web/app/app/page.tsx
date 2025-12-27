import { DashboardOverview } from "@repo/ui"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, AlertTriangle } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { redirect } from 'next/navigation'
import { DashboardOnboarding } from "@/components/onboarding"
import { createServerApi } from "@/lib/api-server"

export const dynamic = 'force-dynamic'

export default async function Overview() {
  const api = await createServerApi()
  
  if (!api.isAuthenticated()) {
    redirect('/login')
  }

  // Fetch ALL data in parallel using the shared API utility
  const [meRes, dataRes, planUsageRes] = await Promise.all([
    api.get<any>("/v1/me"),
    api.get<any>("/v1/usage"),
    api.get<any>("/v1/account/plan-usage"),
  ])

  const me = meRes.data
  const data = dataRes.data
  const planUsage = planUsageRes.data
  
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
    value: item.reports || item.count || 0,
  }))

  // Wire up email timeline from recent emails
  const emails30d = (data?.recent_emails ?? []).reduce((acc: any[], email: any) => {
    if (email.created_at) {
      const date = email.created_at.split('T')[0]
      const existing = acc.find((e: any) => e.date === date)
      if (existing) {
        existing.value += 1
      } else {
        acc.push({ date, value: 1 })
      }
    }
    return acc
  }, []).sort((a: any, b: any) => a.date.localeCompare(b.date))

  // Combine recent reports and emails into a single feed
  const recentReports = (data?.recent_reports ?? []).map((r: any) => ({
    id: r.id,
    type: 'report' as const,
    title: `${r.type?.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())} - ${r.city}`,
    status: r.status,
    timestamp: r.created_at,
    url: r.pdf_url,
  }))
  
  const recentEmails = (data?.recent_emails ?? []).map((e: any) => ({
    id: e.id,
    type: 'email' as const,
    title: e.subject || 'Email sent',
    status: e.status,
    timestamp: e.created_at,
    recipients: e.to,
  }))
  
  // Merge and sort by timestamp
  const recent = [...recentReports, ...recentEmails]
    .sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''))
    .slice(0, 10)

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
