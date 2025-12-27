"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Calendar,
  Search,
  Play,
  Pause,
  RefreshCw,
  Loader2,
  Clock,
  Mail,
  AlertTriangle,
  CheckCircle,
} from "lucide-react"

interface Schedule {
  id: string
  account_id: string
  account_name: string
  name: string
  report_type: string
  city: string | null
  zip_codes: string[] | null
  cadence: string
  weekly_dow: number | null
  monthly_dom: number | null
  send_hour: number
  send_minute: number
  recipients: string[]
  active: boolean
  next_run_at: string | null
  last_run_at: string | null
  created_at: string
}

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [activeFilter, setActiveFilter] = useState<string>("all")
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    fetchSchedules()
  }, [search, activeFilter])

  async function fetchSchedules() {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (search) params.set("search", search)
      if (activeFilter !== "all") params.set("active", activeFilter === "active" ? "true" : "false")
      params.set("limit", "200")

      const res = await fetch(`/api/v1/admin/schedules?${params.toString()}`, {
        credentials: "include",
      })
      if (res.ok) {
        const data = await res.json()
        setSchedules(data.schedules || [])
      }
    } catch (error) {
      console.error("Failed to fetch schedules:", error)
    } finally {
      setLoading(false)
    }
  }

  async function toggleSchedule(scheduleId: string, active: boolean) {
    setActionLoading(scheduleId)
    try {
      const res = await fetch(`/api/v1/admin/schedules/${scheduleId}?active=${active}`, {
        method: "PATCH",
        credentials: "include",
      })
      if (res.ok) {
        fetchSchedules()
      }
    } catch (error) {
      console.error("Failed to toggle schedule:", error)
    } finally {
      setActionLoading(null)
    }
  }

  const formatTime = (hour: number, minute: number) => {
    const h = hour % 12 || 12
    const m = minute.toString().padStart(2, "0")
    const ampm = hour >= 12 ? "PM" : "AM"
    return `${h}:${m} ${ampm}`
  }

  const formatDate = (date: string | null) => {
    if (!date) return "-"
    return new Date(date).toLocaleString()
  }

  const formatTimeAgo = (date: string | null) => {
    if (!date) return "Never"
    const d = new Date(date)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    const mins = Math.floor(diff / (1000 * 60))
    if (mins < 0) {
      // Future
      const futureMins = Math.abs(mins)
      if (futureMins < 60) return `in ${futureMins}m`
      const hours = Math.floor(futureMins / 60)
      if (hours < 24) return `in ${hours}h`
      return `in ${Math.floor(hours / 24)}d`
    }
    if (mins < 60) return `${mins}m ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours}h ago`
    return `${Math.floor(hours / 24)}d ago`
  }

  const getCadenceLabel = (schedule: Schedule) => {
    switch (schedule.cadence) {
      case "daily":
        return "Daily"
      case "weekly":
        const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        return `Weekly (${days[schedule.weekly_dow || 0]})`
      case "monthly":
        return `Monthly (${schedule.monthly_dom}${getOrdinalSuffix(schedule.monthly_dom || 1)})`
      default:
        return schedule.cadence
    }
  }

  const getOrdinalSuffix = (n: number) => {
    const s = ["th", "st", "nd", "rd"]
    const v = n % 100
    return s[(v - 20) % 10] || s[v] || s[0]
  }

  // Calculate stats
  const stats = {
    total: schedules.length,
    active: schedules.filter((s) => s.active).length,
    paused: schedules.filter((s) => !s.active).length,
    dueSoon: schedules.filter((s) => {
      if (!s.next_run_at || !s.active) return false
      const nextRun = new Date(s.next_run_at)
      const now = new Date()
      const diff = nextRun.getTime() - now.getTime()
      return diff > 0 && diff < 60 * 60 * 1000 // Within 1 hour
    }).length,
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Schedules</h1>
          <p className="text-slate-500 mt-1">Monitor and manage all automated report schedules</p>
        </div>
        <Button
          variant="outline"
          onClick={fetchSchedules}
          className="border-slate-300 text-slate-600 hover:bg-slate-50"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Schedules</p>
                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              </div>
              <Calendar className="h-6 w-6 text-slate-300" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Active</p>
                <p className="text-2xl font-bold text-emerald-600">{stats.active}</p>
              </div>
              <CheckCircle className="h-6 w-6 text-emerald-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Paused</p>
                <p className="text-2xl font-bold text-amber-600">{stats.paused}</p>
              </div>
              <Pause className="h-6 w-6 text-amber-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Due Soon (&lt;1h)</p>
                <p className="text-2xl font-bold text-blue-600">{stats.dueSoon}</p>
              </div>
              <Clock className="h-6 w-6 text-blue-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="relative flex-1 min-w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by schedule or account name..."
                className="pl-10 bg-white border-slate-300 text-slate-900"
              />
            </div>
            <Select value={activeFilter} onValueChange={setActiveFilter}>
              <SelectTrigger className="w-40 bg-white border-slate-300 text-slate-900">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent className="bg-white border-slate-200">
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active Only</SelectItem>
                <SelectItem value="paused">Paused Only</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Schedules Table */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardContent className="pt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            </div>
          ) : schedules.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">No schedules found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 hover:bg-transparent">
                  <TableHead className="text-slate-500">Schedule</TableHead>
                  <TableHead className="text-slate-500">Account</TableHead>
                  <TableHead className="text-slate-500">Report</TableHead>
                  <TableHead className="text-slate-500">Cadence</TableHead>
                  <TableHead className="text-slate-500">Time</TableHead>
                  <TableHead className="text-slate-500">Recipients</TableHead>
                  <TableHead className="text-slate-500">Next Run</TableHead>
                  <TableHead className="text-slate-500">Last Run</TableHead>
                  <TableHead className="text-slate-500">Status</TableHead>
                  <TableHead className="text-slate-500 w-20">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {schedules.map((schedule) => (
                  <TableRow key={schedule.id} className="border-slate-100">
                    <TableCell>
                      <div>
                        <p className="text-slate-900 font-medium">{schedule.name}</p>
                        <p className="text-xs text-slate-400">
                          {schedule.city || (schedule.zip_codes || []).slice(0, 2).join(", ")}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-700">{schedule.account_name}</TableCell>
                    <TableCell>
                      <span className="text-slate-600 text-sm">
                        {schedule.report_type.replace(/_/g, " ")}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="border-slate-300 text-slate-600">
                        {getCadenceLabel(schedule)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-600 font-mono text-sm">
                      {formatTime(schedule.send_hour, schedule.send_minute)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-slate-500">
                        <Mail className="h-3 w-3" />
                        <span>{schedule.recipients?.length || 0}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {schedule.active && schedule.next_run_at ? (
                        <div>
                          <p className="text-slate-600 text-sm">{formatTimeAgo(schedule.next_run_at)}</p>
                          <p className="text-xs text-slate-400">
                            {new Date(schedule.next_run_at).toLocaleDateString()}
                          </p>
                        </div>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">
                      {formatTimeAgo(schedule.last_run_at)}
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={
                          schedule.active
                            ? "bg-emerald-100 text-emerald-700 border-emerald-200"
                            : "bg-amber-100 text-amber-700 border-amber-200"
                        }
                      >
                        {schedule.active ? "Active" : "Paused"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {actionLoading === schedule.id ? (
                        <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                      ) : schedule.active ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => toggleSchedule(schedule.id, false)}
                          className="text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                          title="Pause schedule"
                        >
                          <Pause className="h-4 w-4" />
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => toggleSchedule(schedule.id, true)}
                          className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                          title="Activate schedule"
                        >
                          <Play className="h-4 w-4" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Info Box */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-blue-500 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-blue-800">Schedule Processing</p>
              <p className="text-sm text-blue-600 mt-1">
                Schedules are processed by the background worker every 60 seconds. The "Next Run"
                time is automatically computed based on cadence and timezone. Pausing a schedule
                will prevent it from running until reactivated.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

