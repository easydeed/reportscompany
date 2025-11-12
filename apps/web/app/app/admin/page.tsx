import {
  AdminOverview,
  RecentReportsTable,
  SchedulesTableClient,
  EmailLogTable,
  type AdminKPIData,
  type RecentReport,
  type AdminSchedule,
  type EmailLog,
  type ChartDataPoint,
} from "@/components/admin"
import { apiFetch } from "@/lib/api"

async function getAdminData() {
  try {
    // Fetch all admin data in parallel
    const [metricsRes, timeseriesRes, schedulesRes, reportsRes, emailsRes] = await Promise.all([
      apiFetch("/v1/admin/metrics"),
      apiFetch("/v1/admin/metrics/timeseries?days=30"),
      apiFetch("/v1/admin/schedules?limit=20"),
      apiFetch("/v1/admin/reports?limit=20"),
      apiFetch("/v1/admin/emails?limit=20"),
    ])

    return {
      metrics: metricsRes,
      timeseries: timeseriesRes,
      schedules: schedulesRes.schedules || [],
      reports: reportsRes.reports || [],
      emails: emailsRes.emails || [],
    }
  } catch (error) {
    console.error("Failed to fetch admin data:", error)
    // Return empty data on error
    return {
      metrics: {
        reports_24h: 0,
        reports_7d: 0,
        avg_processing_ms_7d: 0,
        schedules_active: 0,
        emails_24h: 0,
        queue_depth: 0,
      },
      timeseries: { reports_by_day: [], emails_by_day: [] },
      schedules: [],
      reports: [],
      emails: [],
    }
  }
}

function formatCadence(schedule: any): string {
  if (schedule.cadence === "weekly") {
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    const day = days[schedule.weekly_dow] || "?"
    return `Weekly - ${day} ${schedule.send_hour}:${String(schedule.send_minute).padStart(2, "0")}`
  } else if (schedule.cadence === "monthly") {
    return `Monthly - ${schedule.monthly_dom}${getOrdinalSuffix(schedule.monthly_dom)} at ${schedule.send_hour}:${String(schedule.send_minute).padStart(2, "0")}`
  }
  return schedule.cadence
}

function getOrdinalSuffix(day: number): string {
  if (day >= 11 && day <= 13) return "th"
  switch (day % 10) {
    case 1:
      return "st"
    case 2:
      return "nd"
    case 3:
      return "rd"
    default:
      return "th"
  }
}

export default async function AdminPage() {
  const data = await getAdminData()

  // Transform API data to component format
  const kpis: AdminKPIData = {
    activeSchedules: data.metrics.schedules_active,
    reportsPerDay: Math.round(data.metrics.reports_24h), // Could average over 7d if needed
    emailsPerDay: Math.round(data.metrics.emails_24h),
    avgRenderMs: data.metrics.avg_processing_ms_7d,
  }

  // Transform timeseries data for charts
  const reportsChartData: ChartDataPoint[] = data.timeseries.reports_by_day.map((item: any) => ({
    date: new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    reports: item.count,
  }))

  const emailsChartData: ChartDataPoint[] = data.timeseries.emails_by_day.map((item: any) => ({
    date: new Date(item.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    emails: item.count,
  }))

  // Transform schedules
  const schedules: AdminSchedule[] = data.schedules.map((s: any) => ({
    id: s.id,
    org: s.account_name,
    name: s.name,
    cadence: formatCadence(s),
    nextRun: s.next_run_at ? new Date(s.next_run_at) : new Date(),
    active: s.active,
  }))

  // Transform reports
  const reports: RecentReport[] = data.reports.map((r: any) => ({
    id: r.id,
    type: r.report_type.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase()),
    org: r.account_name,
    status: r.status === "completed" ? "completed" : r.status === "failed" ? "failed" : "processing",
    duration: r.duration_ms || 0,
    finished: r.finished_at ? new Date(r.finished_at) : new Date(),
  }))

  // Transform email logs
  const emailLogs: EmailLog[] = data.emails.map((e: any) => ({
    id: e.id,
    date: new Date(e.created_at),
    to: e.to_count,
    subject: e.subject || "No subject",
    code: e.response_code || 0,
  }))

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-display font-bold text-foreground">Admin Console</h1>
        <p className="text-muted-foreground mt-2">Monitor system performance and manage all organizations</p>
      </div>

      <AdminOverview kpis={kpis} reportsChartData={reportsChartData} emailsChartData={emailsChartData} />

      <div className="space-y-6">
        <RecentReportsTable reports={reports} />
        <SchedulesTableClient schedules={schedules} />
        <EmailLogTable logs={emailLogs} />
      </div>
    </div>
  )
}

