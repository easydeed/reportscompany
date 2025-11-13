"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table"
import { Card } from "../ui/card"
import { Switch } from "../ui/switch"
import { Button } from "../ui/button"
import { MoreVertical, Pause, Play, ExternalLink } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "../ui/dropdown-menu"
import type { AdminSchedule } from "./types"

interface AdminSchedulesTableProps {
  schedules: AdminSchedule[]
  onToggleActive?: (id: string, active: boolean) => void
  onPauseResume?: (id: string, action: "pause" | "resume") => void
  onImpersonate?: (org: string) => void
}

export function AdminSchedulesTable({
  schedules,
  onToggleActive,
  onPauseResume,
  onImpersonate,
}: AdminSchedulesTableProps) {
  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(date)
  }

  return (
    <Card className="glass border-border/50 backdrop-blur-sm">
      <div className="p-6 border-b border-border/50">
        <h3 className="text-lg font-display font-semibold text-white">Schedules</h3>
        <p className="text-sm text-slate-400">Active schedules across all organizations</p>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-border/50">
              <TableHead className="font-semibold text-slate-300">Organization</TableHead>
              <TableHead className="font-semibold text-slate-300">Name</TableHead>
              <TableHead className="font-semibold text-slate-300">Cadence</TableHead>
              <TableHead className="font-semibold text-slate-300">Next Run</TableHead>
              <TableHead className="font-semibold text-slate-300">Active</TableHead>
              <TableHead className="font-semibold text-slate-300 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {schedules.map((schedule) => (
              <TableRow key={schedule.id} className="border-border/50 hover:bg-slate-800/30">
                <TableCell className="text-slate-400">{schedule.org}</TableCell>
                <TableCell className="font-medium text-white">{schedule.name}</TableCell>
                <TableCell className="text-slate-400 font-mono text-sm">{schedule.cadence}</TableCell>
                <TableCell className="text-slate-400 font-mono text-sm">{formatDate(schedule.nextRun)}</TableCell>
                <TableCell>
                  <Switch
                    checked={schedule.active}
                    onCheckedChange={(checked) => onToggleActive?.(schedule.id, checked)}
                    aria-label={`Toggle ${schedule.name} schedule`}
                  />
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <MoreVertical className="h-4 w-4" />
                        <span className="sr-only">Open menu</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="glass border-border/50">
                      <DropdownMenuItem
                        onClick={() => onPauseResume?.(schedule.id, schedule.active ? "pause" : "resume")}
                      >
                        {schedule.active ? (
                          <>
                            <Pause className="mr-2 h-4 w-4" />
                            Pause
                          </>
                        ) : (
                          <>
                            <Play className="mr-2 h-4 w-4" />
                            Resume
                          </>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => onImpersonate?.(schedule.org)}>
                        <ExternalLink className="mr-2 h-4 w-4" />
                        Impersonate Org
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  )
}
