"use client"

import { useState, useEffect, useMemo } from "react"
import Link from "next/link"
import {
  Search, FileText, Download, CheckCircle2, XCircle,
  Clock, ChevronLeft, ChevronRight, AlertCircle, Calendar, Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { PageHeader } from "@/components/page-header"

// ─── Types ───────────────────────────────────────────────────────────────────

interface ReportRow {
  id: string
  agent_name: string
  agent_id: string
  report_type: string
  city: string | null
  zip_codes: string[] | null
  status: "complete" | "failed" | "generating" | "pending"
  created_at: string
  pdf_url: string | null
  is_scheduled: boolean
}

interface Agent { id: string; name: string }

interface ReportsResponse {
  reports: ReportRow[]
  total: number
  agents?: Agent[]
  metrics?: { total_30d: number; complete: number; failed: number; generating: number }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatRelativeTime(dateStr: string | null): string {
  if (!dateStr) return "—"
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return "Just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days === 1) return "Yesterday"
  if (days < 7) return `${days} days ago`
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric" })
}

function formatReportType(slug: string): string {
  return slug.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatArea(city: string | null, zips: string[] | null): string {
  if (city) return city
  if (zips && zips.length > 0) return zips.length === 1 ? zips[0] : `${zips[0]} +${zips.length - 1}`
  return "—"
}

function StatusBadge({ status }: { status: ReportRow["status"] }) {
  if (status === "complete")
    return <Badge className="bg-green-50 text-green-700 border-green-200 gap-1 text-[11px]"><CheckCircle2 className="w-3 h-3" />Complete</Badge>
  if (status === "failed")
    return <Badge className="bg-red-50 text-red-700 border-red-200 gap-1 text-[11px]"><XCircle className="w-3 h-3" />Failed</Badge>
  return <Badge className="bg-amber-50 text-amber-700 border-amber-200 gap-1 text-[11px]"><Clock className="w-3 h-3" />Generating</Badge>
}

function MetricCard({ label, value, loading }: { label: string; value: number; loading: boolean }) {
  return (
    <div className="bg-card border border-border rounded-xl p-4 shadow-[var(--shadow-card)]">
      <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em] mb-1">{label}</p>
      {loading ? <Skeleton className="h-7 w-16" /> : (
        <p className="text-2xl font-bold text-foreground">{value.toLocaleString()}</p>
      )}
    </div>
  )
}

function TableSkeleton() {
  return (
    <div className="p-4 space-y-2">
      {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-11 w-full" />)}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 25

export default function AffiliateReportsPage() {
  const [data, setData] = useState<ReportsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState("")
  const [agentFilter, setAgentFilter] = useState("all")
  const [typeFilter, setTypeFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")
  const [page, setPage] = useState(0)

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const qs = new URLSearchParams()
        if (agentFilter !== "all") qs.set("agent_id", agentFilter)
        const res = await fetch(`/api/proxy/v1/affiliate/all-reports?${qs}`, { credentials: "include" })
        if (!res.ok) {
          const d = await res.json().catch(() => ({}))
          setError(d.detail || "Failed to load reports")
          return
        }
        setData(await res.json())
      } catch {
        setError("Network error — please try again")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [agentFilter])

  const allReports = data?.reports ?? []
  const agents = data?.agents ?? []
  const metrics = data?.metrics

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return allReports.filter((r) => {
      if (q && !r.agent_name.toLowerCase().includes(q) &&
        !formatReportType(r.report_type).toLowerCase().includes(q) &&
        !(r.city?.toLowerCase().includes(q))) return false
      if (typeFilter !== "all" && r.report_type !== typeFilter) return false
      if (statusFilter !== "all" && r.status !== statusFilter) return false
      return true
    })
  }, [allReports, search, typeFilter, statusFilter])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const pageRows = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const reportTypes = useMemo(() => [...new Set(allReports.map((r) => r.report_type))], [allReports])

  if (error) {
    return (
      <div className="max-w-3xl mx-auto py-16 text-center space-y-3">
        <AlertCircle className="w-8 h-8 text-red-500 mx-auto" />
        <p className="text-sm text-muted-foreground">{error}</p>
        <Button asChild variant="outline"><Link href="/app/affiliate">← My Agents</Link></Button>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Agent Reports"
        description="Reports generated by your agents"
      />

      {/* Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard label="Total (30d)" value={metrics?.total_30d ?? allReports.length} loading={loading} />
        <MetricCard label="Complete" value={metrics?.complete ?? allReports.filter(r => r.status === "complete").length} loading={loading} />
        <MetricCard label="Failed" value={metrics?.failed ?? allReports.filter(r => r.status === "failed").length} loading={loading} />
        <MetricCard label="Generating" value={metrics?.generating ?? allReports.filter(r => r.status === "generating" || r.status === "pending").length} loading={loading} />
      </div>

      {/* Filter bar + table */}
      <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
        <div className="p-4 border-b border-border bg-muted/30">
          <div className="flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-[180px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search by agent, type, or city…"
                className="pl-9 h-9 text-sm"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(0) }}
              />
            </div>

            {agents.length > 0 && (
              <Select value={agentFilter} onValueChange={(v) => { setAgentFilter(v); setPage(0) }}>
                <SelectTrigger className="w-[170px] h-9 text-sm">
                  <SelectValue placeholder="All Agents" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Agents</SelectItem>
                  {agents.map((a) => <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>)}
                </SelectContent>
              </Select>
            )}

            <Select value={typeFilter} onValueChange={(v) => { setTypeFilter(v); setPage(0) }}>
              <SelectTrigger className="w-[180px] h-9 text-sm">
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {reportTypes.map((t) => <SelectItem key={t} value={t}>{formatReportType(t)}</SelectItem>)}
              </SelectContent>
            </Select>

            <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(0) }}>
              <SelectTrigger className="w-[140px] h-9 text-sm">
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="complete">Complete</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="generating">Generating</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {loading ? <TableSkeleton /> : filtered.length === 0 ? (
          <div className="text-center py-14 px-4">
            <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto mb-3">
              <FileText className="w-5 h-5 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-foreground">No reports found</p>
            <p className="text-xs text-muted-foreground mt-1">
              {allReports.length === 0
                ? "Your agents haven't generated any reports yet."
                : "Try adjusting your filters."}
            </p>
          </div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40">
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Agent</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Report Type</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Area</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Status</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Generated</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Type</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">PDF</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pageRows.map((report) => (
                  <TableRow key={report.id} className="hover:bg-muted/30">
                    <TableCell className="py-3">
                      <Link
                        href={`/app/affiliate/agents/${report.agent_id}`}
                        className="font-medium text-sm text-foreground hover:text-primary hover:underline"
                      >
                        {report.agent_name}
                      </Link>
                    </TableCell>
                    <TableCell className="text-sm">{formatReportType(report.report_type)}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatArea(report.city, report.zip_codes)}</TableCell>
                    <TableCell><StatusBadge status={report.status} /></TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatRelativeTime(report.created_at)}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={report.is_scheduled
                          ? "bg-indigo-50 text-indigo-700 border-indigo-200 text-[11px] gap-1"
                          : "bg-muted text-muted-foreground text-[11px] gap-1"}
                      >
                        {report.is_scheduled
                          ? <><Calendar className="w-3 h-3" />Scheduled</>
                          : <><Zap className="w-3 h-3" />Manual</>}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {report.pdf_url ? (
                        <a href={report.pdf_url} target="_blank" rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:underline">
                          <Download className="w-3.5 h-3.5" />Download
                        </a>
                      ) : <span className="text-xs text-muted-foreground">—</span>}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-border">
                <p className="text-xs text-muted-foreground">
                  {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, filtered.length)} of {filtered.length}
                </p>
                <div className="flex gap-1">
                  <Button variant="outline" size="sm" onClick={() => setPage(p => p - 1)} disabled={page === 0}>
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page >= totalPages - 1}>
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
