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
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Welcome to TrendyReports Admin Console</p>
      </div>

      {/* API Connection Warning */}
      {apiIssue && (
        <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-4">
          <p className="text-yellow-400 font-medium">⚠️ Unable to load admin data</p>
          <p className="text-yellow-300/70 text-sm mt-1">
            API calls to the backend failed. Check the Vercel logs for details.
          </p>
        </div>
      )}

      {/* Primary KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Total Accounts</CardTitle>
            <Building className="h-4 w-4 text-violet-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-white">{m.total_accounts || 0}</div>
            <p className="text-xs text-gray-500 mt-1">
              <span className="text-violet-400">{m.total_affiliates || 0}</span> affiliates
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Total Users</CardTitle>
            <Users className="h-4 w-4 text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-white">{m.total_users || 0}</div>
            <p className="text-xs text-gray-500 mt-1">
              <span className="text-green-400">{m.active_users_30d || 0}</span> active (30d)
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Reports (7d)</CardTitle>
            <FileText className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-white">{m.reports_7d || 0}</div>
            <p className="text-xs text-gray-500 mt-1">
              <span className="text-green-400">{m.reports_24h || 0}</span> today
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Error Rate</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${errorRate > 5 ? 'text-red-400' : 'text-green-400'}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold ${errorRate > 5 ? 'text-red-400' : 'text-green-400'}`}>
              {errorRate}%
            </div>
            <p className="text-xs text-gray-500 mt-1">
              <span className="text-red-400">{m.reports_failed_7d || 0}</span> failed
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Secondary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Completed</p>
                <p className="text-xl font-bold text-green-400">{m.reports_completed_7d || 0}</p>
              </div>
              <CheckCircle className="h-6 w-6 text-green-400/30" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Processing</p>
                <p className="text-xl font-bold text-blue-400">{m.reports_processing || 0}</p>
              </div>
              <Activity className="h-6 w-6 text-blue-400/30" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Pending</p>
                <p className="text-xl font-bold text-yellow-400">{m.reports_pending || 0}</p>
              </div>
              <Clock className="h-6 w-6 text-yellow-400/30" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Avg Render</p>
                <p className="text-xl font-bold text-violet-400">{avgRenderSec}s</p>
              </div>
              <TrendingUp className="h-6 w-6 text-violet-400/30" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Reports */}
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-white">Recent Reports</CardTitle>
              <Link href="/admin/reports" className="text-sm text-violet-400 hover:text-violet-300">
                View all →
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {recentReports.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No reports yet</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-gray-800 hover:bg-transparent">
                    <TableHead className="text-gray-400">Account</TableHead>
                    <TableHead className="text-gray-400">Type</TableHead>
                    <TableHead className="text-gray-400">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentReports.map((report: any) => (
                    <TableRow key={report.id} className="border-gray-800">
                      <TableCell className="text-gray-300">{report.account_name}</TableCell>
                      <TableCell className="text-gray-400">{report.report_type}</TableCell>
                      <TableCell>
                        <Badge className={
                          report.status === 'completed' ? 'bg-green-500/20 text-green-400 border-green-500/30' :
                          report.status === 'failed' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                          report.status === 'processing' ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' :
                          'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
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
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-white">Recent Accounts</CardTitle>
              <Link href="/admin/accounts" className="text-sm text-violet-400 hover:text-violet-300">
                View all →
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {recentAccounts.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No accounts yet</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-gray-800 hover:bg-transparent">
                    <TableHead className="text-gray-400">Name</TableHead>
                    <TableHead className="text-gray-400">Plan</TableHead>
                    <TableHead className="text-gray-400">Reports</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentAccounts.map((account: any) => (
                    <TableRow key={account.account_id} className="border-gray-800">
                      <TableCell>
                        <div>
                          <p className="text-gray-300 font-medium">{account.name}</p>
                          <p className="text-xs text-gray-500">{account.slug}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="border-gray-700 text-gray-400">
                          {account.plan_slug}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-gray-400">{account.reports_this_month}</TableCell>
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
        <Card className="bg-gradient-to-br from-violet-600/20 to-purple-600/20 border-violet-500/30">
          <CardContent className="pt-6">
            <p className="text-sm text-violet-300">Active Schedules</p>
            <p className="text-2xl font-bold text-white mt-1">{m.schedules_active || 0}</p>
            <p className="text-xs text-violet-400 mt-1">of {m.schedules_total || 0} total</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-600/20 to-cyan-600/20 border-blue-500/30">
          <CardContent className="pt-6">
            <p className="text-sm text-blue-300">Emails (24h)</p>
            <p className="text-2xl font-bold text-white mt-1">{m.emails_24h || 0}</p>
            <p className="text-xs text-blue-400 mt-1">sent today</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-600/20 to-emerald-600/20 border-green-500/30">
          <CardContent className="pt-6">
            <p className="text-sm text-green-300">Queue Depth</p>
            <p className="text-2xl font-bold text-white mt-1">{m.queue_depth || 0}</p>
            <p className="text-xs text-green-400 mt-1">pending jobs</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-600/20 to-amber-600/20 border-orange-500/30">
          <CardContent className="pt-6">
            <p className="text-sm text-orange-300">Avg Processing</p>
            <p className="text-2xl font-bold text-white mt-1">{m.avg_processing_ms_7d || 0}ms</p>
            <p className="text-xs text-orange-400 mt-1">last 7 days</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
