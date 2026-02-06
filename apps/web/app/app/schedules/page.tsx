'use client'

import { SchedulesListShell } from "@/components/v0-styling/SchedulesListShell"
import { Skeleton } from "@/components/ui/skeleton"
import { useSchedules } from "@/hooks/use-api"

export default function SchedulesPage() {
  const { data, isLoading } = useSchedules()
  const schedules = Array.isArray(data)
    ? data
    : Array.isArray(data?.schedules)
    ? data.schedules
    : []

  if (isLoading) {
    return <SchedulesSkeleton />
  }

  return <SchedulesListShell schedules={schedules} />
}

function SchedulesSkeleton() {
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-7 w-48 mb-2" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="h-9 w-32 rounded-md" />
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-card border border-border rounded-xl p-4 shadow-[var(--shadow-card)]">
            <Skeleton className="h-3 w-20 mb-3" />
            <Skeleton className="h-7 w-16 mb-1" />
          </div>
        ))}
      </div>
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
        <div className="px-4 py-3 border-b border-border">
          <Skeleton className="h-4 w-32" />
        </div>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="px-4 py-3 border-b border-border/50 flex items-center gap-4">
            <Skeleton className="h-4 w-40 flex-1" />
            <Skeleton className="h-4 w-24 flex-1" />
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-8 w-8 rounded" />
          </div>
        ))}
      </div>
    </div>
  )
}
