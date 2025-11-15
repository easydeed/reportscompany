import { apiFetch } from "@/lib/api"
import { ScheduleTable } from "@repo/ui"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Calendar } from "lucide-react"

export default async function SchedulesPage() {
  let items: any[] = []
  
  try {
    items = await apiFetch("/v1/schedules")
  } catch (error) {
    console.error("Failed to fetch schedules:", error)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Schedules</h1>
          <p className="text-[var(--app-muted)] mt-1">
            Automated report generation and delivery
          </p>
        </div>
        <Link href="/app/schedules/new">
          <Button className="bg-[var(--app-primary)]">
            <Calendar className="w-4 h-4 mr-2" />
            New Schedule
          </Button>
        </Link>
      </div>

      {/* Schedules Card */}
      <Card>
        <CardHeader>
          <CardTitle>Your Schedules</CardTitle>
          <CardDescription>
            {items.length === 0 ? 'No schedules configured yet' : `${items.length} schedule${items.length === 1 ? '' : 's'} configured`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScheduleTable schedules={items || []} />
        </CardContent>
      </Card>
    </div>
  )
}
