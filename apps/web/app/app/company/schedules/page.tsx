"use client"

import { useState, useEffect, useMemo } from "react"
import Link from "next/link"
import {
  Search, Calendar, AlertCircle, ChevronLeft, ChevronRight, Users, CheckCircle2,
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

interface ScheduleRow {
  id: string
  user_name: string
  user_type: "rep" | "agent"
  rep_name?: string
  name: string
  report_type: string
  city: string | null
  zip_codes: string[] | null
  cadence: "daily" | "weekly" | "monthly"
  send_hour: number
  send_minute: number
  timezone: string
  active: boolean
  run_count: number
  next_run_at: string | null
}

interface Rep {
  id: string
  name: string
}

interface SchedulesResponse {
  schedules: ScheduleRow[]
  total: number
  reps?: Rep[]
  metrics?: { total: number; active: number; paused: number; by_reps: number; by_agents: number }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatTime12h(hour: number, minute: number): string {
  const ampm = hour >= 12 ? "PM" : "AM"
  const h = hour % 12 || 12
  const m = minute.toString().padStart(2, "0")
  return `${h}:${m} ${ampm}`
}

function formatNextRun(dateStr: string | null): string {
  if (!dateStr) return "—"
  const diff = new Date(dateStr).getTime() - Date.now()
  if (diff < 0) return "Overdue"
  const mins = Math.floor(diff / 60_000)
  if (mins < 60) return `In ${mins}m`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `In ${hrs}h`
  const days = Math.floor(hrs / 24)
  return `In ${days} day${days !== 1 ? "s" : ""}`
}

function formatReportType(slug: string): string {
  return slug.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatArea(city: string | null, zips: string[] | null): string {
  if (city) return city
  if (zips && zips.length > 0) return zips.length === 1 ? zips[0] : `${zips[0]} +${zips.length - 1}`
  return "—"
}

function UserTypeBadge({ type }: { type: "rep" | "agent" }) {
  if (type === "rep")
    return <Badge variant="outline" className="bg-indigo-50 text-indigo-700 border-indigo-200 text-[10px] ml-1.5">Rep</Badge>
  return <Badge variant="outline" className="bg-slate-50 text-slate-600 border-slate-200 text-[10px] ml-1.5">Agent</Badge>
}

function MetricCard({ label, value, icon: Icon, loading }: {
  label: string; value: number; icon: React.ElementType; loading: boolean
}) {
  return (
    <div className="bg-card border border-border rounded-xl p-4 shadow-[var(--shadow-card)]">
      <div className="flex items-center justify-between mb-2">
        <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-[0.05em]">{label}</p>
        <div className="rounded-lg bg-muted p-1.5"><Icon className="w-3.5 h-3.5 text-muted-foreground" /></div>
      </div>
      {loading ? <Skeleton className="h-7 w-16" /> : (
        <p className="text-2xl font-bold text-foreground">{value.toLocaleString()}</p>
      )}
    </div>
  )
}

function TableSkeleton() {
  return (
    <div className="p-4 space-y-2">
      {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-11 w-full" />)}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 25

export default function CompanySchedulesPage() {
  const [data, setData] = useState<SchedulesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState("")
  const [repFilter, setRepFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")
  const [typeFilter, setTypeFilter] = useState("all")
  const [page, setPage] = useState(0)

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const qs = new URLSearchParams()
        if (repFilter !== "all") qs.set("rep_id", repFilter)
        const res = await fetch(`/api/proxy/v1/company/schedules?${qs}`, { credentials: "include" })
        if (!res.ok) {
          const d = await res.json().catch(() => ({}))
          setError(d.detail || "Failed to load schedules")
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
  }, [repFilter])

  const allSchedules = data?.schedules ?? []
  const reps = data?.reps ?? []
  const metrics = data?.metrics

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return allSchedules.filter((s) => {
      if (q && !s.user_name.toLowerCase().includes(q) &&
        !s.name.toLowerCase().includes(q) &&
        !(s.city?.toLowerCase().includes(q))) return false
      if (statusFilter === "active" && !s.active) return false
      if (statusFilter === "paused" && s.active) return false
      if (typeFilter !== "all" && s.report_type !== typeFilter) return false
      return true
    })
  }, [allSchedules, search, statusFilter, typeFilter])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const pageRows = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const reportTypes = useMemo(() => [...new Set(allSchedules.map((s) => s.report_type))], [allSchedules])

  const activeCount = allSchedules.filter((s) => s.active).length

  if (error) {
    return (
      <div className="max-w-3xl mx-auto py-16 text-center space-y-3">
        <AlertCircle className="w-8 h-8 text-red-500 mx-auto" />
        <p className="text-sm text-muted-foreground">{error}</p>
        <Button asChild variant="outline"><Link href="/app/company">← Back</Link></Button>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="All Schedules"
        description="Automated report schedules across your team"
      />

      {/* Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard label="Total Schedules" value={metrics?.total ?? allSchedules.length} icon={Calendar} loading={loading} />
        <MetricCard label="Active" value={metrics?.active ?? activeCount} icon={CheckCircle2} loading={loading} />
        <MetricCard label="By Reps" value={metrics?.by_reps ?? allSchedules.filter(s => s.user_type === "rep").length} icon={Users} loading={loading} />
        <MetricCard label="By Agents" value={metrics?.by_agents ?? allSchedules.filter(s => s.user_type === "agent").length} icon={Users} loading={loading} />
      </div>

      {/* Filter bar + table */}
      <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
        <div className="p-4 border-b border-border bg-muted/30">
          <div className="flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-[180px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search schedules…"
                className="pl-9 h-9 text-sm"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(0) }}
              />
            </div>

            {reps.length > 0 && (
              <Select value={repFilter} onValueChange={(v) => { setRepFilter(v); setPage(0) }}>
                <SelectTrigger className="w-[160px] h-9 text-sm">
                  <SelectValue placeholder="All Reps" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Reps</SelectItem>
                  {reps.map((r) => <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>)}
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
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {loading ? <TableSkeleton /> : filtered.length === 0 ? (
          <div className="text-center py-14 px-4">
            <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto mb-3">
              <Calendar className="w-5 h-5 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-foreground">No schedules found</p>
            <p className="text-xs text-muted-foreground mt-1">Try adjusting your filters.</p>
          </div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40">
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">User</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Schedule Name</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Report Type</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Area</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Cadence</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Time</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Status</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em] text-right">Runs</TableHead>
                  <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Next Run</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pageRows.map((s) => (
                  <TableRow key={s.id} className="hover:bg-muted/30">
                    <TableCell className="py-3">
                      <div className="flex items-center gap-1">
                        <span className="font-medium text-sm text-foreground">{s.user_name}</span>
                        <UserTypeBadge type={s.user_type} />
                      </div>
                      {s.user_type === "agent" && s.rep_name && (
                        <p className="text-xs text-muted-foreground mt-0.5">via {s.rep_name}</p>
                      )}
                    </TableCell>
                    <TableCell className="text-sm font-medium">{s.name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatReportType(s.report_type)}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatArea(s.city, s.zip_codes)}</TableCell>
                    <TableCell className="text-sm capitalize">{s.cadence}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatTime12h(s.send_hour, s.send_minute)}</TableCell>
                    <TableCell>
                      {s.active
                        ? <Badge className="bg-green-50 text-green-700 border-green-200 text-[11px]">Active</Badge>
                        : <Badge className="bg-gray-100 text-gray-600 border-gray-200 text-[11px]">Paused</Badge>}
                    </TableCell>
                    <TableCell className="text-right text-sm font-medium">{s.run_count}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatNextRun(s.next_run_at)}</TableCell>
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
