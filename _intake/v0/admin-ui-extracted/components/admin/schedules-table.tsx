"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import type { AdminSchedule } from "./types"

interface SchedulesTableProps {
  schedules: AdminSchedule[]
  onToggleActive?: (id: string, active: boolean) => void
}

export function SchedulesTable({ schedules, onToggleActive }: SchedulesTableProps) {
  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(date)
  }

  return (
    <Card className="glass border-border">
      <div className="p-6 border-b border-border">
        <h3 className="text-lg font-display font-semibold text-foreground">Schedules</h3>
        <p className="text-sm text-muted-foreground">Active schedules across all organizations</p>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-border">
              <TableHead className="font-semibold">Organization</TableHead>
              <TableHead className="font-semibold">Name</TableHead>
              <TableHead className="font-semibold">Cadence</TableHead>
              <TableHead className="font-semibold">Next Run</TableHead>
              <TableHead className="font-semibold">Active</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {schedules.map((schedule) => (
              <TableRow key={schedule.id} className="border-border">
                <TableCell className="text-muted-foreground">{schedule.org}</TableCell>
                <TableCell className="font-medium">{schedule.name}</TableCell>
                <TableCell className="text-muted-foreground">{schedule.cadence}</TableCell>
                <TableCell className="text-muted-foreground">{formatDate(schedule.nextRun)}</TableCell>
                <TableCell>
                  <Switch
                    checked={schedule.active}
                    onCheckedChange={(checked) => onToggleActive?.(schedule.id, checked)}
                    aria-label={`Toggle ${schedule.name} schedule`}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  )
}
