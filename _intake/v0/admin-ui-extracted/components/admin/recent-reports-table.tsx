"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { CheckCircle2, Clock, XCircle } from "lucide-react"
import type { RecentReport } from "./types"

interface RecentReportsTableProps {
  reports: RecentReport[]
}

export function RecentReportsTable({ reports }: RecentReportsTableProps) {
  const getStatusBadge = (status: RecentReport["status"]) => {
    switch (status) {
      case "completed":
        return (
          <Badge variant="outline" className="border-green-500/50 bg-green-500/10 text-green-700 dark:text-green-400">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Completed
          </Badge>
        )
      case "processing":
        return (
          <Badge variant="outline" className="border-blue-500/50 bg-blue-500/10 text-blue-700 dark:text-blue-400">
            <Clock className="w-3 h-3 mr-1" />
            Processing
          </Badge>
        )
      case "failed":
        return (
          <Badge variant="outline" className="border-red-500/50 bg-red-500/10 text-red-700 dark:text-red-400">
            <XCircle className="w-3 h-3 mr-1" />
            Failed
          </Badge>
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
    <Card className="glass border-border">
      <div className="p-6 border-b border-border">
        <h3 className="text-lg font-display font-semibold text-foreground">Recent Reports</h3>
        <p className="text-sm text-muted-foreground">Latest generated reports across all organizations</p>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-border">
              <TableHead className="font-semibold">Type</TableHead>
              <TableHead className="font-semibold">Organization</TableHead>
              <TableHead className="font-semibold">Status</TableHead>
              <TableHead className="font-semibold text-right">Duration</TableHead>
              <TableHead className="font-semibold">Finished</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reports.map((report) => (
              <TableRow key={report.id} className="border-border">
                <TableCell className="font-medium">{report.type}</TableCell>
                <TableCell className="text-muted-foreground">{report.org}</TableCell>
                <TableCell>{getStatusBadge(report.status)}</TableCell>
                <TableCell className="text-right font-mono text-sm">{formatDuration(report.duration)}</TableCell>
                <TableCell className="text-muted-foreground">{formatDate(report.finished)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  )
}
