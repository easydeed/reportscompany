"use client"

import { useEffect, useState } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Plus,
  Download,
  Eye,
  Trash2,
  QrCode,
  FileText,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
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
import { Card, CardContent } from "@/components/ui/card"
import Link from "next/link"
import { apiFetch } from "@/lib/api"
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
  failed: number
}

export default function PropertyReportsPage() {
  const searchParams = useSearchParams()
  const router = useRouter()

  const [reports, setReports] = useState<PropertyReport[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [stats, setStats] = useState<Stats>({ total: 0, thisMonth: 0, processing: 0, failed: 0 })

  // Filter
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get("status") || "all")

  useEffect(() => {
    loadReports()
  }, [statusFilter])

  async function loadReports() {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (statusFilter && statusFilter !== "all") {
        params.set("status", statusFilter)
      }
      params.set("limit", "100")

      const data = await apiFetch(`/v1/property/reports?${params.toString()}`)
      const fetchedReports = data.reports || []
      setReports(fetchedReports)
      setTotal(data.total || fetchedReports.length)

      // Calculate stats from all reports (need separate call for accurate stats)
      const allData = await apiFetch("/v1/property/reports?limit=100")
      const allReports = allData.reports || []
      
      const now = new Date()
      const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)

      setStats({
        total: allReports.length,
        thisMonth: allReports.filter((r: PropertyReport) => new Date(r.created_at) >= startOfMonth).length,
        processing: allReports.filter((r: PropertyReport) => r.status === "processing").length,
        failed: allReports.filter((r: PropertyReport) => r.status === "failed").length,
      })

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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "complete":
        return (
          <Badge className="bg-green-500/10 text-green-700 hover:bg-green-500/20">
            <CheckCircle className="w-3 h-3 mr-1" />
            Complete
          </Badge>
        )
      case "processing":
        return (
          <Badge className="bg-blue-500/10 text-blue-700 hover:bg-blue-500/20">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Processing
          </Badge>
        )
      case "failed":
        return (
          <Badge className="bg-red-500/10 text-red-700 hover:bg-red-500/20">
            <AlertCircle className="w-3 h-3 mr-1" />
            Failed
          </Badge>
        )
      case "draft":
        return (
          <Badge className="bg-yellow-500/10 text-yellow-700 hover:bg-yellow-500/20">
            <Clock className="w-3 h-3 mr-1" />
            Draft
          </Badge>
        )
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const getReportTypeBadge = (type: string) => {
    return type === "seller" ? (
      <Badge variant="outline" className="border-purple-300 text-purple-700">
        Seller
      </Badge>
    ) : (
      <Badge variant="outline" className="border-blue-300 text-blue-700">
        Buyer
      </Badge>
    )
  }

  if (loading && reports.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="font-bold text-3xl">Property Reports</h1>
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="w-4 h-4 animate-spin" />
          Loading...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-bold text-3xl mb-2">Property Reports</h1>
          <p className="text-muted-foreground">
            Generate seller and buyer property reports with QR codes
          </p>
        </div>
        <Link href="/app/property/new">
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            Create Report
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <FileText className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-sm text-muted-foreground">Total Reports</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.thisMonth}</p>
                <p className="text-sm text-muted-foreground">This Month</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Loader2 className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.processing}</p>
                <p className="text-sm text-muted-foreground">Processing</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
                <AlertCircle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.failed}</p>
                <p className="text-sm text-muted-foreground">Failed</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {error && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

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

        <div className="flex-1" />

        <span className="text-sm text-muted-foreground">
          {total} report{total !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Property</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Views</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reports.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="h-32 text-center">
                  <div className="flex flex-col items-center gap-2">
                    <FileText className="w-8 h-8 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      {statusFilter !== "all"
                        ? "No reports match your filter"
                        : "No property reports yet"}
                    </p>
                    {statusFilter === "all" && (
                      <Link href="/app/property/new">
                        <Button size="sm" variant="outline">
                          Create your first property report
                        </Button>
                      </Link>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              reports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell>
                    <Link
                      href={`/app/property/${report.id}`}
                      className="hover:underline"
                    >
                      <p className="font-medium text-sm">{report.property_address}</p>
                      <p className="text-xs text-muted-foreground">
                        {report.property_city}, {report.property_state}
                      </p>
                    </Link>
                  </TableCell>
                  <TableCell>{getReportTypeBadge(report.report_type)}</TableCell>
                  <TableCell>{getStatusBadge(report.status)}</TableCell>
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
                    <span className="text-sm">
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
                              <a
                                href={report.pdf_url}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
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
                              <a
                                href={`/p/${report.short_code}`}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8 text-purple-600 hover:text-purple-700"
                                >
                                  <QrCode className="w-4 h-4" />
                                </Button>
                              </a>
                            </TooltipTrigger>
                            <TooltipContent>View Public Page</TooltipContent>
                          </Tooltip>
                        )}

                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
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
      </div>
    </div>
  )
}
