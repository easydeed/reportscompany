"use client"

import { EmptyState } from "@/components/empty-state"
import { Calendar } from "lucide-react"

export default function SchedulesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display font-bold text-3xl mb-2">Schedules</h1>
        <p className="text-muted-foreground">Automate report generation with scheduled tasks</p>
      </div>

      <EmptyState
        icon={<Calendar className="w-12 h-12" />}
        title="No schedules yet"
        description="Create automated schedules to generate reports on a recurring basis"
        actionLabel="Create Schedule"
        onAction={() => {}}
      />
    </div>
  )
}
