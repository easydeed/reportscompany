"use client"

import { SchedulesTable } from "./schedules-table"
import type { AdminSchedule } from "./types"
import { useRouter } from "next/navigation"
import { useToast } from "@/components/ui/use-toast"

interface SchedulesTableClientProps {
  schedules: AdminSchedule[]
}

export function SchedulesTableClient({ schedules }: SchedulesTableClientProps) {
  const router = useRouter()
  const { toast } = useToast()

  const handleToggleActive = async (id: string, active: boolean) => {
    try {
      const response = await fetch(`/api/proxy/v1/admin/schedules/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ active }),
      })

      if (!response.ok) {
        throw new Error("Failed to update schedule")
      }

      toast({
        title: "Schedule updated",
        description: `Schedule ${active ? "activated" : "paused"} successfully`,
      })

      // Refresh the page data
      router.refresh()
    } catch (error) {
      console.error("Failed to toggle schedule:", error)
      toast({
        title: "Error",
        description: "Failed to update schedule. Please try again.",
        variant: "destructive",
      })
    }
  }

  return <SchedulesTable schedules={schedules} onToggleActive={handleToggleActive} />
}

