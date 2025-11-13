"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { ScheduleTable, ScheduleWizard, type Schedule, type ScheduleWizardState } from "@/components/schedules"
import { useRouter } from "next/navigation"

// Mock data - parent will wire real data
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
]

export default function SchedulesPage() {
  const router = useRouter()
  const [showWizard, setShowWizard] = useState(false)
  const [schedules, setSchedules] = useState<Schedule[]>(mockSchedules)

  const handleToggleActive = async (id: string, active: boolean) => {
    // Parent will wire API call
    console.log("[v0] Toggle schedule", id, "to", active)
    setSchedules((prev) => prev.map((s) => (s.id === id ? { ...s, active } : s)))
  }

  const handleView = (id: string) => {
    // Parent will wire navigation
    console.log("[v0] View schedule", id)
    router.push(`/dashboard/schedules/${id}`)
  }

  const handleEdit = (id: string) => {
    // Parent will wire edit flow
    console.log("[v0] Edit schedule", id)
  }

  const handleDelete = (id: string) => {
    // Parent will wire API call
    console.log("[v0] Delete schedule", id)
    setSchedules((prev) => prev.filter((s) => s.id !== id))
  }

  const handleSubmitWizard = async (data: ScheduleWizardState) => {
    // Parent will wire API call
    console.log("[v0] Create schedule", data)
    setShowWizard(false)
    // After successful creation, parent would refresh schedules list
  }

  if (showWizard) {
    return <ScheduleWizard onSubmit={handleSubmitWizard} onCancel={() => setShowWizard(false)} />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-3xl mb-2">Schedules</h1>
          <p className="text-muted-foreground">Automate report generation with recurring schedules</p>
        </div>
        <Button onClick={() => setShowWizard(true)} className="gap-2">
          <Plus className="w-4 h-4" />
          New Schedule
        </Button>
      </div>

      <ScheduleTable
        schedules={schedules}
        onToggleActive={handleToggleActive}
        onView={handleView}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />
    </div>
  )
}
