'use client'

import { useEffect, useState } from "react"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Building2,
  Building,
  Users,
  ChevronRight,
  FileText,
  Calendar,
  Mail,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  XCircle,
  Activity,
} from "lucide-react"

interface Report {
  id: string
  account_name: string
  report_type: string
  status: string
  duration_ms: number | null
  error: string | null
  created_at: string
}

interface Schedule {
  id: string
  account_name: string
  name: string
  cadence: string
  active: boolean
  next_run_at: string | null
  last_run_at: string | null
}

interface EmailLog {
  id: string
  account_name: string
  subject: string
  to_count: number
  status: string
  created_at: string
}

interface AdminData {
  metrics: Record<string, any>
  reports: Report[]
  schedules: Schedule[]
  emailLogs: EmailLog[]
}

function formatTimeAgo(dateString: string | null): string {
  if (!dateString) return "Never"
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

const statusColors: Record<string, string> = {
  completed: "bg-green-100 text-green-800",
  processing: "bg-blue-100 text-blue-800",
  pending: "bg-yellow-100 text-yellow-800",
  failed: "bg-red-100 text-red-800",
  success: "bg-green-100 text-green-800",
}

export default function AdminPage() {
  const [data, setData] = useState<AdminData>({
    metrics: {},
    reports: [],
    schedules: [],
    emailLogs: [],
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchAdminData() {
      try {
        const [metricsRes, reportsRes, schedulesRes, emailsRes] = await Promise.all([
          fetch('/api/proxy/v1/admin/metrics/overview', { credentials: 'include' }),
          fetch('/api/proxy/v1/admin/reports?limit=10', { credentials: 'include' }),
          fetch('/api/proxy/v1/admin/schedules?limit=10', { credentials: 'include' }),
          fetch('/api/proxy/v1/admin/emails?limit=10', { credentials: 'include' }),
        ])

        const metrics = metricsRes.ok ? await metricsRes.json() : {}
        const reportsData = reportsRes.ok ? await reportsRes.json() : {}
        const schedulesData = schedulesRes.ok ? await schedulesRes.json() : {}
        const emailsData = emailsRes.ok ? await emailsRes.json() : {}

        setData({
          metrics,
          reports: reportsData?.reports || [],
          schedules: schedulesData?.schedules || [],
          emailLogs: emailsData?.emails || [],
        })
      } catch (err) {
        console.error('Failed to fetch admin data:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchAdminData()
  }, [])

  if (loading) {
    return <AdminSkeleton />
  }

  const { metrics, reports, schedules, emailLogs } = data

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-display font-bold text-foreground">Admin Console</h1>
        <p className="text-muted-foreground mt-2">System overview and management</p>
      </div>

      {/* Key Metrics - Row 1 */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Accounts</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.total_accounts || 0}</div>
            <p className="text-xs text-muted-foreground">
              {metrics.total_affiliates || 0} affiliates
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.total_users || 0}</div>
            <p className="text-xs text-muted-foreground">
              {metrics.active_users_30d || 0} active (30d)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports (7d)</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.reports_7d || 0}</div>
            <p className="text-xs text-muted-foreground">
              {metrics.reports_24h || 0} today
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${(metrics.error_rate_7d || 0) > 5 ? 'text-red-500' : 'text-green-500'}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${(metrics.error_rate_7d || 0) > 5 ? 'text-red-600' : 'text-green-600'}`}>
              {metrics.error_rate_7d || 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              {metrics.reports_failed_7d || 0} failed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Render</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">
              {((metrics.avg_processing_ms_7d || 0) / 1000).toFixed(1)}s
            </div>
            <p className="text-xs text-muted-foreground">
              {metrics.avg_processing_ms_7d || 0}ms
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Schedules</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.schedules_active || 0}</div>
            <p className="text-xs text-muted-foreground">
              of {metrics.schedules_total || 0} total
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Report Status Breakdown */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-800">Completed</p>
                <p className="text-2xl font-bold text-green-900">{metrics.reports_completed_7d || 0}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-800">Processing</p>
                <p className="text-2xl font-bold text-blue-900">{metrics.reports_processing || 0}</p>
              </div>
              <Activity className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-800">Pending</p>
                <p className="text-2xl font-bold text-yellow-900">{metrics.reports_pending || 0}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-red-50 border-red-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-800">Failed</p>
                <p className="text-2xl font-bold text-red-900">{metrics.reports_failed_7d || 0}</p>
              </div>
              <XCircle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Management Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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

      {/* Recent Reports */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Recent Reports
              </CardTitle>
              <CardDescription>Last 10 report generations</CardDescription>
            </div>
            <Link href="/app/admin/reports" className="text-sm text-primary hover:underline">
              View all
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          {reports.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No reports found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Account</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.map((report) => (
                  <TableRow key={report.id}>
                    <TableCell className="font-medium">{report.account_name}</TableCell>
                    <TableCell>{report.report_type}</TableCell>
                    <TableCell>
                      <Badge className={statusColors[report.status] || "bg-gray-100"}>
                        {report.status}
                      </Badge>
                      {report.error && (
                        <span className="ml-2 text-xs text-red-600" title={report.error}>
                          (error)
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {report.duration_ms ? `${(report.duration_ms / 1000).toFixed(1)}s` : '-'}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatTimeAgo(report.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Recent Schedules & Emails */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Schedules */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Active Schedules
                </CardTitle>
                <CardDescription>Automated report schedules</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {schedules.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">No schedules found</p>
            ) : (
              <div className="space-y-3">
                {schedules.slice(0, 5).map((schedule) => (
                  <div key={schedule.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <div>
                      <p className="font-medium">{schedule.name}</p>
                      <p className="text-sm text-muted-foreground">{schedule.account_name}</p>
                    </div>
                    <div className="text-right">
                      <Badge variant={schedule.active ? "default" : "secondary"}>
                        {schedule.active ? "Active" : "Paused"}
                      </Badge>
                      <p className="text-xs text-muted-foreground mt-1">
                        {schedule.cadence}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Emails */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  Recent Emails
                </CardTitle>
                <CardDescription>Email delivery log</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {emailLogs.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">No emails found</p>
            ) : (
              <div className="space-y-3">
                {emailLogs.slice(0, 5).map((email) => (
                  <div key={email.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium truncate">{email.subject}</p>
                      <p className="text-sm text-muted-foreground">{email.account_name}</p>
                    </div>
                    <div className="text-right ml-4">
                      <Badge className={statusColors[email.status] || "bg-gray-100"}>
                        {email.status}
                      </Badge>
                      <p className="text-xs text-muted-foreground mt-1">
                        {email.to_count} recipient{email.to_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function AdminSkeleton() {
  return (
    <div className="space-y-8">
      <div>
        <Skeleton className="h-9 w-48 mb-2" />
        <Skeleton className="h-5 w-64" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-20" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 mb-1" />
              <Skeleton className="h-3 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <Skeleton className="h-4 w-20 mb-2" />
              <Skeleton className="h-8 w-12" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32 mb-1" />
          <Skeleton className="h-4 w-48" />
        </CardHeader>
        <CardContent>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="py-3 flex gap-4">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-4 w-12 font-mono" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
