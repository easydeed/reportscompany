import { apiFetch } from "@/lib/api"
import { ScheduleDetailShell } from "./schedule-detail-shell"

export default async function ScheduleDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  let item: any = null

  try {
    item = await apiFetch(`/v1/schedules/${id}`)
  } catch (error) {
    console.error("Failed to fetch schedule details:", error)
  }

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
