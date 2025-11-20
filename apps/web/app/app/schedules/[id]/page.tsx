import { apiFetch } from "@/lib/api"
import { ScheduleDetail } from "@repo/ui"

export default async function ScheduleDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  let item: any = null
  let runs: any[] = []

  try {
    const items = await apiFetch("/v1/schedules")
    item = (items || []).find((x: any) => x.id === id)
    
    if (item) {
      runs = await apiFetch(`/v1/schedules/${id}/runs`)
    }
  } catch (error) {
    console.error("Failed to fetch schedule details:", error)
  }

  if (!item) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-slate-400">Schedule not found</h2>
        <a href="/app/schedules" className="text-[#22D3EE] hover:underline mt-4 inline-block">
          ← Back to Schedules
        </a>
      </div>
    )
  }

  return (
    <div>
      <ScheduleDetail schedule={item} runs={runs || []} />
    </div>
  )
}
