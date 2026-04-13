'use client'

import { useEffect, useState, useMemo, useCallback } from "react"
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Calendar,
  AlertTriangle,
  Play,
  Pause,
  MoreHorizontal,
  Search,
  X,
  ExternalLink,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

interface Schedule {
  id: string
  name: string
  account_id: string
  account_name: string
  report_type: string
  city: string | null
  zips: string[] | null
  cadence: string
  active: boolean
  next_run_at: string | null
  last_run_at: string | null
  last_run_status: string | null
  created_at: string
}

const REPORT_TYPE_LABELS: Record<string, string> = {
  new_listings_gallery: "New Listings Gallery",
  closed: "Closed Sales",
  market_snapshot: "Market Snapshot",
  inventory: "Active Inventory",
  featured_listings: "Featured Listings",
  open_houses: "Open Houses",
  price_bands: "Price Bands",
  new_listings: "New Listings Analytics",
}

function formatTimeAgo(dateString: string | null): string {
  if (!dateString) return "—"
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

function formatNextRun(dateString: string | null): string {
  if (!dateString) return "—"
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMs < 0) return "Overdue"
  if (diffHours < 1) return "< 1h"
  if (diffHours < 24) return `in ${diffHours}h`
  return `in ${diffDays}d`
}

function getArea(schedule: Schedule): string {
  if (schedule.city) return schedule.city
  if (schedule.zips?.length) return `ZIP ${schedule.zips[0]}${schedule.zips.length > 1 ? ` +${schedule.zips.length - 1}` : ""}`
  return "—"
}

export default function AdminSchedulesPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)
  const [togglingId, setTogglingId] = useState<string | null>(null)

  const filterStatus = searchParams.get("status") || "all"
  const filterType = searchParams.get("report_type") || "all"
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "")

  const fetchSchedules = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterStatus !== "all") params.set("active", filterStatus === "active" ? "true" : "false")
      if (filterType !== "all") params.set("report_type", filterType)
      const acctId = searchParams.get("account_id")
      if (acctId) params.set("account_id", acctId)
      const q = searchParams.get("q")
      if (q) params.set("q", q)
      params.set("limit", "200")

      const res = await fetch(`/api/proxy/v1/admin/schedules?${params.toString()}`, { credentials: "include" })
      if (res.ok) {
        const data = await res.json()
        setSchedules(data?.schedules || data || [])
      }
    } catch (err) {
      console.error("Failed to fetch schedules:", err)
    } finally {
      setLoading(false)
    }
  }, [searchParams, filterStatus, filterType])

  useEffect(() => { fetchSchedules() }, [fetchSchedules])

  const stats = useMemo(() => {
    const active = schedules.filter(s => s.active).length
    const paused = schedules.filter(s => !s.active).length
    const failedRuns = schedules.filter(s => s.last_run_status === "failed").length
    return { active, paused, failedRuns }
  }, [schedules])

  async function toggleActive(schedule: Schedule) {
    setTogglingId(schedule.id)
    try {
      const res = await fetch(`/api/proxy/v1/admin/schedules/${schedule.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ active: !schedule.active }),
      })
      if (res.ok) {
        setSchedules(prev => prev.map(s => s.id === schedule.id ? { ...s, active: !s.active } : s))
        toast({
          title: schedule.active ? "Schedule paused" : "Schedule resumed",
          description: schedule.name,
        })
      } else {
        toast({ title: "Failed to update schedule", variant: "destructive" })
      }
    } catch {
      toast({ title: "Failed to update schedule", variant: "destructive" })
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
    router.push(`/app/admin/schedules?${params.toString()}`)
  }

  function clearFilters() {
    setSearchQuery("")
    router.push("/app/admin/schedules")
  }

  const hasFilters = filterStatus !== "all" || filterType !== "all" || searchParams.get("q") || searchParams.get("account_id")

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-72" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-8 w-16" /></CardContent></Card>
          ))}
        </div>
        <Card><CardContent className="pt-6">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="py-3 flex gap-4">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
          ))}
        </CardContent></Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-display font-bold">Schedules</h1>
        <p className="text-muted-foreground mt-2">Manage recurring report schedules across all accounts</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <Play className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{stats.active}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Paused</CardTitle>
            <Pause className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{stats.paused}</div></CardContent>
        </Card>
        <Card className={stats.failedRuns > 0 ? "bg-red-50 border-red-200" : ""}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed Last Run</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${stats.failedRuns > 0 ? "text-red-500" : "text-muted-foreground"}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.failedRuns > 0 ? "text-red-600" : ""}`}>{stats.failedRuns}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by name or account..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && updateFilter("q", searchQuery)}
            className="pl-9"
          />
        </div>

        <Select value={filterStatus} onValueChange={(v) => updateFilter("status", v)}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="paused">Paused</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filterType} onValueChange={(v) => updateFilter("report_type", v)}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Report Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {Object.entries(REPORT_TYPE_LABELS).map(([id, label]) => (
              <SelectItem key={id} value={id}>{label}</SelectItem>
            ))}
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
            <Calendar className="h-5 w-5" />
            Schedules ({schedules.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {schedules.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No schedules found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-[11px] uppercase tracking-wider">Name</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Account</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Type</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">City</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Cadence</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Next Run</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Status</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Last Run</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {schedules.map((schedule) => (
                  <TableRow key={schedule.id} className={!schedule.active ? "opacity-60" : ""}>
                    <TableCell className="font-medium text-sm max-w-[200px] truncate">
                      {schedule.name}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{schedule.account_name}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs font-medium">
                        {REPORT_TYPE_LABELS[schedule.report_type] || schedule.report_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{getArea(schedule)}</TableCell>
                    <TableCell className="text-sm capitalize">{schedule.cadence}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {schedule.active ? formatNextRun(schedule.next_run_at) : "—"}
                    </TableCell>
                    <TableCell>
                      <Badge className={schedule.active ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"}>
                        {schedule.active ? "Active" : "Paused"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {schedule.last_run_at ? (
                        <div className="flex items-center gap-1.5">
                          {schedule.last_run_status === "failed" && (
                            <AlertTriangle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                          )}
                          <span className={`text-sm ${schedule.last_run_status === "failed" ? "text-red-600" : "text-muted-foreground"}`}>
                            {formatTimeAgo(schedule.last_run_at)}
                          </span>
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground">Never</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button className="p-2 hover:bg-muted rounded-md">
                            <MoreHorizontal className="w-4 h-4" />
                          </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => toggleActive(schedule)}
                            disabled={togglingId === schedule.id}
                          >
                            {schedule.active ? (
                              <><Pause className="w-4 h-4 mr-2" /> Pause Schedule</>
                            ) : (
                              <><Play className="w-4 h-4 mr-2" /> Resume Schedule</>
                            )}
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link href={`/app/admin/accounts/${schedule.account_id}`}>
                              <ExternalLink className="w-4 h-4 mr-2" /> View Account
                            </Link>
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {schedules.length > 0 && (
            <p className="text-xs text-muted-foreground text-center mt-4">
              Showing {schedules.length} schedule{schedules.length !== 1 ? "s" : ""}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
