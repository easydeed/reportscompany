import { redirect } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Building,
  Users,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity,
  TrendingUp,
} from "lucide-react"
import { createServerApi } from "@/lib/api-server"

export const dynamic = 'force-dynamic'

export default async function AdminDashboard() {
  const api = await createServerApi()

  if (!api.isAuthenticated()) {
    redirect('/login?next=/admin')
  }

  // Fetch all admin data in parallel using the shared API utility
  const [metricsRes, reportsRes, accountsRes] = await Promise.all([
    api.get<any>("/v1/admin/metrics"),
    api.get<any>("/v1/admin/reports?limit=5"),
    api.get<any>("/v1/admin/accounts?limit=5"),
  ])

  const metrics = metricsRes.data
  const reports = reportsRes.data
  const accounts = accountsRes.data

  const m = metrics || {}
  const recentReports = reports?.reports || []
  const recentAccounts = accounts?.accounts || []

  // Calculate some derived metrics
  const errorRate = m.error_rate_7d || 0
  const avgRenderSec = ((m.avg_processing_ms_7d || 0) / 1000).toFixed(1)

  // Debug: Check if API calls failed
  const apiIssue = !metrics && !reports && !accounts

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Welcome to TrendyReports Admin Console</p>
      </div>

      {/* API Connection Warning */}
      {apiIssue && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <p className="text-amber-800 font-medium">⚠️ Unable to load admin data</p>
          <p className="text-amber-600 text-sm mt-1">
            API calls to the backend failed. Check the Vercel logs for details.
          </p>
        </div>
      )}

      {/* Primary KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Total Accounts</CardTitle>
            <Building className="h-4 w-4 text-indigo-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{m.total_accounts || 0}</div>
            <p className="text-xs text-slate-500 mt-1">
              <span className="text-indigo-600 font-medium">{m.total_affiliates || 0}</span> affiliates
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Total Users</CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{m.total_users || 0}</div>
            <p className="text-xs text-slate-500 mt-1">
              <span className="text-emerald-600 font-medium">{m.active_users_30d || 0}</span> active (30d)
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Reports (7d)</CardTitle>
            <FileText className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{m.reports_7d || 0}</div>
            <p className="text-xs text-slate-500 mt-1">
              <span className="text-emerald-600 font-medium">{m.reports_24h || 0}</span> today
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Error Rate</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${errorRate > 5 ? 'text-red-500' : 'text-emerald-500'}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold ${errorRate > 5 ? 'text-red-600' : 'text-emerald-600'}`}>
              {errorRate}%
            </div>
            <p className="text-xs text-slate-500 mt-1">
              <span className="text-red-600 font-medium">{m.reports_failed_7d || 0}</span> failed
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Secondary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-emerald-50 border-emerald-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-emerald-600">Completed</p>
                <p className="text-xl font-bold text-emerald-700">{m.reports_completed_7d || 0}</p>
              </div>
              <CheckCircle className="h-6 w-6 text-emerald-300" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-blue-600">Processing</p>
                <p className="text-xl font-bold text-blue-700">{m.reports_processing || 0}</p>
              </div>
              <Activity className="h-6 w-6 text-blue-300" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-amber-50 border-amber-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-amber-600">Pending</p>
                <p className="text-xl font-bold text-amber-700">{m.reports_pending || 0}</p>
              </div>
              <Clock className="h-6 w-6 text-amber-300" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-indigo-50 border-indigo-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-indigo-600">Avg Render</p>
                <p className="text-xl font-bold text-indigo-700">{avgRenderSec}s</p>
              </div>
              <TrendingUp className="h-6 w-6 text-violet-300" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Reports */}
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-slate-900">Recent Reports</CardTitle>
              <Link href="/admin/reports" className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
                View all →
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {recentReports.length === 0 ? (
              <p className="text-slate-400 text-center py-8">No reports yet</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-200 hover:bg-transparent">
                    <TableHead className="text-slate-500">Account</TableHead>
                    <TableHead className="text-slate-500">Type</TableHead>
                    <TableHead className="text-slate-500">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentReports.map((report: any) => (
                    <TableRow key={report.id} className="border-slate-100">
                      <TableCell className="text-slate-700">{report.account_name}</TableCell>
                      <TableCell className="text-slate-500">{report.report_type}</TableCell>
                      <TableCell>
                        <Badge className={
                          report.status === 'completed' ? 'bg-emerald-100 text-emerald-700 border-emerald-200' :
                          report.status === 'failed' ? 'bg-red-100 text-red-700 border-red-200' :
                          report.status === 'processing' ? 'bg-blue-100 text-blue-700 border-blue-200' :
                          'bg-amber-100 text-amber-700 border-amber-200'
                        }>
                          {report.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Recent Accounts */}
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-slate-900">Recent Accounts</CardTitle>
              <Link href="/admin/accounts" className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
                View all →
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {recentAccounts.length === 0 ? (
              <p className="text-slate-400 text-center py-8">No accounts yet</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-200 hover:bg-transparent">
                    <TableHead className="text-slate-500">Name</TableHead>
                    <TableHead className="text-slate-500">Plan</TableHead>
                    <TableHead className="text-slate-500">Reports</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentAccounts.map((account: any) => (
                    <TableRow key={account.account_id} className="border-slate-100">
                      <TableCell>
                        <div>
                          <p className="text-slate-700 font-medium">{account.name}</p>
                          <p className="text-xs text-slate-400">{account.slug}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="border-slate-300 text-slate-600">
                          {account.plan_slug}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-slate-600">{account.reports_this_month}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-violet-500 to-purple-600 border-0 shadow-lg">
          <CardContent className="pt-6">
            <p className="text-sm text-violet-100">Active Schedules</p>
            <p className="text-2xl font-bold text-white mt-1">{m.schedules_active || 0}</p>
            <p className="text-xs text-indigo-200 mt-1">of {m.schedules_total || 0} total</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500 to-cyan-600 border-0 shadow-lg">
          <CardContent className="pt-6">
            <p className="text-sm text-blue-100">Emails (24h)</p>
            <p className="text-2xl font-bold text-white mt-1">{m.emails_24h || 0}</p>
            <p className="text-xs text-blue-200 mt-1">sent today</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-500 to-teal-600 border-0 shadow-lg">
          <CardContent className="pt-6">
            <p className="text-sm text-emerald-100">Queue Depth</p>
            <p className="text-2xl font-bold text-white mt-1">{m.queue_depth || 0}</p>
            <p className="text-xs text-emerald-200 mt-1">pending jobs</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-500 to-amber-600 border-0 shadow-lg">
          <CardContent className="pt-6">
            <p className="text-sm text-orange-100">Avg Processing</p>
            <p className="text-2xl font-bold text-white mt-1">{m.avg_processing_ms_7d || 0}ms</p>
            <p className="text-xs text-orange-200 mt-1">last 7 days</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
