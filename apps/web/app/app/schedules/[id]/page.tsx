import { createServerApi } from "@/lib/api-server"
import type { Schedule } from "@/components/schedules/types"
import { ScheduleDetailShell } from "./schedule-detail-shell"

export default async function ScheduleDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const api = await createServerApi()
  const { data: item } = await api.get<Schedule>(`/v1/schedules/${encodeURIComponent(id)}`)

  if (!item) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-muted-foreground">Schedule not found</h2>
        <a href="/app/schedules" className="text-primary hover:underline mt-4 inline-block">
          &larr; Back to Schedules
        </a>
      </div>
    )
  }

  return <ScheduleDetailShell schedule={item} />
}
