"use client"

import { useRouter } from "next/navigation"
import { ScheduleDetail, type Schedule, type ScheduleRun } from "@/components/schedules"

// Mock data - parent will wire real data from API
const mockSchedule: Schedule = {
  id: "1",
  name: "Weekly SF Market Update",
  report_type: "market_snapshot",
  area_mode: "city",
  city: "San Francisco",
  lookback_days: 7,
  cadence: "weekly",
  weekday: "monday",
  time: "09:00",
  recipients: ["agent@example.com", "broker@example.com", "team@realty.com"],
  active: true,
  next_run: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
  last_run: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
  created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
}

const mockRuns: ScheduleRun[] = [
  {
    id: "r1",
    schedule_id: "1",
    created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    status: "completed",
    finished_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000 + 30000).toISOString(),
  },
  {
    id: "r2",
    schedule_id: "1",
    created_at: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString(),
    status: "completed",
    finished_at: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000 + 25000).toISOString(),
  },
  {
    id: "r3",
    schedule_id: "1",
    created_at: new Date(Date.now() - 19 * 24 * 60 * 60 * 1000).toISOString(),
    status: "failed",
    finished_at: new Date(Date.now() - 19 * 24 * 60 * 60 * 1000 + 5000).toISOString(),
    error: "MLS data service temporarily unavailable",
  },
]

export default function ScheduleDetailPage() {
  const router = useRouter()

  const handleToggleActive = async (active: boolean) => {
    // Parent will wire API call
    console.log("[v0] Toggle schedule to", active)
  }

  const handleRunNow = async () => {
    // Parent will wire API call
    console.log("[v0] Run schedule now")
  }

  const handleEdit = () => {
    // Parent will wire edit flow
    console.log("[v0] Edit schedule")
  }

  const handleDelete = async () => {
    // Parent will wire API call and navigation
    console.log("[v0] Delete schedule")
    router.push("/dashboard/schedules")
  }

  return (
    <ScheduleDetail
      schedule={mockSchedule}
      runs={mockRuns}
      onBack={() => router.push("/dashboard/schedules")}
      onToggleActive={handleToggleActive}
      onRunNow={handleRunNow}
      onEdit={handleEdit}
      onDelete={handleDelete}
    />
  )
}
