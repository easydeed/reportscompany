import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Eye,
  Download,
  ExternalLink,
} from "lucide-react"
import { PropertyReportsFilters } from "./filters"
import { PropertyReportActions } from "./actions"

export const dynamic = 'force-dynamic'

interface PropertyReport {
  id: string
  account_id: string
  account_name: string
  user_email: string
  report_type: string
  status: string
  property_address: string
  property_city: string
  property_state: string
  short_code: string
  pdf_url: string | null
  view_count: number
  created_at: string
}

interface Stats {
  total: number
  this_month: number
  failed: number
  processing: number
}

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

export default async function AdminPropertyReportsPage({
  searchParams,
}: {
  searchParams: { status?: string; account?: string; from?: string; to?: string }
}) {
  const cookieStore = await cookies()
  const token = cookieStore.get('mr_token')?.value

  if (!token) {
    redirect('/login')
  }

  // Build query params
  const params = new URLSearchParams()
  if (searchParams.status && searchParams.status !== 'all') params.set('status', searchParams.status)
  if (searchParams.account) params.set('account', searchParams.account)
  if (searchParams.from) params.set('from_date', searchParams.from)
  if (searchParams.to) params.set('to_date', searchParams.to)
  params.set('limit', '100')

  const [reportsRes, statsRes] = await Promise.all([
    fetchWithAuth(`/v1/admin/property-reports?${params.toString()}`, token),
    fetchWithAuth('/v1/admin/stats/property-reports', token),
  ])

  const reports: PropertyReport[] = reportsRes?.reports || []
  const stats: Stats = statsRes || { total: 0, this_month: 0, failed: 0, processing: 0 }

  const statusColors: Record<string, string> = {
    complete: "bg-green-100 text-green-800",
    processing: "bg-blue-100 text-blue-800",
    draft: "bg-yellow-100 text-yellow-800",
    failed: "bg-red-100 text-red-800",
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-display font-bold">Property Reports</h1>
        <p className="text-muted-foreground mt-2">Manage property reports across all accounts</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.this_month}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.processing}</div>
          </CardContent>
        </Card>

        <Card className={stats.failed > 0 ? "bg-red-50 border-red-200" : ""}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${stats.failed > 0 ? 'text-red-500' : 'text-muted-foreground'}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.failed > 0 ? 'text-red-600' : ''}`}>
              {stats.failed}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <PropertyReportsFilters />

      {/* Reports Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Property Reports ({reports.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {reports.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No property reports found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Property</TableHead>
                  <TableHead>Account</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Views</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.map((report) => (
                  <TableRow key={report.id}>
                    <TableCell>
                      <Link 
                        href={`/app/admin/property-reports/${report.id}`}
                        className="hover:underline"
                      >
                        <p className="font-medium text-sm">{report.property_address}</p>
                        <p className="text-xs text-muted-foreground">
                          {report.property_city}, {report.property_state}
                        </p>
                      </Link>
                    </TableCell>
                    <TableCell>
                      <p className="text-sm">{report.account_name}</p>
                      <p className="text-xs text-muted-foreground">{report.user_email}</p>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="capitalize">
                        {report.report_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[report.status] || "bg-gray-100"}>
                        {report.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm font-medium">{report.view_count}</span>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {formatTimeAgo(report.created_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Link href={`/app/admin/property-reports/${report.id}`}>
                          <button className="p-2 hover:bg-muted rounded-md">
                            <Eye className="w-4 h-4" />
                          </button>
                        </Link>
                        {report.pdf_url && (
                          <a href={report.pdf_url} target="_blank" rel="noopener noreferrer">
                            <button className="p-2 hover:bg-muted rounded-md">
                              <Download className="w-4 h-4" />
                            </button>
                          </a>
                        )}
                        {report.short_code && (
                          <a href={`/p/${report.short_code}`} target="_blank" rel="noopener noreferrer">
                            <button className="p-2 hover:bg-muted rounded-md text-purple-600">
                              <ExternalLink className="w-4 h-4" />
                            </button>
                          </a>
                        )}
                        <PropertyReportActions reportId={report.id} status={report.status} />
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

