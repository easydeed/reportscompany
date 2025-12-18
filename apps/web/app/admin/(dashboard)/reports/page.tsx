"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  FileText,
  RefreshCw,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  AlertTriangle,
  ExternalLink,
} from "lucide-react"

interface Report {
  id: string
  account_id: string
  account_name: string
  report_type: string
  status: string
  params: Record<string, unknown>
  has_result: boolean
  pdf_url: string | null
  error: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
  duration_ms: number | null
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [typeFilter, setTypeFilter] = useState<string>("all")

  useEffect(() => {
    fetchReports()
  }, [statusFilter, typeFilter])

  async function fetchReports() {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (statusFilter !== "all") params.set("status", statusFilter)
      if (typeFilter !== "all") params.set("report_type", typeFilter)
      params.set("limit", "100")

      const res = await fetch(`/api/v1/admin/reports?${params.toString()}`, {
        credentials: "include",
      })
      if (res.ok) {
        const data = await res.json()
        setReports(data.reports || [])
      }
    } catch (error) {
      console.error("Failed to fetch reports:", error)
    } finally {
      setLoading(false)
    }
  }

  const formatTimeAgo = (date: string | null) => {
    if (!date) return "-"
    const d = new Date(date)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    const mins = Math.floor(diff / (1000 * 60))
    if (mins < 1) return "Just now"
    if (mins < 60) return `${mins}m ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours}h ago`
    const days = Math.floor(hours / 24)
    return `${days}d ago`
  }

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle className="h-4 w-4 text-emerald-500" />
      case "failed": return <XCircle className="h-4 w-4 text-red-500" />
      case "processing": return <Activity className="h-4 w-4 text-blue-500" />
      case "pending": return <Clock className="h-4 w-4 text-amber-500" />
      default: return <Clock className="h-4 w-4 text-slate-400" />
    }
  }

  const statusColor = (status: string) => {
    switch (status) {
      case "completed": return "bg-emerald-100 text-emerald-700 border-emerald-200"
      case "failed": return "bg-red-100 text-red-700 border-red-200"
      case "processing": return "bg-blue-100 text-blue-700 border-blue-200"
      case "pending": return "bg-amber-100 text-amber-700 border-amber-200"
      default: return "bg-slate-100 text-slate-600"
    }
  }

  // Calculate stats
  const stats = {
    total: reports.length,
    completed: reports.filter(r => r.status === "completed").length,
    failed: reports.filter(r => r.status === "failed").length,
    processing: reports.filter(r => r.status === "processing").length,
    pending: reports.filter(r => r.status === "pending").length,
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Reports</h1>
          <p className="text-slate-500 mt-1">Monitor all report generations across the platform</p>
        </div>
        <Button
          variant="outline"
          onClick={fetchReports}
          className="border-slate-300 text-slate-600 hover:bg-slate-50"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-5 gap-4">
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total</p>
                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              </div>
              <FileText className="h-6 w-6 text-slate-300" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Completed</p>
                <p className="text-2xl font-bold text-emerald-600">{stats.completed}</p>
              </div>
              <CheckCircle className="h-6 w-6 text-emerald-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Processing</p>
                <p className="text-2xl font-bold text-blue-600">{stats.processing}</p>
              </div>
              <Activity className="h-6 w-6 text-blue-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Pending</p>
                <p className="text-2xl font-bold text-amber-600">{stats.pending}</p>
              </div>
              <Clock className="h-6 w-6 text-amber-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Failed</p>
                <p className="text-2xl font-bold text-red-600">{stats.failed}</p>
              </div>
              <XCircle className="h-6 w-6 text-red-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40 bg-white border-slate-300 text-slate-900">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent className="bg-white border-slate-200">
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-48 bg-white border-slate-300 text-slate-900">
                <SelectValue placeholder="Report Type" />
              </SelectTrigger>
              <SelectContent className="bg-white border-slate-200">
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="market_snapshot">Market Snapshot</SelectItem>
                <SelectItem value="new_listings">New Listings</SelectItem>
                <SelectItem value="new_listings_gallery">New Listings Gallery</SelectItem>
                <SelectItem value="featured_listings">Featured Listings</SelectItem>
                <SelectItem value="closed_sales">Closed Sales</SelectItem>
                <SelectItem value="inventory">Inventory</SelectItem>
                <SelectItem value="price_bands">Price Bands</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Reports Table */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardContent className="pt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            </div>
          ) : reports.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">No reports found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 hover:bg-transparent">
                  <TableHead className="text-slate-500">Account</TableHead>
                  <TableHead className="text-slate-500">Type</TableHead>
                  <TableHead className="text-slate-500">Status</TableHead>
                  <TableHead className="text-slate-500">Duration</TableHead>
                  <TableHead className="text-slate-500">Created</TableHead>
                  <TableHead className="text-slate-500">Error</TableHead>
                  <TableHead className="text-slate-500 w-16">PDF</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.map((report) => (
                  <TableRow key={report.id} className="border-slate-100">
                    <TableCell>
                      <p className="text-slate-900 font-medium">{report.account_name}</p>
                    </TableCell>
                    <TableCell className="text-slate-500">
                      {report.report_type.replace(/_/g, ' ')}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {statusIcon(report.status)}
                        <Badge className={statusColor(report.status)}>
                          {report.status}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-600 font-mono">
                      {report.duration_ms ? `${(report.duration_ms / 1000).toFixed(1)}s` : "-"}
                    </TableCell>
                    <TableCell className="text-slate-400">
                      {formatTimeAgo(report.created_at)}
                    </TableCell>
                    <TableCell>
                      {report.error && (
                        <div className="flex items-center gap-1 text-red-600" title={report.error}>
                          <AlertTriangle className="h-4 w-4" />
                          <span className="text-xs truncate max-w-32">{report.error}</span>
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      {report.pdf_url && (
                        <a
                          href={report.pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-violet-600 hover:text-violet-700"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      )}
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
