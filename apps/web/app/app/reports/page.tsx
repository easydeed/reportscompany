"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Plus, Download, Eye, FileJson, FileText as FileTextIcon } from "lucide-react"
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

type Report = {
  id: string
  report_type: string
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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge className="bg-green-500/10 text-green-700 hover:bg-green-500/20">Completed</Badge>
      case "processing":
        return <Badge className="bg-blue-500/10 text-blue-700 hover:bg-blue-500/20">Processing</Badge>
      case "failed":
        return <Badge className="bg-red-500/10 text-red-700 hover:bg-red-500/20">Failed</Badge>
      case "pending":
        return <Badge className="bg-yellow-500/10 text-yellow-700 hover:bg-yellow-500/20">Pending</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="font-bold text-3xl">Reports</h1>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-bold text-3xl mb-2">Reports</h1>
          <p className="text-muted-foreground">Manage and generate your market reports</p>
        </div>
        <Link href="/app/reports/new">
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            New Report
          </Button>
        </Link>
      </div>

      {offline && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-800">
          API temporarily unavailable. Please try again in a moment.
        </div>
      )}

      <div className="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Report</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Files</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reports.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="h-32 text-center">
                  <div className="flex flex-col items-center gap-2">
                    <p className="text-sm text-muted-foreground">
                      {offline ? "API offline. Try again shortly." : "No reports yet"}
                    </p>
                    {!offline && (
                      <Link href="/app/reports/new">
                        <Button size="sm" variant="outline">Create your first report</Button>
                      </Link>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              reports.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>
                    <div>
                      <p className="font-medium text-sm capitalize">{r.report_type.replace(/_/g, " ")}</p>
                      <p className="text-xs text-muted-foreground">ID: {r.id.slice(0, 8)}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">{new Date(r.generated_at).toLocaleString()}</span>
                  </TableCell>
                  <TableCell>{getStatusBadge(r.status)}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      {r.html_url && (
                        <a href={r.html_url} target="_blank" rel="noopener noreferrer">
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Eye className="w-4 h-4" />
                          </Button>
                        </a>
                      )}
                      {r.pdf_url && (
                        <a href={r.pdf_url} target="_blank" rel="noopener noreferrer">
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Download className="w-4 h-4" />
                          </Button>
                        </a>
                      )}
                      {r.json_url && (
                        <a href={r.json_url} target="_blank" rel="noopener noreferrer">
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <FileJson className="w-4 h-4" />
                          </Button>
                        </a>
                      )}
                    </div>
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
