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
      return `Weekly · ${day}`
    }
    return `Monthly · Day ${schedule.monthly_day}`
  }

  const formatNextRun = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = date.getTime() - now.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return "Today"
    if (diffDays === 1) return "Tomorrow"
    if (diffDays < 7) return `${diffDays}d`
    return date.toLocaleDateString()
  }

  if (schedules.length === 0) {
    return (
      <div className="border border-border/50 rounded-xl p-12 text-center bg-gradient-to-b from-muted/20 to-transparent">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
          <Calendar className="w-8 h-8 text-primary" />
        </div>
        <h3 className="font-display font-semibold text-lg mb-2">No schedules found</h3>
        <p className="text-muted-foreground text-sm max-w-md mx-auto">
          Create your first automated schedule to start generating reports on a recurring basis
        </p>
      </div>
    )
  }

  return (
    <div className="border border-border/50 rounded-xl overflow-hidden bg-card/50 backdrop-blur-sm">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted/30 border-b border-border/50">
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
          <tbody className="divide-y divide-border/30">
            {schedules.map((schedule) => (
              <tr key={schedule.id} className="hover:bg-muted/20 transition-colors duration-150">
                <td className="px-4 py-3">
                  <button
                    onClick={() => onView?.(schedule.id)}
                    className="font-medium hover:text-primary transition-colors text-left group flex items-center gap-2"
                  >
                    {schedule.name}
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${schedule.active ? "bg-cyan-500" : "bg-slate-400"}`}
                      aria-label={schedule.active ? "Active" : "Inactive"}
                    />
                  </button>
                </td>
                <td className="px-4 py-3">
                  <Badge variant="secondary" className="font-normal bg-primary/10 text-primary border-primary/20">
                    {reportTypeLabels[schedule.report_type]}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{formatArea(schedule)}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground font-mono">{formatCadence(schedule)}</td>
                <td className="px-4 py-3 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-medium font-mono">{formatNextRun(schedule.next_run)}</span>
                    <span className="text-muted-foreground text-xs">at {schedule.time}</span>
                  </div>
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
