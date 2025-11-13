"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table"
import { Card } from "../ui/card"
import { Button } from "../ui/button"
import { RotateCcw, ExternalLink, MoreVertical } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "../ui/dropdown-menu"
import type { RecentReport } from "./types"

interface AdminReportsTableProps {
  reports: RecentReport[]
  onRetry?: (id: string) => void
  onImpersonate?: (org: string) => void
}

export function AdminReportsTable({ reports, onRetry, onImpersonate }: AdminReportsTableProps) {
  const getStatusBadge = (status: RecentReport["status"]) => {
    switch (status) {
      case "completed":
        return (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-400" />
            <span className="text-green-400 text-sm">Completed</span>
          </div>
        )
      case "processing":
        return (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-cyan-400 text-sm">Processing</span>
          </div>
        )
      case "failed":
        return (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-400" />
            <span className="text-red-400 text-sm">Failed</span>
          </div>
        )
    }
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(date)
  }

  return (
    <Card className="glass border-border/50 backdrop-blur-sm">
      <div className="p-6 border-b border-border/50">
        <h3 className="text-lg font-display font-semibold text-white">Recent Reports</h3>
        <p className="text-sm text-slate-400">Latest generated reports across all organizations</p>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-border/50">
              <TableHead className="font-semibold text-slate-300">Type</TableHead>
              <TableHead className="font-semibold text-slate-300">Organization</TableHead>
              <TableHead className="font-semibold text-slate-300">Status</TableHead>
              <TableHead className="font-semibold text-slate-300 text-right">Duration</TableHead>
              <TableHead className="font-semibold text-slate-300">Finished</TableHead>
              <TableHead className="font-semibold text-slate-300 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reports.map((report) => (
              <TableRow key={report.id} className="border-border/50 hover:bg-slate-800/30">
                <TableCell className="font-medium text-white">{report.type}</TableCell>
                <TableCell className="text-slate-400">{report.org}</TableCell>
                <TableCell>{getStatusBadge(report.status)}</TableCell>
                <TableCell className="text-right font-mono text-sm text-slate-300">
                  {formatDuration(report.duration)}
                </TableCell>
                <TableCell className="text-slate-400 font-mono text-sm">{formatDate(report.finished)}</TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <MoreVertical className="h-4 w-4" />
                        <span className="sr-only">Open menu</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="glass border-border/50">
                      {report.status === "failed" && (
                        <DropdownMenuItem onClick={() => onRetry?.(report.id)}>
                          <RotateCcw className="mr-2 h-4 w-4" />
                          Retry Report
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuItem onClick={() => onImpersonate?.(report.org)}>
                        <ExternalLink className="mr-2 h-4 w-4" />
                        Impersonate Org
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  )
}
