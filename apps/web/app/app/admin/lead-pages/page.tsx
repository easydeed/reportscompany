"use client"

import { useEffect, useState, useMemo, useCallback } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
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
  ExternalLink,
  Search,
  X,
  Users,
  TrendingUp,
  CalendarDays,
  ToggleLeft,
  ToggleRight,
  Loader2,
  Link2,
  FileText,
  Eye,
  Phone,
  Download,
  BarChart3,
  Monitor,
  Smartphone,
  Tablet,
  RefreshCw,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts"

// ────────────────────────────────────────
// Types
// ────────────────────────────────────────

interface LeadPage {
  user_id: string
  agent_code: string
  agent_name: string
  email: string
  account_id: string
  account_name: string
  enabled: boolean
  landing_page_headline: string | null
  landing_page_theme_color: string | null
  visits: number
  created_at: string
  total_leads: number
  last_lead_at: string | null
  leads_this_month: number
}

interface Stats {
  active_pages: number
  total_leads: number
  leads_this_month: number
}

// ────────────────────────────────────────
// Helpers
// ────────────────────────────────────────

function formatTimeAgo(dateString: string | null): string {
  if (!dateString) return "Never"
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 30) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

const DEVICE_ICONS: Record<string, React.ReactNode> = {
  mobile: <Smartphone className="h-5 w-5" />,
  desktop: <Monitor className="h-5 w-5" />,
  tablet: <Tablet className="h-5 w-5" />,
}

const PIE_COLORS = ["#6366F1", "#EC4899", "#F59E0B", "#10B981"]

// ────────────────────────────────────────
// Main Page
// ────────────────────────────────────────

export default function AdminLeadPagesPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const currentTab = searchParams.get("tab") || "pages"

  // Management state
  const [pages, setPages] = useState<LeadPage[]>([])
  const [stats, setStats] = useState<Stats>({
    active_pages: 0,
    total_leads: 0,
    leads_this_month: 0,
  })
  const [loading, setLoading] = useState(true)
  const [togglingId, setTogglingId] = useState<string | null>(null)

  const filterStatus = searchParams.get("status") || "all"
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "")

  // Analytics state
  const [overview, setOverview] = useState<any>(null)
  const [daily, setDaily] = useState<any[]>([])
  const [agents, setAgents] = useState<any[]>([])
  const [devices, setDevices] = useState<any[]>([])
  const [funnel, setFunnel] = useState<any>(null)
  const [recent, setRecent] = useState<any[]>([])
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [analyticsLoaded, setAnalyticsLoaded] = useState(false)

  // ── Fetch management data ──
  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        const status = searchParams.get("status")
        if (status && status !== "all") params.set("status", status)
        params.set("limit", "200")

        const res = await fetch(
          `/api/proxy/v1/admin/lead-pages?${params.toString()}`,
          { credentials: "include" }
        )
        if (res.ok) {
          const data = await res.json()
          setPages(data?.lead_pages || [])
          if (data?.stats) setStats(data.stats)
        }
      } catch (err) {
        console.error("Failed to fetch lead pages:", err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [searchParams])

  // ── Fetch analytics (lazy, on first tab switch) ──
  const fetchAnalytics = useCallback(async () => {
    if (analyticsLoaded) return
    setAnalyticsLoading(true)
    try {
      const [ov, dy, ag, dv, fn, rc] = await Promise.all([
        fetch("/api/proxy/v1/admin/metrics/overview", { credentials: "include" }).then((r) => r.json()),
        fetch("/api/proxy/v1/admin/metrics/daily?days=30", { credentials: "include" }).then((r) => r.json()),
        fetch("/api/proxy/v1/admin/metrics/agents?limit=10", { credentials: "include" }).then((r) => r.json()),
        fetch("/api/proxy/v1/admin/metrics/devices", { credentials: "include" }).then((r) => r.json()),
        fetch("/api/proxy/v1/admin/metrics/conversion-funnel", { credentials: "include" }).then((r) => r.json()),
        fetch("/api/proxy/v1/admin/metrics/recent?limit=10", { credentials: "include" }).then((r) => r.json()),
      ])
      setOverview(ov)
      setDaily(Array.isArray(dy) ? [...dy].reverse() : [])
      setAgents(Array.isArray(ag) ? ag : [])
      setDevices(Array.isArray(dv) ? dv : [])
      setFunnel(fn)
      setRecent(Array.isArray(rc) ? rc : [])
      setAnalyticsLoaded(true)
    } catch (err) {
      console.error("Failed to fetch analytics:", err)
    } finally {
      setAnalyticsLoading(false)
    }
  }, [analyticsLoaded])

  function refreshAnalytics() {
    setAnalyticsLoaded(false)
    setTimeout(() => fetchAnalytics(), 0)
  }

  useEffect(() => {
    if (currentTab === "analytics" && !analyticsLoaded) {
      fetchAnalytics()
    }
  }, [currentTab, analyticsLoaded, fetchAnalytics])

  // ── Filtered pages ──
  const filteredPages = useMemo(() => {
    const q = searchParams.get("q")?.toLowerCase()
    if (!q) return pages
    return pages.filter(
      (p) =>
        p.agent_name.toLowerCase().includes(q) ||
        p.email.toLowerCase().includes(q) ||
        p.agent_code.toLowerCase().includes(q) ||
        p.account_name.toLowerCase().includes(q)
    )
  }, [pages, searchParams])

  // ── Toggle enabled ──
  async function toggleEnabled(page: LeadPage) {
    setTogglingId(page.user_id)
    try {
      const res = await fetch(
        `/api/proxy/v1/admin/lead-pages/${page.user_id}?enabled=${!page.enabled}`,
        { method: "PATCH", credentials: "include" }
      )
      if (res.ok) {
        setPages((prev) =>
          prev.map((p) =>
            p.user_id === page.user_id ? { ...p, enabled: !p.enabled } : p
          )
        )
        setStats((prev) => ({
          ...prev,
          active_pages: prev.active_pages + (page.enabled ? -1 : 1),
        }))
        toast({
          title: page.enabled ? "Lead page disabled" : "Lead page enabled",
          description: `${page.agent_name} (${page.agent_code})`,
        })
      } else {
        toast({ title: "Failed to update", variant: "destructive" })
      }
    } catch {
      toast({ title: "Failed to update", variant: "destructive" })
    } finally {
      setTogglingId(null)
    }
  }

  function updateFilter(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString())
    if (value && value !== "all") {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    params.set("tab", currentTab)
    router.push(`/app/admin/lead-pages?${params.toString()}`)
  }

  function clearFilters() {
    setSearchQuery("")
    const params = new URLSearchParams()
    params.set("tab", currentTab)
    router.push(`/app/admin/lead-pages?${params.toString()}`)
  }

  function switchTab(tab: string) {
    const params = new URLSearchParams(searchParams.toString())
    params.set("tab", tab)
    router.push(`/app/admin/lead-pages?${params.toString()}`)
  }

  const hasFilters = filterStatus !== "all" || searchParams.get("q")

  // ── Loading skeleton ──
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
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="pt-6">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="py-3 flex gap-4">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    )
  }

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
          <h1 className="text-3xl font-display font-bold text-foreground">
            CMA Lead Pages
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage lead pages and view performance analytics
          </p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={currentTab} onValueChange={switchTab}>
        <TabsList>
          <TabsTrigger value="pages" className="gap-1.5">
            <Link2 className="h-3.5 w-3.5" />
            Lead Pages
          </TabsTrigger>
          <TabsTrigger value="analytics" className="gap-1.5">
            <BarChart3 className="h-3.5 w-3.5" />
            Analytics
          </TabsTrigger>
        </TabsList>

        {/* ════════════════════════════════════════ */}
        {/* Tab 1: Lead Pages Management             */}
        {/* ════════════════════════════════════════ */}
        <TabsContent value="pages" className="space-y-6 mt-6">
          {/* Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Pages</CardTitle>
                <Link2 className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.active_pages}</div>
                <p className="text-xs text-muted-foreground">of {pages.length} total</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Leads</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_leads}</div>
                <p className="text-xs text-muted-foreground">All time</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Leads This Month</CardTitle>
                <TrendingUp className="h-4 w-4 text-indigo-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.leads_this_month}</div>
                <p className="text-xs text-muted-foreground">Current month</p>
              </CardContent>
            </Card>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 min-w-[200px] max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search agent, email, code..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) =>
                  e.key === "Enter" && updateFilter("q", searchQuery)
                }
                className="pl-9"
              />
            </div>
            <Select
              value={filterStatus}
              onValueChange={(v) => updateFilter("status", v)}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
            {hasFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="w-4 h-4 mr-1" />
                Clear
              </Button>
            )}
          </div>

          {/* Table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Link2 className="h-5 w-5" />
                Lead Pages ({filteredPages.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {filteredPages.length === 0 ? (
                <div className="text-center py-12">
                  <Link2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No lead pages found</h3>
                  <p className="text-muted-foreground">
                    {hasFilters
                      ? "No lead pages match your filters"
                      : "No agents have CMA lead pages yet"}
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-[11px] uppercase tracking-wider">Agent</TableHead>
                      <TableHead className="text-[11px] uppercase tracking-wider">Code / URL</TableHead>
                      <TableHead className="text-[11px] uppercase tracking-wider">Account</TableHead>
                      <TableHead className="text-[11px] uppercase tracking-wider">Status</TableHead>
                      <TableHead className="text-[11px] uppercase tracking-wider text-right">Visits</TableHead>
                      <TableHead className="text-[11px] uppercase tracking-wider text-right">Leads</TableHead>
                      <TableHead className="text-[11px] uppercase tracking-wider">Last Lead</TableHead>
                      <TableHead className="text-[11px] uppercase tracking-wider">Created</TableHead>
                      <TableHead className="text-[11px] uppercase tracking-wider">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredPages.map((page) => (
                      <TableRow
                        key={page.user_id}
                        className={!page.enabled ? "opacity-60" : ""}
                      >
                        <TableCell>
                          <div>
                            <p className="font-medium text-sm">{page.agent_name}</p>
                            <p className="text-xs text-muted-foreground">{page.email}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1.5">
                            <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">
                              {page.agent_code}
                            </code>
                            <a
                              href={`/cma/${page.agent_code}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-indigo-600 hover:text-indigo-800"
                            >
                              <ExternalLink className="h-3.5 w-3.5" />
                            </a>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Link
                            href={`/app/admin/accounts/${page.account_id}`}
                            className="text-sm hover:underline"
                          >
                            {page.account_name}
                          </Link>
                        </TableCell>
                        <TableCell>
                          {page.enabled ? (
                            <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">
                              Active
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50">
                              Inactive
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right font-medium text-sm">
                          {page.visits.toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <Link
                            href={`/app/admin/leads?account_id=${page.account_id}`}
                            className="font-medium text-sm text-indigo-600 hover:underline"
                          >
                            {page.total_leads}
                          </Link>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatTimeAgo(page.last_lead_at)}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatTimeAgo(page.created_at)}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0"
                              onClick={() => toggleEnabled(page)}
                              disabled={togglingId === page.user_id}
                              title={page.enabled ? "Disable page" : "Enable page"}
                            >
                              {togglingId === page.user_id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : page.enabled ? (
                                <ToggleRight className="h-4 w-4 text-green-600" />
                              ) : (
                                <ToggleLeft className="h-4 w-4 text-muted-foreground" />
                              )}
                            </Button>
                            <Link href={`/app/admin/leads?account_id=${page.account_id}`}>
                              <Button variant="ghost" size="sm" className="h-8 w-8 p-0" title="View leads">
                                <CalendarDays className="h-4 w-4" />
                              </Button>
                            </Link>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
              {filteredPages.length > 0 && (
                <p className="text-xs text-muted-foreground text-center mt-4">
                  Showing {filteredPages.length} lead page
                  {filteredPages.length !== 1 ? "s" : ""}
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ════════════════════════════════════════ */}
        {/* Tab 2: Analytics                         */}
        {/* ════════════════════════════════════════ */}
        <TabsContent value="analytics" className="space-y-6 mt-6">
          {analyticsLoading && !analyticsLoaded ? (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <Card key={i}>
                    <CardContent className="pt-6">
                      <Skeleton className="h-5 w-24 mb-2" />
                      <Skeleton className="h-8 w-16" />
                    </CardContent>
                  </Card>
                ))}
              </div>
              <div className="grid md:grid-cols-2 gap-6">
                <Card><CardContent className="pt-6"><Skeleton className="h-64 w-full" /></CardContent></Card>
                <Card><CardContent className="pt-6"><Skeleton className="h-64 w-full" /></CardContent></Card>
              </div>
              <Card><CardContent className="pt-6"><Skeleton className="h-40 w-full" /></CardContent></Card>
            </div>
          ) : (
            <>
              {/* Refresh */}
              <div className="flex justify-end">
                <Button variant="outline" size="sm" onClick={refreshAnalytics}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
              </div>

              {/* Overview KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
                    <FileText className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {overview?.total_reports?.toLocaleString() || "0"}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {overview?.reports_today || 0} today
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Views</CardTitle>
                    <Eye className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {overview?.total_views?.toLocaleString() || "0"}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {overview?.views_today || 0} today
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Agent Contacts</CardTitle>
                    <Phone className="h-4 w-4 text-indigo-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {overview?.total_contacts?.toLocaleString() || "0"}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {overview?.contact_rate_pct || 0}% conversion
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">PDFs Generated</CardTitle>
                    <Download className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {overview?.total_pdfs?.toLocaleString() || "0"}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {overview?.pdf_rate_pct || 0}% of reports
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Charts Row */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Daily Trend */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium">
                      Reports &amp; Contacts (30 Days)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      {daily.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={daily}>
                            <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                            <XAxis
                              dataKey="date"
                              tick={{ fontSize: 11 }}
                              className="text-muted-foreground"
                            />
                            <YAxis
                              tick={{ fontSize: 11 }}
                              className="text-muted-foreground"
                            />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: "hsl(var(--card))",
                                border: "1px solid hsl(var(--border))",
                                borderRadius: 8,
                                fontSize: 12,
                              }}
                            />
                            <Line
                              type="monotone"
                              dataKey="reports_requested"
                              stroke="#6366F1"
                              strokeWidth={2}
                              dot={false}
                              name="Reports"
                            />
                            <Line
                              type="monotone"
                              dataKey="agent_contacts"
                              stroke="#10B981"
                              strokeWidth={2}
                              dot={false}
                              name="Contacts"
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-full flex items-center justify-center text-muted-foreground">
                          No data yet
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Device Breakdown */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium">
                      Device Breakdown
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      {devices.length > 0 ? (
                        <div className="flex items-center h-full gap-6">
                          <div className="w-1/2 h-full">
                            <ResponsiveContainer width="100%" height="100%">
                              <PieChart>
                                <Pie
                                  data={devices}
                                  cx="50%"
                                  cy="50%"
                                  innerRadius={50}
                                  outerRadius={75}
                                  dataKey="count"
                                  nameKey="device_type"
                                >
                                  {devices.map((_, i) => (
                                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                                  ))}
                                </Pie>
                                <Tooltip
                                  contentStyle={{
                                    backgroundColor: "hsl(var(--card))",
                                    border: "1px solid hsl(var(--border))",
                                    borderRadius: 8,
                                    fontSize: 12,
                                  }}
                                />
                              </PieChart>
                            </ResponsiveContainer>
                          </div>
                          <div className="w-1/2 space-y-3">
                            {devices.map((d, i) => {
                              const total = devices.reduce((s, x) => s + (x.count || 0), 0)
                              const pct = total > 0 ? ((d.count / total) * 100).toFixed(0) : "0"
                              return (
                                <div key={i} className="flex items-center gap-3">
                                  <div
                                    className="w-3 h-3 rounded-full shrink-0"
                                    style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
                                  />
                                  <div className="flex items-center gap-2 flex-1 min-w-0">
                                    {DEVICE_ICONS[d.device_type?.toLowerCase()] || <Monitor className="h-4 w-4" />}
                                    <span className="text-sm capitalize truncate">{d.device_type || "Unknown"}</span>
                                  </div>
                                  <span className="text-sm font-medium tabular-nums">{pct}%</span>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      ) : (
                        <div className="h-full flex items-center justify-center text-muted-foreground">
                          No data yet
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Conversion Funnel */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium">
                    Conversion Funnel (30 Days)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {funnel?.funnel?.length > 0 ? (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                      {funnel.funnel.map((step: any, i: number) => (
                        <div
                          key={i}
                          className="text-center p-4 rounded-lg border bg-card"
                        >
                          <p className="text-2xl font-bold text-indigo-600">
                            {step.count?.toLocaleString()}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1 capitalize">
                            {step.stage}
                          </p>
                          <div className="mt-2">
                            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                              <div
                                className="h-full bg-indigo-500 rounded-full transition-all"
                                style={{ width: `${Math.max(step.pct, 2)}%` }}
                              />
                            </div>
                            <p className="text-xs font-medium text-muted-foreground mt-1">
                              {step.pct}%
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No funnel data yet
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Agent Leaderboard */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm font-medium">
                    <TrendingUp className="h-4 w-4" />
                    Top Agents by Reports
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {agents.length > 0 ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="text-[11px] uppercase tracking-wider">Agent</TableHead>
                          <TableHead className="text-[11px] uppercase tracking-wider">Account</TableHead>
                          <TableHead className="text-[11px] uppercase tracking-wider text-right">Reports</TableHead>
                          <TableHead className="text-[11px] uppercase tracking-wider text-right">Views</TableHead>
                          <TableHead className="text-[11px] uppercase tracking-wider text-right">Contacts</TableHead>
                          <TableHead className="text-[11px] uppercase tracking-wider text-right">Rate</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {agents.map((agent, i) => (
                          <TableRow key={i}>
                            <TableCell>
                              <div>
                                <p className="font-medium text-sm">{agent.agent_name}</p>
                                <p className="text-xs text-muted-foreground">{agent.agent_email}</p>
                              </div>
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {agent.account_name}
                            </TableCell>
                            <TableCell className="text-right font-medium text-sm">
                              {agent.total_reports}
                            </TableCell>
                            <TableCell className="text-right text-sm text-muted-foreground">
                              {agent.total_views}
                            </TableCell>
                            <TableCell className="text-right text-sm text-muted-foreground">
                              {agent.contacts}
                            </TableCell>
                            <TableCell className="text-right">
                              <Badge
                                variant="outline"
                                className={
                                  agent.contact_rate_pct >= 10
                                    ? "text-green-600 border-green-200 bg-green-50"
                                    : agent.contact_rate_pct >= 5
                                      ? "text-yellow-600 border-yellow-200 bg-yellow-50"
                                      : ""
                                }
                              >
                                {agent.contact_rate_pct}%
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No agents with reports yet
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium">Recent Reports</CardTitle>
                </CardHeader>
                <CardContent>
                  {recent.length > 0 ? (
                    <div className="space-y-2">
                      {recent.map((report, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-muted/40 transition-colors"
                        >
                          <div className="flex-1 min-w-0 mr-4">
                            <p className="font-medium text-sm truncate">
                              {report.property_address}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {report.agent_name}
                            </p>
                          </div>
                          <div className="flex items-center gap-3 text-sm shrink-0">
                            <Badge
                              variant="outline"
                              className={
                                report.status === "ready"
                                  ? "text-green-600 border-green-200 bg-green-50"
                                  : report.status === "failed"
                                    ? "text-red-600 border-red-200 bg-red-50"
                                    : "text-yellow-600 border-yellow-200 bg-yellow-50"
                              }
                            >
                              {report.status}
                            </Badge>
                            <span className="text-muted-foreground text-xs">
                              {report.view_count} views
                            </span>
                            {report.agent_contacted && (
                              <Phone className="w-3.5 h-3.5 text-green-600" />
                            )}
                            {report.has_pdf && (
                              <Download className="w-3.5 h-3.5 text-indigo-600" />
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No recent reports yet
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
