'use client'

import { Button } from "@/components/ui/button"
import { Plus, Download, Eye, FileJson, Share2, FileText } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import Link from "next/link"
import { PageHeader } from "@/components/page-header"
import { StatusBadge } from "@/components/status-badge"
import { EmptyState } from "@/components/empty-state"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useReports } from "@/hooks/use-api"

type Report = {
  id: string
  report_type: string
  city?: string
  status: "completed" | "processing" | "pending" | "failed"
  html_url?: string
  json_url?: string
  pdf_url?: string
  generated_at: string
}

export default function ReportsPage() {
  const { data, isLoading: loading, error: queryError } = useReports()
  const reports: Report[] = data?.reports || []
  const error = !!queryError

  return (
    <div className="space-y-5">
      <PageHeader
        title="Market Reports"
        description="Manage and generate your market reports"
        action={
          <Button asChild size="sm">
            <Link href="/app/reports/new">
              <Plus className="w-4 h-4 mr-1.5" />
              New Report
            </Link>
          </Button>
        }
      />

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          API temporarily unavailable. Please try again in a moment.
        </div>
      )}

      {loading ? (
        <ReportsTableSkeleton />
      ) : reports.length === 0 && !error ? (
        <EmptyState
          icon={<FileText className="w-6 h-6" />}
          title="No reports yet"
          description="Create your first market report to get started with data-driven insights."
          action={{
            label: "Create Report",
            onClick: () => { window.location.href = '/app/reports/new' }
          }}
        />
      ) : (
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/40 hover:bg-muted/40 border-b border-border">
                <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Report</TableHead>
                <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Area</TableHead>
                <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Created</TableHead>
                <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Status</TableHead>
                <TableHead className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] py-2.5">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {reports.map((r) => (
                <TableRow key={r.id} className="hover:bg-muted/30 transition-colors border-b border-border/50 last:border-0">
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
          <div className="flex items-center justify-between px-4 py-2.5 border-t border-border bg-muted/20">
            <p className="text-[11px] text-muted-foreground">
              Showing {reports.length} report{reports.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

function ReportsTableSkeleton() {
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
      <div className="px-4 py-3 border-b border-border bg-muted/40">
        <div className="grid grid-cols-5 gap-4">
          {['Report', 'Area', 'Created', 'Status', 'Actions'].map((h) => (
            <Skeleton key={h} className="h-3 w-16" />
          ))}
        </div>
      </div>
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="px-4 py-3 border-b border-border/50 flex items-center gap-4">
          <Skeleton className="h-4 w-32 flex-1" />
          <Skeleton className="h-4 w-20 flex-1" />
          <Skeleton className="h-4 w-24 flex-1" />
          <Skeleton className="h-5 w-16 rounded-full flex-1" />
          <div className="flex gap-1 flex-1">
            <Skeleton className="h-8 w-8 rounded" />
            <Skeleton className="h-8 w-8 rounded" />
          </div>
        </div>
      ))}
    </div>
  )
}
