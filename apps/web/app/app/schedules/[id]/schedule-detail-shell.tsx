"use client"

import { useRouter } from "next/navigation"
import { ScheduleDetail } from "@/components/schedules/schedule-detail"

export function ScheduleDetailShell({ schedule }: { schedule: any }) {
  const router = useRouter()

  const handleToggleActive = async (active: boolean) => {
    try {
      await fetch(`/api/proxy/v1/schedules/${schedule.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ active }),
      })
      router.refresh()
    } catch (err) {
      console.error("Failed to toggle schedule:", err)
    }
  }

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this schedule?")) return
    try {
      await fetch(`/api/proxy/v1/schedules/${schedule.id}`, {
        method: "DELETE",
        credentials: "include",
      })
      router.push("/app/schedules")
    } catch (err) {
      console.error("Failed to delete schedule:", err)
    }
  }

  return (
    <ScheduleDetail
      schedule={schedule}
      runs={[]}
      onBack={() => router.back()}
      onToggleActive={handleToggleActive}
      onRunNow={() => {}}
      onEdit={() => router.push(`/app/schedules/${schedule.id}/edit`)}
      onDelete={handleDelete}
    />
  )
}
