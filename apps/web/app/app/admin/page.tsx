import { apiFetch } from "@/lib/api"
import { AdminOverview } from "@repo/ui"

async function getAdminData() {
  try {
    const [kpisRes, reportsChartRes, emailsChartRes, reportsRes, schedulesRes, emailLogsRes] = await Promise.all([
      apiFetch("/v1/admin/metrics"),
      apiFetch("/v1/admin/metrics/timeseries"),
      apiFetch("/v1/admin/metrics/timeseries?type=emails"),
      apiFetch("/v1/admin/reports?limit=10"),
      apiFetch("/v1/admin/schedules?limit=10"),
      apiFetch("/v1/admin/emails?limit=10"),
    ])

    const kpis = kpisRes || { activeSchedules: 0, reportsPerDay: 0, emailsPerDay: 0, avgRenderMs: 0 }
    const reportsChartData = reportsChartRes || []
    const emailsChartData = emailsChartRes || []
    const reports = reportsRes || []
    const schedules = schedulesRes || []
    const emailLogs = emailLogsRes || []

    return { kpis, reportsChartData, emailsChartData, reports, schedules, emailLogs }
  } catch (error) {
    console.error("Failed to fetch admin data:", error)
    return {
      kpis: { activeSchedules: 0, reportsPerDay: 0, emailsPerDay: 0, avgRenderMs: 0 },
      reportsChartData: [],
      emailsChartData: [],
      reports: [],
      schedules: [],
      emailLogs: [],
    }
  }
}

export default async function AdminPage() {
  const { kpis, reportsChartData, emailsChartData, reports, schedules, emailLogs } = await getAdminData()

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-display font-bold text-foreground">Admin Console</h1>
        <p className="text-muted-foreground mt-2">Monitor system performance and manage all organizations</p>
      </div>

      <AdminOverview 
        kpis={kpis}
        reportsChartData={reportsChartData}
        emailsChartData={emailsChartData}
      />
    </div>
  )
}
