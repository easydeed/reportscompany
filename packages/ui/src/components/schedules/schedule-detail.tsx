"use client"

import { Button } from "../ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card"
import { Badge } from "../ui/badge"
import { Switch } from "../ui/switch"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table"
import {
  ArrowLeft,
  Play,
  Edit,
  Trash2,
  Mail,
  MapPin,
  Hash,
  Calendar,
  Clock,
  AlertCircle,
  CheckCircle2,
  Loader2,
} from "lucide-react"
import { type Schedule, type ScheduleRun, reportTypeLabels } from "./types"
import { cn } from "../../lib/utils"

export interface ScheduleDetailProps {
  schedule: Schedule
  runs: ScheduleRun[]
  onBack?: () => void
  onToggleActive?: (active: boolean) => void
  onRunNow?: () => void
  onEdit?: () => void
  onDelete?: () => void
}

export function ScheduleDetail({
  schedule,
  runs,
  onBack,
  onToggleActive,
  onRunNow,
  onEdit,
  onDelete,
}: ScheduleDetailProps) {
  const formatArea = () => {
    if (schedule.area_mode === "city") {
      return (
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-muted-foreground" />
          <span>{schedule.city}</span>
        </div>
      )
    }
    return (
      <div className="flex items-center gap-2">
        <Hash className="w-4 h-4 text-muted-foreground" />
        <span>ZIP codes ({schedule.zips?.length || 0})</span>
        {schedule.zips && schedule.zips.length > 0 && (
          <div className="flex flex-wrap gap-1 ml-2">
            {schedule.zips.slice(0, 3).map((zip) => (
              <Badge key={zip} variant="outline" className="text-xs">
                {zip}
              </Badge>
            ))}
            {schedule.zips.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{schedule.zips.length - 3}
              </Badge>
            )}
          </div>
        )}
      </div>
    )
  }

  const formatCadence = () => {
    if (schedule.cadence === "weekly") {
      const day = schedule.weekday?.charAt(0).toUpperCase() + (schedule.weekday?.slice(1) || "")
      return `Weekly on ${day} at ${schedule.time}`
    }
    return `Monthly on day ${schedule.monthly_day} at ${schedule.time}`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const getStatusColor = (status: ScheduleRun["status"]) => {
    switch (status) {
      case "completed":
        return "text-green-600 bg-green-50 border-green-200 dark:text-green-400 dark:bg-green-950 dark:border-green-800"
      case "processing":
        return "text-cyan-600 bg-cyan-50 border-cyan-200 dark:text-cyan-400 dark:bg-cyan-950 dark:border-cyan-800"
      case "failed":
        return "text-red-600 bg-red-50 border-red-200 dark:text-red-400 dark:bg-red-950 dark:border-red-800"
      default:
        return "text-slate-600 bg-slate-50 border-slate-200 dark:text-slate-400 dark:bg-slate-950 dark:border-slate-800"
    }
  }

  const getStatusIcon = (status: ScheduleRun["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-3.5 h-3.5" />
      case "processing":
        return <Loader2 className="w-3.5 h-3.5 animate-spin" />
      case "failed":
        return <AlertCircle className="w-3.5 h-3.5" />
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <Button variant="ghost" onClick={onBack} className="gap-2 mb-3 -ml-3">
            <ArrowLeft className="w-4 h-4" />
            Back to Schedules
          </Button>
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <h1 className="font-display font-bold text-3xl mb-2">{schedule.name}</h1>
              <div className="flex items-center gap-3">
                <Badge variant="secondary">{reportTypeLabels[schedule.report_type]}</Badge>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={schedule.active}
                    onCheckedChange={onToggleActive}
                    aria-label={`Toggle schedule ${schedule.active ? "off" : "on"}`}
                  />
                  <span className="text-sm text-muted-foreground">{schedule.active ? "Active" : "Inactive"}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onRunNow} disabled className="gap-2 bg-transparent">
            <Play className="w-4 h-4" />
            Run Now
          </Button>
          <Button variant="outline" onClick={onEdit} className="gap-2 bg-transparent">
            <Edit className="w-4 h-4" />
            Edit
          </Button>
          <Button
            variant="outline"
            onClick={onDelete}
            className="gap-2 text-destructive hover:text-destructive bg-transparent"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </Button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Area</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">{formatArea()}</div>
          </CardContent>
        </Card>
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Cadence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-start gap-2">
              <Calendar className="w-4 h-4 text-cyan-500 mt-0.5" />
              <span className="text-sm font-medium font-mono">{formatCadence()}</span>
            </div>
          </CardContent>
        </Card>
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Next Run
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-start gap-2">
              <Clock className="w-4 h-4 text-cyan-500 mt-0.5" />
              <span className="text-sm font-medium font-mono">{formatDate(schedule.next_run)}</span>
            </div>
          </CardContent>
        </Card>
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Last Run
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-start gap-2">
              <Clock className="w-4 h-4 text-muted-foreground mt-0.5" />
              <span className="text-sm font-medium font-mono">
                {schedule.last_run ? formatDate(schedule.last_run) : "Never"}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-lg font-display flex items-center gap-2">
            <Mail className="w-5 h-5 text-cyan-500" />
            Recipients ({schedule.recipients.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {schedule.recipients.map((email) => (
              <Badge
                key={email}
                variant="secondary"
                className="gap-2 bg-primary/10 text-primary border-primary/20 font-mono"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
                {email}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-lg font-display">Run History</CardTitle>
        </CardHeader>
        <CardContent>
          {runs.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-muted/50 flex items-center justify-center">
                <Calendar className="w-8 h-8 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground">No runs yet</p>
              <p className="text-sm text-muted-foreground mt-1">This schedule hasn't been executed</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-border/50">
                  <tr>
                    <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase">Created</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase">Status</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase">
                      Duration
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase">Error</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/30">
                  {runs.map((run) => {
                    const duration = run.finished_at
                      ? Math.round((new Date(run.finished_at).getTime() - new Date(run.created_at).getTime()) / 1000)
                      : null

                    return (
                      <tr key={run.id} className="hover:bg-muted/20 transition-colors duration-150">
                        <td className="px-4 py-3 text-sm font-mono">{formatDate(run.created_at)}</td>
                        <td className="px-4 py-3">
                          <Badge variant="outline" className={`gap-1.5 ${getStatusColor(run.status)}`}>
                            {getStatusIcon(run.status)}
                            {run.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-sm text-muted-foreground font-mono">
                          {duration ? `${duration}s` : "—"}
                        </td>
                        <td className="px-4 py-3">
                          {run.error ? (
                            <div className="flex items-center gap-2 text-sm text-destructive">
                              <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                              <span className="truncate max-w-xs">{run.error}</span>
                            </div>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
