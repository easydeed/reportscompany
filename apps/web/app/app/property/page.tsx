"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Plus, Download, Eye, Trash2, QrCode, ExternalLink } from "lucide-react"
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
  created_at: string
}

export default function PropertyReportsPage() {
  const [reports, setReports] = useState<PropertyReport[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadReports()
  }, [])

  async function loadReports() {
    try {
      setLoading(true)
      const data = await apiFetch("/v1/property/reports")
      setReports(data.reports || [])
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
    } catch (e: any) {
      setError(e.message || "Failed to delete report")
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "complete":
        return <Badge className="bg-green-500/10 text-green-700 hover:bg-green-500/20">Complete</Badge>
      case "processing":
        return <Badge className="bg-blue-500/10 text-blue-700 hover:bg-blue-500/20">Processing</Badge>
      case "failed":
        return <Badge className="bg-red-500/10 text-red-700 hover:bg-red-500/20">Failed</Badge>
      case "draft":
        return <Badge className="bg-yellow-500/10 text-yellow-700 hover:bg-yellow-500/20">Draft</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const getReportTypeBadge = (type: string) => {
    return type === "seller" 
      ? <Badge variant="outline" className="border-purple-300 text-purple-700">Seller</Badge>
      : <Badge variant="outline" className="border-blue-300 text-blue-700">Buyer</Badge>
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="font-bold text-3xl">Property Reports</h1>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-bold text-3xl mb-2">Property Reports</h1>
          <p className="text-muted-foreground">Generate seller and buyer property reports with QR codes</p>
        </div>
        <Link href="/app/property/new">
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            Create Report
          </Button>
        </Link>
      </div>

      {error && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

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
                    <p className="text-sm text-muted-foreground">No property reports yet</p>
                    <Link href="/app/property/new">
                      <Button size="sm" variant="outline">Create your first property report</Button>
                    </Link>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              reports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell>
                    <div>
                      <p className="font-medium text-sm">{report.property_address}</p>
                      <p className="text-xs text-muted-foreground">
                        {report.property_city}, {report.property_state}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>{getReportTypeBadge(report.report_type)}</TableCell>
                  <TableCell>{getStatusBadge(report.status)}</TableCell>
                  <TableCell>
                    <span className="text-sm font-medium">{report.view_count}</span>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">{new Date(report.created_at).toLocaleDateString()}</span>
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
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-purple-600 hover:text-purple-700">
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
                                Are you sure you want to delete this property report? This action cannot be undone.
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

