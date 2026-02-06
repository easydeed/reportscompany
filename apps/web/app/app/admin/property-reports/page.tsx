'use client'

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
  complete: "bg-green-100 text-green-800",
  processing: "bg-blue-100 text-blue-800",
  draft: "bg-yellow-100 text-yellow-800",
  failed: "bg-red-100 text-red-800",
}

export default function AdminPropertyReportsPage() {
  const searchParams = useSearchParams()
  const [reports, setReports] = useState<PropertyReport[]>([])
  const [stats, setStats] = useState<Stats>({ total: 0, this_month: 0, failed: 0, processing: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        const status = searchParams.get('status')
        const account = searchParams.get('account')
        const from = searchParams.get('from')
        const to = searchParams.get('to')

        if (status && status !== 'all') params.set('status', status)
        if (account) params.set('account', account)
        if (from) params.set('from_date', from)
        if (to) params.set('to_date', to)
        params.set('limit', '100')

        const [reportsRes, statsRes] = await Promise.all([
          fetch(`/api/proxy/v1/admin/property-reports?${params.toString()}`, { credentials: 'include' }),
          fetch('/api/proxy/v1/admin/stats/property-reports', { credentials: 'include' }),
        ])

        if (reportsRes.ok) {
          const data = await reportsRes.json()
          setReports(data?.reports || [])
        }
        if (statsRes.ok) {
          setStats(await statsRes.json())
        }
      } catch (err) {
        console.error('Failed to fetch property reports:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [searchParams])

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-72" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-8 w-16" /></CardContent></Card>
          ))}
        </div>
        <Card><CardContent className="pt-6">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="py-3 flex gap-4">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
          ))}
        </CardContent></Card>
      </div>
    )
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
          <CardContent><div className="text-2xl font-bold">{stats.total}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{stats.this_month}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{stats.processing}</div></CardContent>
        </Card>
        <Card className={stats.failed > 0 ? "bg-red-50 border-red-200" : ""}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${stats.failed > 0 ? 'text-red-500' : 'text-muted-foreground'}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.failed > 0 ? 'text-red-600' : ''}`}>{stats.failed}</div>
          </CardContent>
        </Card>
      </div>

      <PropertyReportsFilters />

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
                      <Link href={`/app/admin/property-reports/${report.id}`} className="hover:underline">
                        <p className="font-medium text-sm">{report.property_address}</p>
                        <p className="text-xs text-muted-foreground">{report.property_city}, {report.property_state}</p>
                      </Link>
                    </TableCell>
                    <TableCell>
                      <p className="text-sm">{report.account_name}</p>
                      <p className="text-xs text-muted-foreground">{report.user_email}</p>
                    </TableCell>
                    <TableCell><Badge variant="outline" className="capitalize">{report.report_type}</Badge></TableCell>
                    <TableCell><Badge className={statusColors[report.status] || "bg-gray-100"}>{report.status}</Badge></TableCell>
                    <TableCell><span className="text-sm font-medium">{report.view_count}</span></TableCell>
                    <TableCell className="text-muted-foreground text-sm">{formatTimeAgo(report.created_at)}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Link href={`/app/admin/property-reports/${report.id}`}>
                          <button className="p-2 hover:bg-muted rounded-md"><Eye className="w-4 h-4" /></button>
                        </Link>
                        {report.pdf_url && (
                          <a href={report.pdf_url} target="_blank" rel="noopener noreferrer">
                            <button className="p-2 hover:bg-muted rounded-md"><Download className="w-4 h-4" /></button>
                          </a>
                        )}
                        {report.short_code && (
                          <a href={`/p/${report.short_code}`} target="_blank" rel="noopener noreferrer">
                            <button className="p-2 hover:bg-muted rounded-md text-indigo-600"><ExternalLink className="w-4 h-4" /></button>
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
