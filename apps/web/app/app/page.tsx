import { apiFetch } from "@/lib/api"
import { DashboardOverview } from "@repo/ui"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, AlertTriangle } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export const dynamic = 'force-dynamic'

export default async function Overview() {
  let data: any = null
  try {
    data = await apiFetch("/v1/usage")
  } catch (error) {
    console.error("Failed to fetch usage data:", error)
  }

  // Phase 29E: Fetch plan usage for warning banner
  let planUsage: any = null
  try {
    planUsage = await apiFetch("/v1/account/plan-usage")
  } catch (error) {
    console.error("Failed to fetch plan usage:", error)
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
    <div>
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      
      {/* Phase 29E: Usage Warning Banner */}
      {planUsage && planUsage.decision === 'ALLOW_WITH_WARNING' && (
        <Alert className="mb-6 border-yellow-500/20 bg-yellow-500/10">
          <AlertTriangle className="h-4 w-4 text-yellow-500" />
          <AlertTitle>Approaching Limit</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>
              You're approaching your monthly report limit for the <strong>{planUsage.plan.plan_name}</strong> plan. {planUsage.info.message}
            </span>
            <Button asChild variant="outline" size="sm" className="ml-4">
              <Link href="/app/account/plan">View Plan</Link>
            </Button>
          </AlertDescription>
        </Alert>
      )}
      
      {planUsage && planUsage.decision === 'BLOCK' && (
        <Alert className="mb-6 border-red-500/20 bg-red-500/10">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <AlertTitle>Monthly Limit Reached</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>
              You've reached your monthly report limit for your current plan. New reports may be blocked until the period resets.
            </span>
            <Button asChild variant="outline" size="sm" className="ml-4">
              <Link href="/app/account/plan">View Plan</Link>
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
