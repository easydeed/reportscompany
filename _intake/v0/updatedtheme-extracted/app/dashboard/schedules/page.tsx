"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { ScheduleTable, type Schedule } from "@/components/schedules"
import { useRouter } from "next/navigation"
import { Badge } from "@/components/ui/badge"

const mockSchedules: Schedule[] = [
  {
    id: "1",
    name: "Weekly SF Market Update",
    report_type: "market_snapshot",
    area_mode: "city",
    city: "San Francisco",
    lookback_days: 7,
    cadence: "weekly",
    weekday: "monday",
    time: "09:00",
    recipients: ["agent@example.com", "broker@example.com"],
    active: true,
    next_run: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
    last_run: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "2",
    name: "Monthly Bay Area Inventory",
    report_type: "inventory",
    area_mode: "zips",
    zips: ["94102", "94103", "94104", "94105"],
    lookback_days: 30,
    cadence: "monthly",
    monthly_day: 1,
    time: "08:00",
    recipients: ["team@realty.com"],
    active: true,
    next_run: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString(),
    last_run: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "3",
    name: "Bi-weekly Closed Sales Report",
    report_type: "closed",
    area_mode: "city",
    city: "Oakland",
    lookback_days: 14,
    cadence: "weekly",
    weekday: "friday",
    time: "14:00",
    recipients: ["manager@realty.com"],
    active: false,
    next_run: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
    last_run: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
  },
]

export default function SchedulesPage() {
  const router = useRouter()
  const [schedules, setSchedules] = useState<Schedule[]>(mockSchedules)
  const [filter, setFilter] = useState<"all" | "active">("all")

  const handleToggleActive = async (id: string, active: boolean) => {
    console.log("[v0] Toggle schedule", id, "to", active)
    setSchedules((prev) => prev.map((s) => (s.id === id ? { ...s, active } : s)))
  }

  const handleView = (id: string) => {
    console.log("[v0] View schedule", id)
    router.push(`/dashboard/schedules/${id}`)
  }

  const handleEdit = (id: string) => {
    console.log("[v0] Edit schedule", id)
  }

  const handleDelete = (id: string) => {
    console.log("[v0] Delete schedule", id)
    setSchedules((prev) => prev.filter((s) => s.id !== id))
  }

  const filteredSchedules = filter === "all" ? schedules : schedules.filter((s) => s.active)

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display font-bold text-3xl mb-2 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
            Schedules
          </h1>
          <p className="text-muted-foreground">Automate report generation with recurring schedules</p>
          <div className="flex items-center gap-3 mt-4">
            <Badge variant="outline" className="gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
              {schedules.filter((s) => s.active).length} Active
            </Badge>
            <Badge variant="outline" className="gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
              {schedules.filter((s) => !s.active).length} Inactive
            </Badge>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 border border-border rounded-lg p-1 bg-muted/20">
            <button
              onClick={() => setFilter("all")}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                filter === "all"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter("active")}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                filter === "active"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Active
            </button>
          </div>
          <Button onClick={() => router.push("/dashboard/schedules/new")} className="gap-2">
            <Plus className="w-4 h-4" />
            New Schedule
          </Button>
        </div>
      </div>

      <ScheduleTable
        schedules={filteredSchedules}
        onToggleActive={handleToggleActive}
        onView={handleView}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />
    </div>
  )
}
