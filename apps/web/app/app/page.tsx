import { apiFetch } from "@/lib/api"
import { DashboardOverview } from "@repo/ui"

export default async function Overview() {
  let data: any = null
  try {
    data = await apiFetch("/v1/usage")
  } catch (error) {
    console.error("Failed to fetch usage data:", error)
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
      <DashboardOverview 
        kpis={kpis}
        reports30d={reports30d}
        emails30d={emails30d}
        recent={recent}
      />
    </div>
  )
}
