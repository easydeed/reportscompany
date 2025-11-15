import { ScheduleTable } from "@repo/ui"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Calendar } from "lucide-react"

export type ScheduleRow = {
  id: string;
  name: string;
  report_type: string;
  city: string;
  cadence: string;
  next_run_at: string | null;
  active: boolean;
};

export type SchedulesListShellProps = {
  schedules: ScheduleRow[];
};

export function SchedulesListShell(props: SchedulesListShellProps) {
  const { schedules } = props;

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
            {schedules.length === 0 ? 'No schedules configured yet' : `${schedules.length} schedule${schedules.length === 1 ? '' : 's'} configured`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScheduleTable schedules={schedules} />
        </CardContent>
      </Card>
    </div>
  );
}

