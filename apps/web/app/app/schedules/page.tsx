import { apiFetch } from "@/lib/api"
import { ScheduleTable } from "@repo/ui"

export default async function SchedulesPage() {
  let items: any[] = []
  
  try {
    items = await apiFetch("/v1/schedules")
  } catch (error) {
    console.error("Failed to fetch schedules:", error)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Schedules</h1>
        <a
          href="/app/schedules/new"
          className="inline-flex items-center px-4 py-2 bg-[#22D3EE] text-slate-900 rounded-lg hover:bg-[#06B6D4] transition-colors font-medium"
        >
          New Schedule
        </a>
      </div>
      <ScheduleTable schedules={items || []} />
    </div>
  )
}
