"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Plus, Download, Eye, FileJson, Share2, FileText, Loader2 } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import Link from "next/link"
import { apiFetch } from "@/lib/api"
import { PageHeader } from "@/components/page-header"
import { StatusBadge } from "@/components/status-badge"
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

type Report = {
  id: string
  report_type: string
  city?: string
  status: string
  html_url?: string
  json_url?: string
  pdf_url?: string
  generated_at: string
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [offline, setOffline] = useState(false)

  useEffect(() => {
    apiFetch("/v1/reports")
      .then((data: any) => {
        setReports(data.reports || [])
        setLoading(false)
      })
      .catch(() => {
        setOffline(true)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Market Reports"
          description="Manage and generate your market reports"
          action={
            <Button disabled>
              <Plus className="w-4 h-4 mr-2" />
              New Report
            </Button>
          }
        />
        <TableSkeleton rows={5} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Market Reports"
        description="Manage and generate your market reports"
        action={
          <Button asChild>
            <Link href="/app/reports/new">
              <Plus className="w-4 h-4 mr-2" />
              New Report
            </Link>
          </Button>
        }
      />

      {offline && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          API temporarily unavailable. Please try again in a moment.
        </div>
      )}

      {reports.length === 0 && !offline ? (
        <EmptyState
          icon={<FileText className="w-6 h-6" />}
          title="No reports yet"
          description="Create your first market report to get started with data-driven insights."
          action={{
            label: "Create Report",
            onClick: () => window.location.href = "/app/reports/new"
          }}
        />
      ) : (
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50 hover:bg-muted/50">
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Report</TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Area</TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Created</TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {reports.map((r) => (
                <TableRow key={r.id} className="hover:bg-muted/30 transition-colors">
                  <TableCell>
                    <p className="text-sm font-medium capitalize">{r.report_type.replace(/_/g, " ")}</p>
                  </TableCell>
                  <TableCell>
                    <p className="text-sm text-muted-foreground">{r.city || 'N/A'}</p>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-muted-foreground">
                      {new Date(r.generated_at).toLocaleDateString()}
                    </span>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={r.status} />
                  </TableCell>
                  <TableCell>
                    <TooltipProvider delayDuration={300}>
                      <div className="flex gap-1">
                        {r.html_url && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <a href={r.html_url} target="_blank" rel="noopener noreferrer">
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <Eye className="w-4 h-4" />
                                </Button>
                              </a>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Preview Report</p>
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {r.pdf_url && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <a href={r.pdf_url} target="_blank" rel="noopener noreferrer">
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <Download className="w-4 h-4" />
                                </Button>
                              </a>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Download PDF</p>
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {r.status === "completed" && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <a href={`/social/${r.id}`} target="_blank" rel="noopener noreferrer">
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-primary hover:text-primary/80">
                                  <Share2 className="w-4 h-4" />
                                </Button>
                              </a>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Share on Social Media</p>
                              <p className="text-xs text-muted-foreground">1080x1920 for Stories</p>
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {r.json_url && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <a href={r.json_url} target="_blank" rel="noopener noreferrer">
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <FileJson className="w-4 h-4" />
                                </Button>
                              </a>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>View JSON Data</p>
                            </TooltipContent>
                          </Tooltip>
                        )}
                      </div>
                    </TooltipProvider>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          
          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <p className="text-xs text-muted-foreground">
              Showing {reports.length} report{reports.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
