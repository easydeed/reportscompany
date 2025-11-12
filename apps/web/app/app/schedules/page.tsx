"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { 
  ScheduleTable, 
  ScheduleWizard, 
  type Schedule, 
  type ScheduleWizardState,
  wizardStateToApiPayload 
} from "@/components/schedules"
import { apiFetch } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"

export default function SchedulesPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [showWizard, setShowWizard] = useState(false)
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)

  // Load schedules on mount
  useEffect(() => {
    loadSchedules()
  }, [])

  const loadSchedules = async () => {
    try {
      setLoading(true)
      const data = await apiFetch("/v1/schedules")
      setSchedules(data)
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Error loading schedules",
        description: error.message,
      })
    } finally {
      setLoading(false)
    }
  }

  const handleToggleActive = async (id: string, active: boolean) => {
    try {
      await apiFetch(`/v1/schedules/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ active }),
      })
      
      // Update local state
      setSchedules((prev) =>
        prev.map((s) => (s.id === id ? { ...s, active } : s))
      )
      
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
      // Revert on error
      loadSchedules()
    }
  }

  const handleView = (id: string) => {
    router.push(`/app/schedules/${id}`)
  }

  const handleEdit = (id: string) => {
    // TODO: Implement edit flow (Phase 24F)
    toast({
      title: "Edit coming soon",
      description: "Schedule editing will be available in the next update",
    })
  }

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this schedule? This action cannot be undone.")) {
      return
    }

    try {
      await apiFetch(`/v1/schedules/${id}`, {
        method: "DELETE",
      })
      
      setSchedules((prev) => prev.filter((s) => s.id !== id))
      
      toast({
        title: "Schedule deleted",
        description: "The schedule has been permanently removed",
      })
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Error deleting schedule",
        description: error.message,
      })
    }
  }

  const handleSubmitWizard = async (wizardState: ScheduleWizardState) => {
    try {
      const payload = wizardStateToApiPayload(wizardState)
      
      const created = await apiFetch("/v1/schedules", {
        method: "POST",
        body: JSON.stringify(payload),
      })
      
      setSchedules((prev) => [created, ...prev])
      setShowWizard(false)
      
      toast({
        title: "Schedule created!",
        description: `"${created.name}" will run ${created.cadence === "weekly" ? "weekly" : "monthly"}`,
      })
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Error creating schedule",
        description: error.message,
      })
    }
  }

  if (showWizard) {
    return (
      <ScheduleWizard
        onSubmit={handleSubmitWizard}
        onCancel={() => setShowWizard(false)}
      />
    )
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display font-bold text-3xl mb-2">Schedules</h1>
            <p className="text-muted-foreground">Automate report generation with recurring schedules</p>
          </div>
        </div>
        <div className="border border-border rounded-xl p-12 text-center">
          <p className="text-muted-foreground">Loading schedules...</p>
        </div>
      </div>
    )
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

