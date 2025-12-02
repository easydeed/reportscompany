import { apiFetch } from "@/lib/api"
import { AdminOverview } from "@repo/ui"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Building2, Building, Users, ChevronRight } from "lucide-react"

export const dynamic = 'force-dynamic'

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

      {/* Management Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Link href="/app/admin/affiliates" className="group">
          <Card className="h-full transition-colors hover:border-primary/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-base font-medium">Title Companies</CardTitle>
              <Building2 className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </CardHeader>
            <CardContent>
              <CardDescription className="flex items-center justify-between">
                Manage affiliates and their agents
                <ChevronRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
              </CardDescription>
            </CardContent>
          </Card>
        </Link>

        <Link href="/app/admin/accounts" className="group">
          <Card className="h-full transition-colors hover:border-primary/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-base font-medium">All Accounts</CardTitle>
              <Building className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </CardHeader>
            <CardContent>
              <CardDescription className="flex items-center justify-between">
                View and manage all accounts
                <ChevronRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
              </CardDescription>
            </CardContent>
          </Card>
        </Link>

        <Link href="/app/admin/users" className="group">
          <Card className="h-full transition-colors hover:border-primary/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-base font-medium">All Users</CardTitle>
              <Users className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </CardHeader>
            <CardContent>
              <CardDescription className="flex items-center justify-between">
                View and manage all users
                <ChevronRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
              </CardDescription>
            </CardContent>
          </Card>
        </Link>
      </div>

      <AdminOverview
        kpis={kpis}
        reportsChartData={reportsChartData}
        emailsChartData={emailsChartData}
      />
    </div>
  )
}
