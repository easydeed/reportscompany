"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { MoreHorizontal, Eye, Edit, Trash2, Calendar } from "lucide-react"
import { type Schedule, reportTypeLabels } from "./types"

export interface ScheduleTableProps {
  schedules: Schedule[]
  onToggleActive?: (id: string, active: boolean) => void
  onView?: (id: string) => void
  onEdit?: (id: string) => void
  onDelete?: (id: string) => void
}

export function ScheduleTable({ schedules, onToggleActive, onView, onEdit, onDelete }: ScheduleTableProps) {
  const [toggling, setToggling] = useState<string | null>(null)

  const handleToggle = async (id: string, currentActive: boolean) => {
    setToggling(id)
    await onToggleActive?.(id, !currentActive)
    setToggling(null)
  }

  const formatArea = (schedule: Schedule) => {
    if (schedule.area_mode === "city") {
      return schedule.city || "—"
    }
    return `ZIPs (${schedule.zips?.length || 0})`
  }

  const formatCadence = (schedule: Schedule) => {
    if (schedule.cadence === "weekly") {
      const day = schedule.weekday?.charAt(0).toUpperCase() + (schedule.weekday?.slice(1) || "")
      return `Weekly on ${day}`
    }
    return `Monthly on day ${schedule.monthly_day}`
  }

  const formatNextRun = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = date.getTime() - now.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return "Today"
    if (diffDays === 1) return "Tomorrow"
    if (diffDays < 7) return `In ${diffDays} days`
    return date.toLocaleDateString()
  }

  if (schedules.length === 0) {
    return (
      <div className="border border-border rounded-xl p-12 text-center">
        <Calendar className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <h3 className="font-display font-semibold text-lg mb-2">No schedules yet</h3>
        <p className="text-muted-foreground text-sm">Create your first automated schedule to get started</p>
      </div>
    )
  }

  return (
    <div className="border border-border rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted/50 border-b border-border">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Name
              </th>
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Report Type
              </th>
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Area
              </th>
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Cadence
              </th>
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Next Run
              </th>
              <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Active
              </th>
              <th className="text-right px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {schedules.map((schedule) => (
              <tr key={schedule.id} className="hover:bg-muted/30 transition-colors">
                <td className="px-4 py-3">
                  <button
                    onClick={() => onView?.(schedule.id)}
                    className="font-medium hover:text-primary transition-colors text-left"
                  >
                    {schedule.name}
                  </button>
                </td>
                <td className="px-4 py-3">
                  <Badge variant="secondary" className="font-normal">
                    {reportTypeLabels[schedule.report_type]}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{formatArea(schedule)}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{formatCadence(schedule)}</td>
                <td className="px-4 py-3 text-sm">
                  <span className="text-foreground font-medium">{formatNextRun(schedule.next_run)}</span>
                  <span className="text-muted-foreground ml-1">at {schedule.time}</span>
                </td>
                <td className="px-4 py-3">
                  <Switch
                    checked={schedule.active}
                    onCheckedChange={() => handleToggle(schedule.id, schedule.active)}
                    disabled={toggling === schedule.id}
                    aria-label={`Toggle ${schedule.name} ${schedule.active ? "off" : "on"}`}
                  />
                </td>
                <td className="px-4 py-3 text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreHorizontal className="w-4 h-4" />
                        <span className="sr-only">Open menu</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onView?.(schedule.id)} className="gap-2">
                        <Eye className="w-4 h-4" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => onEdit?.(schedule.id)} className="gap-2">
                        <Edit className="w-4 h-4" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onDelete?.(schedule.id)}
                        className="gap-2 text-destructive focus:text-destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
