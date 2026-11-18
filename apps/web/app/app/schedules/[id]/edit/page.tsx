import Link from "next/link"
import { ScheduleBuilder } from "@/components/schedule-builder"
import type { StoredSchedule } from "@/components/schedule-builder/edit-state"
import { createServerApi } from "@/lib/api-server"

interface PageProps {
  params: Promise<{ id: string }>
}

export default async function EditSchedulePage({ params }: PageProps) {
  const { id } = await params
  const api = await createServerApi()
  const { data, status } = await api.get<StoredSchedule>(`/v1/schedules/${encodeURIComponent(id)}`)
  if (!data || data.id !== id || typeof data.active !== "boolean" || !Array.isArray(data.resolved_recipients)) {
    return (
      <main className="mx-auto max-w-xl space-y-4 p-8">
        <h1 className="text-xl font-semibold">{status === 404 ? "Schedule not found" : "Couldn’t load this schedule"}</h1>
        <Link href="/app/schedules" className="text-primary underline">Back to schedules</Link>
      </main>
    )
  }
  return <ScheduleBuilder key={id} schedule={data} />
}
