"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import {
  Plus,
  Download,
  Eye,
  Trash2,
  QrCode,
  FileText,
  Loader2,
  CheckCircle,
  Filter,
  X,
} from "lucide-react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import Link from "next/link"
import { apiFetch } from "@/lib/api"
import { PageHeader } from "@/components/page-header"
import { StatusBadge } from "@/components/status-badge"
import { MetricCard } from "@/components/metric-card"
import { EmptyState } from "@/components/empty-state"
import { TableSkeleton } from "@/components/page-skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

type PropertyReport = {
  id: string
  report_type: "seller" | "buyer"
  status: "draft" | "processing" | "complete" | "failed"
  property_address: string
  property_city: string
  property_state: string
  short_code: string
  qr_code_url?: string
  pdf_url?: string
  view_count: number
  unique_visitors?: number
  created_at: string
}

type Stats = {
  total: number
  thisMonth: number
  processing: number
  complete: number
}

export default function PropertyReportsPage() {
  const searchParams = useSearchParams()

  const [reports, setReports] = useState<PropertyReport[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [stats, setStats] = useState<Stats>({ total: 0, thisMonth: 0, processing: 0, complete: 0 })

  // Filter
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get("status") || "all")

  useEffect(() => {
    loadReports()
  }, [statusFilter])

  async function loadReports() {
    try {
      setLoading(true)
      
      // Always fetch ALL reports first (for stats), then filter client-side
      // This eliminates the duplicate API call we were making before
      const allData = await apiFetch("/v1/property/reports?limit=100")
      const allReports: PropertyReport[] = allData.reports || []
      
      // Calculate stats from all reports (single API call)
      const now = new Date()
      const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)

      setStats({
        total: allReports.length,
        thisMonth: allReports.filter((r) => new Date(r.created_at) >= startOfMonth).length,
        processing: allReports.filter((r) => r.status === "processing").length,
        complete: allReports.filter((r) => r.status === "complete").length,
      })

      // Filter client-side based on status (no second API call needed)
      const filteredReports = statusFilter && statusFilter !== "all"
        ? allReports.filter((r) => r.status === statusFilter)
        : allReports

      setReports(filteredReports)
      setTotal(allData.total || allReports.length)
      setError(null)
    } catch (e: any) {
      setError(e.message || "Failed to load reports")
    } finally {
      setLoading(false)
    }
  }

  async function deleteReport(id: string) {
    try {
      await apiFetch(`/v1/property/reports/${id}`, { method: "DELETE" })
      setReports((prev) => prev.filter((r) => r.id !== id))
      setStats((prev) => ({ ...prev, total: prev.total - 1 }))
    } catch (e: any) {
      setError(e.message || "Failed to delete report")
    }
  }

  if (loading && reports.length === 0) {
    return (
      <div className="space-y-5">
        <PageHeader
          title="Property Reports"
          description="Generate seller and buyer property reports with QR codes"
          action={
            <Button disabled size="sm">
              <Plus className="w-4 h-4 mr-1.5" />
              Create Report
            </Button>
          }
        />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-card border border-border rounded-xl p-5 shadow-sm animate-pulse">
              <div className="h-4 w-20 bg-muted rounded mb-3" />
              <div className="h-7 w-12 bg-muted rounded" />
            </div>
          ))}
        </div>
        <TableSkeleton rows={5} />
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <PageHeader
        title="Property Reports"
        description="Generate seller and buyer property reports with QR codes"
        action={
          <Button asChild size="sm">
            <Link href="/app/property/new">
              <Plus className="w-4 h-4 mr-1.5" />
              Create Report
            </Link>
          </Button>
        }
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          label="Total Reports"
          value={stats.total}
          icon={<FileText className="w-4 h-4" />}
          index={0}
        />
        <MetricCard
          label="This Month"
          value={stats.thisMonth}
          icon={<CheckCircle className="w-4 h-4" />}
          index={1}
        />
        <MetricCard
          label="Processing"
          value={stats.processing}
          icon={<Loader2 className="w-4 h-4" />}
          index={2}
        />
        <MetricCard
          label="Completed"
          value={stats.complete}
          icon={<CheckCircle className="w-4 h-4" />}
          index={3}
        />
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {reports.length === 0 && statusFilter === "all" ? (
        <EmptyState
          icon={<FileText className="w-6 h-6" />}
          title="No property reports yet"
          description="Create professional property reports with QR codes for sellers and buyers."
          action={{
            label: "Create Property Report",
            onClick: () => window.location.href = "/app/property/new"
          }}
        />
      ) : (
        <>
          {/* Filters */}
          <div className="flex items-center gap-3">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <Filter className="w-4 h-4 mr-2" />
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="complete">Complete</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>

            {statusFilter !== "all" && (
              <Button variant="ghost" size="sm" onClick={() => setStatusFilter("all")}>
                <X className="w-4 h-4 mr-1" />
                Clear
              </Button>
            )}
          </div>

          {/* Table */}
          <div className="bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40 hover:bg-muted/40 border-b border-border">
                  <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Property</TableHead>
                  <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Type</TableHead>
                  <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Status</TableHead>
                  <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Views</TableHead>
                  <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Created</TableHead>
                  <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-32 text-center">
                      <div className="flex flex-col items-center gap-2">
                        <FileText className="w-8 h-8 text-muted-foreground" />
                        <p className="text-sm text-muted-foreground">
                          No reports match your filter
                        </p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  reports.map((report) => (
                    <TableRow key={report.id} className="hover:bg-muted/30 transition-colors">
                      <TableCell>
                        <Link href={`/app/property/${report.id}`} className="hover:underline">
                          <p className="text-sm font-medium">{report.property_address}</p>
                          <p className="text-xs text-muted-foreground">
                            {report.property_city}, {report.property_state}
                          </p>
                        </Link>
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
                          report.report_type === "seller" 
                            ? "bg-indigo-50 text-indigo-700 border-indigo-200" 
                            : "bg-blue-50 text-blue-700 border-blue-200"
                        }`}>
                          {report.report_type === "seller" ? "Seller" : "Buyer"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={report.status === "complete" ? "completed" : report.status} />
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <span className="font-medium">{report.view_count}</span>
                          {report.unique_visitors !== undefined && (
                            <span className="text-muted-foreground ml-1">
                              ({report.unique_visitors} unique)
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-muted-foreground">
                          {new Date(report.created_at).toLocaleDateString()}
                        </span>
                      </TableCell>
                      <TableCell>
                        <TooltipProvider delayDuration={300}>
                          <div className="flex gap-1">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Link href={`/app/property/${report.id}`}>
                                  <Button variant="ghost" size="icon" className="h-8 w-8">
                                    <Eye className="w-4 h-4" />
                                  </Button>
                                </Link>
                              </TooltipTrigger>
                              <TooltipContent>View Details</TooltipContent>
                            </Tooltip>

                            {report.pdf_url && (
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <a href={report.pdf_url} target="_blank" rel="noopener noreferrer">
                                    <Button variant="ghost" size="icon" className="h-8 w-8">
                                      <Download className="w-4 h-4" />
                                    </Button>
                                  </a>
                                </TooltipTrigger>
                                <TooltipContent>Download PDF</TooltipContent>
                              </Tooltip>
                            )}

                            {report.short_code && (
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <a href={`/p/${report.short_code}`} target="_blank" rel="noopener noreferrer">
                                    <Button variant="ghost" size="icon" className="h-8 w-8 text-primary hover:text-primary/80">
                                      <QrCode className="w-4 h-4" />
                                    </Button>
                                  </a>
                                </TooltipTrigger>
                                <TooltipContent>View Public Page</TooltipContent>
                              </Tooltip>
                            )}

                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-50">
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Delete Property Report</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    Are you sure you want to delete this property report? This
                                    will also remove the landing page and QR code. This action
                                    cannot be undone.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => deleteReport(report.id)}
                                    className="bg-red-600 hover:bg-red-700"
                                  >
                                    Delete
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </div>
                        </TooltipProvider>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
            
            {/* Footer */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-border">
              <p className="text-xs text-muted-foreground">
                Showing {reports.length} of {total} report{total !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
