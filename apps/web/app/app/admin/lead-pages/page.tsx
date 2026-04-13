"use client"

import { useEffect, useState, useMemo } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
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
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

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

export default function AdminLeadPagesPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()

  const [pages, setPages] = useState<LeadPage[]>([])
  const [stats, setStats] = useState<Stats>({ active_pages: 0, total_leads: 0, leads_this_month: 0 })
  const [loading, setLoading] = useState(true)
  const [togglingId, setTogglingId] = useState<string | null>(null)

  const filterStatus = searchParams.get("status") || "all"
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "")

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        const status = searchParams.get("status")
        if (status && status !== "all") params.set("status", status)
        params.set("limit", "200")

        const res = await fetch(`/api/proxy/v1/admin/lead-pages?${params.toString()}`, {
          credentials: "include",
        })
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
    router.push(`/app/admin/lead-pages?${params.toString()}`)
  }

  function clearFilters() {
    setSearchQuery("")
    router.push("/app/admin/lead-pages")
  }

  const hasFilters = filterStatus !== "all" || searchParams.get("q")

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
            All CMA lead pages across accounts
          </p>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Pages</CardTitle>
            <Link2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.active_pages}</div>
            <p className="text-xs text-muted-foreground">
              of {pages.length} total
            </p>
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
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Agent
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Code / URL
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Account
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Status
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider text-right">
                    Visits
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider text-right">
                    Leads
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Last Lead
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Created
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Actions
                  </TableHead>
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
                        <p className="text-xs text-muted-foreground">
                          {page.email}
                        </p>
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
                        <Badge
                          variant="outline"
                          className="text-green-600 border-green-200 bg-green-50"
                        >
                          Active
                        </Badge>
                      ) : (
                        <Badge
                          variant="outline"
                          className="text-red-600 border-red-200 bg-red-50"
                        >
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
                          title={
                            page.enabled ? "Disable page" : "Enable page"
                          }
                        >
                          {togglingId === page.user_id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : page.enabled ? (
                            <ToggleRight className="h-4 w-4 text-green-600" />
                          ) : (
                            <ToggleLeft className="h-4 w-4 text-muted-foreground" />
                          )}
                        </Button>
                        <Link
                          href={`/app/admin/leads?account_id=${page.account_id}`}
                        >
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            title="View leads"
                          >
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
    </div>
  )
}
