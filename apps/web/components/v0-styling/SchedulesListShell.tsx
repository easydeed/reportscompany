"use client"

import { ScheduleTable } from "@repo/ui"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Calendar, Plus, Pause } from 'lucide-react'
import { PageHeader } from "@/components/page-header"
import { MetricCard } from "@/components/metric-card"
import { EmptyState } from "@/components/empty-state"

export type SchedulesListShellProps = {
  schedules: any[]
}

export function SchedulesListShell(props: SchedulesListShellProps) {
  const router = useRouter()
  const list = Array.isArray(props.schedules) ? props.schedules : []

  const handleEdit = (id: string) => {
    router.push(`/app/schedules/${id}/edit`)
  }

  const handleView = (id: string) => {
    router.push(`/app/schedules/${id}`)
  }

  const handleToggleActive = async (id: string, active: boolean) => {
    try {
      await fetch(`/api/proxy/v1/schedules/${id}`, {
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

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this schedule?")) return
    
    try {
      await fetch(`/api/proxy/v1/schedules/${id}`, {
        method: "DELETE",
        credentials: "include",
      })
      router.refresh()
    } catch (err) {
      console.error("Failed to delete schedule:", err)
    }
  }

  const activeCount = list.filter((s) => s?.active).length
  const pausedCount = list.filter((s) => !s?.active).length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Scheduled Reports"
        description="Automated report generation and delivery"
        action={
          <Button asChild>
            <Link href="/app/schedules/new">
              <Plus className="w-4 h-4 mr-2" />
              New Schedule
            </Link>
          </Button>
        }
      />

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          label="Total Schedules"
          value={list.length}
          icon={<Calendar className="w-4 h-4" />}
          index={0}
        />
        <MetricCard
          label="Active"
          value={activeCount}
          icon={<div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />}
          index={1}
        />
        <MetricCard
          label="Paused"
          value={pausedCount}
          icon={<Pause className="w-4 h-4" />}
          index={2}
        />
      </div>

      {list.length === 0 ? (
        <EmptyState
          icon={<Calendar className="w-6 h-6" />}
          title="No schedules yet"
          description="Set up automated report generation and delivery to keep your clients informed."
          action={{
            label: "Create Schedule",
            onClick: () => router.push("/app/schedules/new")
          }}
        />
      ) : (
        <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <h3 className="text-sm font-medium text-foreground">Your Schedules</h3>
            <span className="text-xs text-muted-foreground">
              {list.length} schedule{list.length === 1 ? "" : "s"} configured
            </span>
          </div>
          <ScheduleTable 
            schedules={list} 
            onEdit={handleEdit}
            onView={handleView}
            onToggleActive={handleToggleActive}
            onDelete={handleDelete}
          />
        </div>
      )}
    </div>
  )
}
