"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { ScheduleDetail, type Schedule, type ScheduleRun } from "@/components/schedules"
import { apiFetch } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

export default function ScheduleDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { toast } = useToast()
  
  const scheduleId = params.id as string
  
  const [schedule, setSchedule] = useState<Schedule | null>(null)
  const [runs, setRuns] = useState<ScheduleRun[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadScheduleData()
  }, [scheduleId])

  const loadScheduleData = async () => {
    try {
      setLoading(true)
      
      // Load schedule and runs in parallel
      const [scheduleData, runsData] = await Promise.all([
        apiFetch(`/v1/schedules/${scheduleId}`),
        apiFetch(`/v1/schedules/${scheduleId}/runs`),
      ])
      
      setSchedule(scheduleData)
      setRuns(runsData)
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Error loading schedule",
        description: error.message,
      })
      // Navigate back on error
      router.push("/app/schedules")
    } finally {
      setLoading(false)
    }
  }

  const handleToggleActive = async (active: boolean) => {
    if (!schedule) return

    try {
      await apiFetch(`/v1/schedules/${scheduleId}`, {
        method: "PATCH",
        body: JSON.stringify({ active }),
      })
      
      setSchedule({ ...schedule, active })
      
      toast({
        title: active ? "Schedule activated" : "Schedule paused",
        description: active ? "Reports will be generated automatically" : "Automatic generation paused",
      })
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Error updating schedule",
        description: error.message,
      })
      // Reload on error
      loadScheduleData()
    }
  }

  const handleRunNow = async () => {
    if (!schedule) return

    try {
      // Set next_run_at to now to trigger immediate execution by ticker
      await apiFetch(`/v1/schedules/${scheduleId}`, {
        method: "PATCH",
        body: JSON.stringify({ 
          next_run_at: new Date().toISOString() 
        }),
      })
      
      toast({
        title: "Schedule queued",
        description: "The report will be generated within the next minute",
      })
      
      // Reload to show updated next_run_at
      setTimeout(() => loadScheduleData(), 2000)
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Error triggering run",
        description: error.message,
      })
    }
  }

  const handleEdit = () => {
    // TODO: Implement edit flow (Phase 24F)
    toast({
      title: "Edit coming soon",
      description: "Schedule editing will be available in the next update",
    })
  }

  const handleDelete = async () => {
    if (!schedule) return

    if (!confirm(`Are you sure you want to delete "${schedule.name}"? This action cannot be undone.`)) {
      return
    }

    try {
      await apiFetch(`/v1/schedules/${scheduleId}`, {
        method: "DELETE",
      })
      
      toast({
        title: "Schedule deleted",
        description: "The schedule has been permanently removed",
      })
      
      router.push("/app/schedules")
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Error deleting schedule",
        description: error.message,
      })
    }
  }

  if (loading || !schedule) {
    return (
      <div className="space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h1 className="font-display font-bold text-3xl mb-2">Loading...</h1>
            <p className="text-muted-foreground">Fetching schedule details</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <ScheduleDetail
      schedule={schedule}
      runs={runs}
      onBack={() => router.push("/app/schedules")}
      onToggleActive={handleToggleActive}
      onRunNow={handleRunNow}
      onEdit={handleEdit}
      onDelete={handleDelete}
    />
  )
}

