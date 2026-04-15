'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowLeft,
  FileText,
  Calendar,
  Download,
  AlertCircle,
  Loader2,
  CheckCircle2,
  Clock,
  XCircle,
  Zap,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

// ─── Types ──────────────────────────────────────────────────────────────────

interface AgentUsage {
  agent: {
    id: string
    name: string
    email: string
    phone?: string | null
    status: 'active' | 'pending' | 'deactivated'
    plan_slug: string
  }
  limits: {
    market_reports: { used: number; limit: number }
    schedules: { used: number; limit: number }
    property_reports: { used: number; limit: number }
  }
}

interface AgentReport {
  id: string
  report_type: string
  city: string | null
  zip_codes: string[] | null
  status: 'complete' | 'failed' | 'generating' | 'pending'
  created_at: string
  pdf_url: string | null
  is_scheduled: boolean
}

interface AgentSchedule {
  id: string
  name: string
  report_type: string
  city: string | null
  zip_codes: string[] | null
  cadence: 'daily' | 'weekly' | 'monthly'
  send_hour: number
  send_minute: number
  timezone: string
  active: boolean
  run_count: number
  next_run_at: string | null
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatRelativeTime(dateStr: string | null): string {
  if (!dateStr) return '—'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days} days ago`
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function formatNextRun(dateStr: string | null): string {
  if (!dateStr) return '—'
  const diff = new Date(dateStr).getTime() - Date.now()
  if (diff < 0) return 'Overdue'
  const mins = Math.floor(diff / 60_000)
  if (mins < 60) return `In ${mins}m`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `In ${hrs}h`
  const days = Math.floor(hrs / 24)
  return `In ${days} day${days !== 1 ? 's' : ''}`
}

function formatTime12h(hour: number, minute: number): string {
  const ampm = hour >= 12 ? 'PM' : 'AM'
  const h = hour % 12 || 12
  const m = minute.toString().padStart(2, '0')
  return `${h}:${m} ${ampm}`
}

function formatReportType(slug: string): string {
  return slug
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatArea(city: string | null, zips: string[] | null): string {
  if (city) return city
  if (zips && zips.length > 0) {
    return zips.length === 1 ? zips[0] : `${zips[0]} +${zips.length - 1}`
  }
  return '—'
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function UsageBar({ label, used, limit }: { label: string; used: number; limit: number }) {
  const isUnlimited = limit >= 99999
  const pct = isUnlimited ? 0 : Math.min((used / Math.max(limit, 1)) * 100, 100)
  const color = pct >= 100 ? 'bg-red-500' : pct >= 80 ? 'bg-amber-500' : 'bg-indigo-500'

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[12px]">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium tabular-nums">
          {isUnlimited ? `${used} / ∞` : `${used} / ${limit}`}
        </span>
      </div>
      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${isUnlimited ? 'bg-indigo-200' : color}`}
          style={{ width: isUnlimited ? '20%' : `${pct}%` }}
        />
      </div>
    </div>
  )
}

function ReportStatusBadge({ status }: { status: AgentReport['status'] }) {
  switch (status) {
    case 'complete':
      return (
        <Badge className="bg-green-50 text-green-700 border-green-200 gap-1">
          <CheckCircle2 className="w-3 h-3" />
          Complete
        </Badge>
      )
    case 'failed':
      return (
        <Badge className="bg-red-50 text-red-700 border-red-200 gap-1">
          <XCircle className="w-3 h-3" />
          Failed
        </Badge>
      )
    case 'generating':
    case 'pending':
      return (
        <Badge className="bg-amber-50 text-amber-700 border-amber-200 gap-1">
          <Clock className="w-3 h-3" />
          Generating
        </Badge>
      )
  }
}

function AgentStatusBadge({ status }: { status: string }) {
  if (status === 'active') {
    return (
      <Badge className="bg-green-50 text-green-700 border-green-200">Active</Badge>
    )
  }
  if (status === 'pending') {
    return (
      <Badge className="bg-yellow-50 text-yellow-800 border-yellow-200">Pending</Badge>
    )
  }
  return (
    <Badge className="bg-gray-100 text-gray-600 border-gray-200">Deactivated</Badge>
  )
}

// ─── Skeleton loaders ────────────────────────────────────────────────────────

function HeaderSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-4 w-24" />
      <div className="flex items-center gap-3">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <Skeleton className="h-4 w-40" />
    </div>
  )
}

function UsageSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <Skeleton className="h-4 w-24" />
      </CardHeader>
      <CardContent className="space-y-4">
        <Skeleton className="h-6 w-full" />
        <Skeleton className="h-6 w-full" />
        <Skeleton className="h-6 w-full" />
      </CardContent>
    </Card>
  )
}

function TableSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-2 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  )
}

// ─── Main page ───────────────────────────────────────────────────────────────

export default function AgentDetailPage() {
  const params = useParams()
  const agentId = params.agentId as string

  const [usage, setUsage] = useState<AgentUsage | null>(null)
  const [usageLoading, setUsageLoading] = useState(true)
  const [usageError, setUsageError] = useState<string | null>(null)

  const [reports, setReports] = useState<AgentReport[]>([])
  const [reportsLoading, setReportsLoading] = useState(true)

  const [schedules, setSchedules] = useState<AgentSchedule[]>([])
  const [schedulesLoading, setSchedulesLoading] = useState(false)
  const [schedulesLoaded, setSchedulesLoaded] = useState(false)

  useEffect(() => {
    async function fetchUsage() {
      try {
        const res = await fetch(`/api/proxy/v1/affiliate/agents/${agentId}/usage`, {
          credentials: 'include',
        })
        if (!res.ok) {
          const d = await res.json().catch(() => ({}))
          setUsageError(
            res.status === 403
              ? "You don't have access to this agent's data."
              : d.detail || 'Failed to load agent data'
          )
          return
        }
        setUsage(await res.json())
      } catch {
        setUsageError('Network error — please try again')
      } finally {
        setUsageLoading(false)
      }
    }

    async function fetchReports() {
      try {
        const res = await fetch(`/api/proxy/v1/affiliate/agents/${agentId}/reports`, {
          credentials: 'include',
        })
        if (res.ok) {
          const d = await res.json()
          setReports(d.reports ?? d ?? [])
        }
      } catch {
        // non-critical
      } finally {
        setReportsLoading(false)
      }
    }

    fetchUsage()
    fetchReports()
  }, [agentId])

  async function loadSchedules() {
    if (schedulesLoaded) return
    setSchedulesLoading(true)
    try {
      const res = await fetch(`/api/proxy/v1/affiliate/agents/${agentId}/schedules`, {
        credentials: 'include',
      })
      if (res.ok) {
        const d = await res.json()
        setSchedules(d.schedules ?? d ?? [])
      }
    } catch {
      // non-critical
    } finally {
      setSchedulesLoading(false)
      setSchedulesLoaded(true)
    }
  }

  if (usageError) {
    return (
      <div className="max-w-3xl mx-auto py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6 text-red-500" />
        </div>
        <h2 className="text-lg font-semibold">Access Denied</h2>
        <p className="text-sm text-muted-foreground">{usageError}</p>
        <Button asChild variant="outline">
          <Link href="/app/affiliate">← Back to My Agents</Link>
        </Button>
      </div>
    )
  }

  const agent = usage?.agent

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Back link + header */}
      <div>
        <Link
          href="/app/affiliate"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-3"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          My Agents
        </Link>

        {usageLoading ? (
          <HeaderSkeleton />
        ) : (
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-foreground">{agent?.name}</h1>
              {agent?.status && <AgentStatusBadge status={agent.status} />}
            </div>
            <div className="flex items-center gap-3 text-sm text-muted-foreground flex-wrap">
              {agent?.email && <span>{agent.email}</span>}
              {agent?.phone && <span>· {agent.phone}</span>}
            </div>
          </div>
        )}
      </div>

      {/* Usage card */}
      {usageLoading ? (
        <UsageSkeleton />
      ) : usage?.limits ? (
        <Card className="border-border shadow-[var(--shadow-card)]">
          <div className="px-5 py-3 border-b border-border bg-muted/30">
            <h3 className="text-sm font-semibold text-foreground">Plan Usage</h3>
          </div>
          <CardContent className="p-5 space-y-3">
            <UsageBar
              label="Market Reports"
              used={usage.limits.market_reports.used}
              limit={usage.limits.market_reports.limit}
            />
            <UsageBar
              label="Schedules"
              used={usage.limits.schedules.used}
              limit={usage.limits.schedules.limit}
            />
            <UsageBar
              label="Property Reports"
              used={usage.limits.property_reports.used}
              limit={usage.limits.property_reports.limit}
            />
          </CardContent>
        </Card>
      ) : null}

      {/* Tabs */}
      <Tabs defaultValue="reports" onValueChange={(v) => v === 'schedules' && loadSchedules()}>
        <TabsList className="w-full sm:w-auto">
          <TabsTrigger value="reports" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Reports
          </TabsTrigger>
          <TabsTrigger value="schedules" className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Schedules
          </TabsTrigger>
        </TabsList>

        {/* Reports tab */}
        <TabsContent value="reports" className="mt-4">
          <Card className="border-border shadow-[var(--shadow-card)]">
            <div className="px-5 py-3 border-b border-border bg-muted/30">
              <h3 className="text-sm font-semibold text-foreground">Reports</h3>
            </div>
            {reportsLoading ? (
              <TableSkeleton rows={5} />
            ) : reports.length === 0 ? (
              <div className="text-center py-14 px-4">
                <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto mb-3">
                  <FileText className="w-5 h-5 text-muted-foreground" />
                </div>
                <p className="text-sm font-medium text-foreground">No reports generated yet</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Reports will appear here once the agent generates them.
                </p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/40">
                    <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Report Type</TableHead>
                    <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Area</TableHead>
                    <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Status</TableHead>
                    <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Generated</TableHead>
                    <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">Type</TableHead>
                    <TableHead className="text-[11px] font-semibold uppercase tracking-[0.05em]">PDF</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reports.map((report) => (
                    <TableRow key={report.id} className="hover:bg-muted/30">
                      <TableCell className="font-medium text-sm">
                        {formatReportType(report.report_type)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatArea(report.city, report.zip_codes)}
                      </TableCell>
                      <TableCell>
                        <ReportStatusBadge status={report.status} />
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatRelativeTime(report.created_at)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={report.is_scheduled
                            ? 'bg-indigo-50 text-indigo-700 border-indigo-200 text-[11px] gap-1'
                            : 'bg-muted text-muted-foreground text-[11px]'}
                        >
                          {report.is_scheduled ? (
                            <><Calendar className="w-3 h-3" />Scheduled</>
                          ) : (
                            <><Zap className="w-3 h-3" />Manual</>
                          )}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {report.pdf_url ? (
                          <a
                            href={report.pdf_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 hover:underline"
                          >
                            <Download className="w-3.5 h-3.5" />
                            Download
                          </a>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        </TabsContent>

        {/* Schedules tab */}
        <TabsContent value="schedules" className="mt-4">
          <Card className="border-border shadow-[var(--shadow-card)]">
            <div className="px-5 py-3 border-b border-border bg-muted/30">
              <h3 className="text-sm font-semibold text-foreground">Schedules</h3>
            </div>
            {schedulesLoading ? (
              <TableSkeleton rows={3} />
            ) : !schedulesLoaded ? (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
              </div>
            ) : schedules.length === 0 ? (
              <div className="text-center py-14 px-4">
                <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto mb-3">
                  <Calendar className="w-5 h-5 text-muted-foreground" />
                </div>
                <p className="text-sm font-medium text-foreground">No schedules created yet</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Schedules will appear here once the agent sets up automated reports.
                </p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/40">
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
                  {schedules.map((schedule) => (
                    <TableRow key={schedule.id} className="hover:bg-muted/30">
                      <TableCell className="font-medium text-sm">{schedule.name}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatReportType(schedule.report_type)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatArea(schedule.city, schedule.zip_codes)}
                      </TableCell>
                      <TableCell className="text-sm capitalize">{schedule.cadence}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatTime12h(schedule.send_hour, schedule.send_minute)}
                      </TableCell>
                      <TableCell>
                        {schedule.active ? (
                          <Badge className="bg-green-50 text-green-700 border-green-200 text-[11px]">Active</Badge>
                        ) : (
                          <Badge className="bg-gray-100 text-gray-600 border-gray-200 text-[11px]">Paused</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right font-medium text-sm">
                        {schedule.run_count}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatNextRun(schedule.next_run_at)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
