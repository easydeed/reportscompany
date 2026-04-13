'use client'

import { useEffect, useState, useMemo } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
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
  Download,
  Timer,
  Search,
  X,
  RefreshCw,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

interface Report {
  id: string
  account_name: string
  report_type: string
  city: string | null
  zips: string[] | null
  status: string
  duration_ms: number | null
  error: string | null
  pdf_url: string | null
  created_at: string
}

const REPORT_TYPE_LABELS: Record<string, string> = {
  new_listings_gallery: "New Listings Gallery",
  closed: "Closed Sales",
  market_snapshot: "Market Snapshot",
  inventory: "Active Inventory",
  featured_listings: "Featured Listings",
  open_houses: "Open Houses",
  price_bands: "Price Bands",
  new_listings: "New Listings Analytics",
}

const STATUS_STYLES: Record<string, string> = {
  completed: "bg-green-100 text-green-800",
  complete: "bg-green-100 text-green-800",
  generating: "bg-yellow-100 text-yellow-800",
  processing: "bg-yellow-100 text-yellow-800",
  queued: "bg-gray-100 text-gray-700",
  pending: "bg-gray-100 text-gray-700",
  failed: "bg-red-100 text-red-800",
}

function formatTimeAgo(dateString: string | null): string {
  if (!dateString) return "—"
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 30) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function formatDuration(ms: number | null): string {
  if (!ms) return "—"
  return `${(ms / 1000).toFixed(1)}s`
}

function getArea(report: Report): string {
  if (report.city) return report.city
  if (report.zips?.length) return `ZIP ${report.zips[0]}${report.zips.length > 1 ? ` +${report.zips.length - 1}` : ""}`
  return "—"
}

export default function AdminReportsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [retryingId, setRetryingId] = useState<string | null>(null)
  const { toast } = useToast()

  const filterStatus = searchParams.get("status") || "all"
  const filterType = searchParams.get("report_type") || "all"
  const [accountSearch, setAccountSearch] = useState(searchParams.get("account") || "")

  useEffect(() => {
    async function fetchReports() {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        if (filterStatus !== "all") params.set("status", filterStatus)
        if (filterType !== "all") params.set("report_type", filterType)
        const acctId = searchParams.get("account_id")
        if (acctId) params.set("account_id", acctId)
        const acct = searchParams.get("account")
        if (acct) params.set("account", acct)
        params.set("limit", "200")

        const res = await fetch(`/api/proxy/v1/admin/reports?${params.toString()}`, { credentials: "include" })
        if (res.ok) {
          const data = await res.json()
          setReports(data?.reports || data || [])
        }
      } catch (err) {
        console.error("Failed to fetch reports:", err)
      } finally {
        setLoading(false)
      }
    }
    fetchReports()
  }, [searchParams, filterStatus, filterType])

  const stats = useMemo(() => {
    const now = new Date()
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
    const recent = reports.filter(r => new Date(r.created_at) >= thirtyDaysAgo)
    const failed = recent.filter(r => r.status === "failed").length
    const durations = recent.map(r => r.duration_ms).filter((d): d is number => d != null && d > 0)
    const avgDuration = durations.length > 0 ? durations.reduce((a, b) => a + b, 0) / durations.length : 0

    return {
      total30d: recent.length,
      failed,
      avgDuration,
    }
  }, [reports])

  function updateFilter(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString())
    if (value && value !== "all") {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    router.push(`/app/admin/reports?${params.toString()}`)
  }

  function clearFilters() {
    setAccountSearch("")
    router.push("/app/admin/reports")
  }

  async function handleRetry(reportId: string) {
    setRetryingId(reportId)
    try {
      const res = await fetch(`/api/proxy/v1/admin/reports/${reportId}/retry`, {
        method: "POST",
        credentials: "include",
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || data.error || "Retry failed")
      }
      setReports((prev) =>
        prev.map((r) => (r.id === reportId ? { ...r, status: "queued", error: null } : r))
      )
      toast({ title: "Report re-queued", description: "Report has been re-queued for generation." })
    } catch (err) {
      console.error("Retry failed:", err)
      toast({
        title: "Retry failed",
        description: err instanceof Error ? err.message : "Could not retry report",
        variant: "destructive",
      })
    } finally {
      setRetryingId(null)
    }
  }

  const hasFilters = filterStatus !== "all" || filterType !== "all" || searchParams.get("account") || searchParams.get("account_id")

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-72" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
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
        <h1 className="text-3xl font-display font-bold">Market Reports</h1>
        <p className="text-muted-foreground mt-2">All market report generations across accounts</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports (30d)</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{stats.total30d}</div></CardContent>
        </Card>
        <Card className={stats.failed > 0 ? "bg-red-50 border-red-200" : ""}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed (30d)</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${stats.failed > 0 ? "text-red-500" : "text-muted-foreground"}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.failed > 0 ? "text-red-600" : ""}`}>{stats.failed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            <Timer className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.avgDuration ? `${(stats.avgDuration / 1000).toFixed(1)}s` : "—"}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by account..."
            value={accountSearch}
            onChange={(e) => setAccountSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && updateFilter("account", accountSearch)}
            className="pl-9"
          />
        </div>

        <Select value={filterType} onValueChange={(v) => updateFilter("report_type", v)}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Report Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {Object.entries(REPORT_TYPE_LABELS).map(([id, label]) => (
              <SelectItem key={id} value={id}>{label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filterStatus} onValueChange={(v) => updateFilter("status", v)}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="queued">Queued</SelectItem>
            <SelectItem value="generating">Generating</SelectItem>
            <SelectItem value="completed">Complete</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>

        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="w-4 h-4 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Market Reports ({reports.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {reports.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No reports found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-[11px] uppercase tracking-wider">Report Type</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">City / Area</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Account</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Status</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Duration</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Generated</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">PDF</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.map((report) => (
                  <TableRow key={report.id}>
                    <TableCell>
                      <Badge variant="outline" className="text-xs font-medium">
                        {REPORT_TYPE_LABELS[report.report_type] || report.report_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{getArea(report)}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{report.account_name}</TableCell>
                    <TableCell>
                      <Badge className={STATUS_STYLES[report.status] || "bg-gray-100"}>
                        {report.status}
                      </Badge>
                      {report.error && (
                        <span className="ml-2 text-xs text-red-600 cursor-help" title={report.error}>
                          (error)
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-sm text-muted-foreground">
                      {formatDuration(report.duration_ms)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatTimeAgo(report.created_at)}
                    </TableCell>
                    <TableCell>
                      {report.pdf_url ? (
                        <a href={report.pdf_url} target="_blank" rel="noopener noreferrer">
                          <button className="p-2 hover:bg-muted rounded-md text-primary">
                            <Download className="w-4 h-4" />
                          </button>
                        </a>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {report.status === "failed" && (
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={retryingId === report.id}
                          onClick={() => handleRetry(report.id)}
                          className="h-7 text-xs"
                        >
                          <RefreshCw className={`w-3 h-3 mr-1 ${retryingId === report.id ? "animate-spin" : ""}`} />
                          Retry
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {reports.length > 0 && (
            <p className="text-xs text-muted-foreground text-center mt-4">
              Showing {reports.length} report{reports.length !== 1 ? "s" : ""}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
