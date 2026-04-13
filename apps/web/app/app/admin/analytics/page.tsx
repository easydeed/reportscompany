"use client"

import { useEffect, useState, useCallback } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  ArrowLeft,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Eye,
  FileText,
  Users,
  Phone,
  Download,
  Clock,
  Monitor,
  Smartphone,
  Tablet,
  Globe,
  CheckCircle,
  XCircle,
  Activity,
} from "lucide-react"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"

// ── Types ──────────────────────────────────────────

interface Overview {
  total_reports: number
  total_views: number
  total_pdfs: number
  total_contacts: number
  pdf_rate_pct: number
  contact_rate_pct: number
  reports_today: number
  views_today: number
  contacts_today: number
  reports_this_week: number
  reports_this_month: number
  reports_trend_pct: number
  contacts_trend_pct: number
}

interface DailyMetric {
  date: string
  reports_requested: number
  reports_ready: number
  reports_failed: number
  pdfs_generated: number
  agent_contacts: number
  total_views: number
  unique_agents: number
}

interface Agent {
  agent_id: string
  agent_name: string
  agent_email: string
  account_name: string
  total_reports: number
  reports_30d: number
  total_views: number
  contacts: number
  contact_rate_pct: number
  pdfs_downloaded: number
}

interface HourlyBucket {
  hour: number
  report_count: number
  pdf_count: number
}

interface DeviceStat {
  device_type: string
  count: number
  percentage: number
}

interface FunnelStage {
  stage: string
  count: number
  pct: number
}

interface RecentItem {
  id: string
  agent_name: string
  property_address: string
  status: string
  view_count: number
  agent_contacted: boolean
  has_pdf: boolean
  created_at: string
}

// ── Helpers ────────────────────────────────────────

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

function formatHour(hour: number): string {
  if (hour === 0) return "12 AM"
  if (hour < 12) return `${hour} AM`
  if (hour === 12) return "12 PM"
  return `${hour - 12} PM`
}

function TrendBadge({ value }: { value: number }) {
  if (value === 0) return null
  const positive = value > 0
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs font-medium ${positive ? "text-green-600" : "text-red-600"}`}>
      {positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
      {positive ? "+" : ""}{value}%
    </span>
  )
}

const DEVICE_ICONS: Record<string, React.ReactNode> = {
  desktop: <Monitor className="h-5 w-5" />,
  mobile: <Smartphone className="h-5 w-5" />,
  tablet: <Tablet className="h-5 w-5" />,
}

const STATUS_STYLES: Record<string, string> = {
  ready: "text-green-600 border-green-200 bg-green-50",
  pending: "text-yellow-600 border-yellow-200 bg-yellow-50",
  failed: "text-red-600 border-red-200 bg-red-50",
}

// ── Component ──────────────────────────────────────

export default function AdminAnalyticsPage() {
  const [loading, setLoading] = useState(true)
  const [overview, setOverview] = useState<Overview | null>(null)
  const [daily, setDaily] = useState<DailyMetric[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [hourly, setHourly] = useState<HourlyBucket[]>([])
  const [devices, setDevices] = useState<DeviceStat[]>([])
  const [funnel, setFunnel] = useState<FunnelStage[]>([])
  const [recent, setRecent] = useState<RecentItem[]>([])

  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      const [ovRes, dyRes, agRes, hrRes, dvRes, fnRes, rcRes] = await Promise.all([
        fetch("/api/proxy/v1/admin/metrics/overview", { credentials: "include" }),
        fetch("/api/proxy/v1/admin/metrics/daily?days=30", { credentials: "include" }),
        fetch("/api/proxy/v1/admin/metrics/agents?limit=10", { credentials: "include" }),
        fetch("/api/proxy/v1/admin/metrics/hourly", { credentials: "include" }),
        fetch("/api/proxy/v1/admin/metrics/devices", { credentials: "include" }),
        fetch("/api/proxy/v1/admin/metrics/conversion-funnel", { credentials: "include" }),
        fetch("/api/proxy/v1/admin/metrics/recent?limit=15", { credentials: "include" }),
      ])

      if (ovRes.ok) setOverview(await ovRes.json())
      if (dyRes.ok) {
        const d = await dyRes.json()
        setDaily((Array.isArray(d) ? d : []).reverse())
      }
      if (agRes.ok) {
        const a = await agRes.json()
        setAgents(Array.isArray(a) ? a : [])
      }
      if (hrRes.ok) {
        const h = await hrRes.json()
        setHourly(Array.isArray(h) ? h : [])
      }
      if (dvRes.ok) {
        const dv = await dvRes.json()
        setDevices(Array.isArray(dv) ? dv : [])
      }
      if (fnRes.ok) {
        const fn = await fnRes.json()
        setFunnel(fn?.funnel || [])
      }
      if (rcRes.ok) {
        const rc = await rcRes.json()
        setRecent(Array.isArray(rc) ? rc : [])
      }
    } catch (err) {
      console.error("Failed to fetch analytics:", err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded" />
          <div>
            <Skeleton className="h-9 w-48 mb-2" />
            <Skeleton className="h-5 w-72" />
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-10 w-20" /></CardContent></Card>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card><CardContent className="pt-6"><Skeleton className="h-64 w-full" /></CardContent></Card>
          <Card><CardContent className="pt-6"><Skeleton className="h-64 w-full" /></CardContent></Card>
        </div>
      </div>
    )
  }

  const ov = overview || {} as Overview

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/app/admin">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">CMA Analytics</h1>
          <p className="text-muted-foreground mt-1">Lead page performance across all accounts</p>
        </div>
      </div>

      {/* ── KPI Cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{ov.total_reports?.toLocaleString()}</div>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-muted-foreground">{ov.reports_this_month} this month</span>
              <TrendBadge value={ov.reports_trend_pct} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Views</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{ov.total_views?.toLocaleString()}</div>
            <span className="text-xs text-muted-foreground">{ov.views_today} today</span>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">PDF Rate</CardTitle>
            <Download className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{ov.pdf_rate_pct}%</div>
            <span className="text-xs text-muted-foreground">{ov.total_pdfs?.toLocaleString()} PDFs total</span>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Contact Rate</CardTitle>
            <Phone className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{ov.contact_rate_pct}%</div>
            <span className="text-xs text-muted-foreground">{ov.total_contacts?.toLocaleString()} contacts</span>
          </CardContent>
        </Card>
      </div>

      {/* ── Second row KPIs ── */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Today</p>
                <p className="text-xl font-bold">{ov.reports_today}</p>
              </div>
              <Activity className="h-5 w-5 text-indigo-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">This Week</p>
                <p className="text-xl font-bold">{ov.reports_this_week}</p>
              </div>
              <BarChart3 className="h-5 w-5 text-indigo-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Contacts Today</p>
                <p className="text-xl font-bold">{ov.contacts_today}</p>
              </div>
              <Phone className="h-5 w-5 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Charts Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Line Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Daily CMA Reports (30 days)</CardTitle>
          </CardHeader>
          <CardContent>
            {daily.length === 0 ? (
              <p className="text-muted-foreground text-center py-12">No data yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={daily}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(v: string) => {
                      const d = new Date(v)
                      return `${d.getMonth() + 1}/${d.getDate()}`
                    }}
                  />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ fontSize: 12, borderRadius: 8 }}
                    labelFormatter={(v: string) => new Date(v).toLocaleDateString()}
                  />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line type="monotone" dataKey="reports_requested" name="Requested" stroke="#6366f1" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="reports_ready" name="Ready" stroke="#22c55e" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="agent_contacts" name="Contacts" stroke="#f59e0b" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Hourly Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Hourly Distribution (30 days)</CardTitle>
            <CardDescription>Peak hours for CMA report requests</CardDescription>
          </CardHeader>
          <CardContent>
            {hourly.length === 0 ? (
              <p className="text-muted-foreground text-center py-12">No data yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={hourly}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="hour" tick={{ fontSize: 11 }} tickFormatter={formatHour} />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ fontSize: 12, borderRadius: 8 }}
                    labelFormatter={(v: number) => formatHour(v)}
                  />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="report_count" name="Reports" fill="#6366f1" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="pdf_count" name="PDFs" fill="#a5b4fc" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Funnel + Devices ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Conversion Funnel */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Conversion Funnel (30 days)</CardTitle>
          </CardHeader>
          <CardContent>
            {funnel.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">No data yet</p>
            ) : (
              <div className="space-y-3">
                {funnel.map((stage, i) => {
                  const barWidth = Math.max(stage.pct, 3)
                  const isFirst = i === 0
                  const isLast = i === funnel.length - 1
                  return (
                    <div key={stage.stage} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className={isFirst ? "font-semibold" : isLast ? "font-semibold text-green-600" : ""}>
                          {stage.stage}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs text-muted-foreground">
                            {stage.count.toLocaleString()}
                          </span>
                          <Badge variant="outline" className={`text-xs ${stage.pct >= 50 ? "text-green-600" : stage.pct >= 20 ? "text-yellow-600" : "text-red-600"}`}>
                            {stage.pct}%
                          </Badge>
                        </div>
                      </div>
                      <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${isLast ? "bg-green-500" : "bg-indigo-500"}`}
                          style={{ width: `${barWidth}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Device Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Devices</CardTitle>
          </CardHeader>
          <CardContent>
            {devices.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">No data yet</p>
            ) : (
              <div className="space-y-4">
                {devices.map((d) => (
                  <div key={d.device_type} className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center text-muted-foreground">
                      {DEVICE_ICONS[d.device_type.toLowerCase()] || <Globe className="h-5 w-5" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium capitalize">{d.device_type}</span>
                        <span className="text-sm font-bold">{d.percentage}%</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-indigo-500"
                          style={{ width: `${d.percentage}%` }}
                        />
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">{d.count.toLocaleString()} reports</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Agent Leaderboard ── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Agent Leaderboard (Top 10)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {agents.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No agents with reports yet</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-[11px] uppercase tracking-wider w-8">#</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Agent</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Account</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider text-right">Total</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider text-right">30d</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider text-right">Views</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider text-right">Contacts</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider text-right">Contact %</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider text-right">PDFs</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {agents.map((agent, idx) => (
                  <TableRow key={agent.agent_id}>
                    <TableCell className="font-medium text-muted-foreground">{idx + 1}</TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium text-sm">{agent.agent_name || "—"}</p>
                        <p className="text-xs text-muted-foreground">{agent.agent_email}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{agent.account_name}</TableCell>
                    <TableCell className="text-right font-medium">{agent.total_reports}</TableCell>
                    <TableCell className="text-right text-muted-foreground">{agent.reports_30d}</TableCell>
                    <TableCell className="text-right text-muted-foreground">{agent.total_views.toLocaleString()}</TableCell>
                    <TableCell className="text-right text-muted-foreground">{agent.contacts}</TableCell>
                    <TableCell className="text-right">
                      <Badge variant="outline" className={`text-xs ${agent.contact_rate_pct >= 20 ? "text-green-600 border-green-200 bg-green-50" : ""}`}>
                        {agent.contact_rate_pct}%
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">{agent.pdfs_downloaded}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* ── Recent Activity ── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          {recent.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No recent activity</p>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
              {recent.map((item) => (
                <div key={item.id} className="flex items-start gap-3 p-3 rounded-lg border hover:bg-muted/30 transition-colors">
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    item.status === "ready" ? "bg-green-100 text-green-600" :
                    item.status === "failed" ? "bg-red-100 text-red-600" :
                    "bg-yellow-100 text-yellow-600"
                  }`}>
                    <FileText className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium">{item.agent_name || "Unknown"}</span>
                      <Badge variant="outline" className={`text-xs ${STATUS_STYLES[item.status] || ""}`}>
                        {item.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground truncate">{item.property_address || "No address"}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Eye className="h-3 w-3" />
                        {item.view_count}
                      </span>
                      {item.has_pdf && (
                        <span className="flex items-center gap-1 text-xs text-green-600">
                          <Download className="h-3 w-3" />
                          PDF
                        </span>
                      )}
                      {item.agent_contacted && (
                        <span className="flex items-center gap-1 text-xs text-indigo-600">
                          <Phone className="h-3 w-3" />
                          Contacted
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap flex-shrink-0">
                    {formatTimeAgo(item.created_at)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
