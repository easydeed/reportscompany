import { ScheduleTable } from "@repo/ui"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Calendar, Plus } from 'lucide-react'

export type SchedulesListShellProps = {
  schedules: any[] // Accept any[] since we're just passing through to ScheduleTable
}

export function SchedulesListShell(props: SchedulesListShellProps) {
  const list = Array.isArray(props.schedules) ? props.schedules : []

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-display font-bold tracking-tight text-slate-900">
              Schedules
            </h1>
            <p className="text-slate-600 mt-1.5 text-[15px]">
              Automated report generation and delivery
            </p>
          </div>
          <Link href="/app/schedules/new">
            <Button 
              className="bg-gradient-to-r from-violet-600 to-violet-700 hover:from-violet-700 hover:to-violet-800 text-white shadow-md hover:shadow-lg transition-all duration-200"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Schedule
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="border-slate-200 bg-white shadow-sm hover:shadow-md transition-shadow duration-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600 mb-1">Total Schedules</p>
                  <p className="text-3xl font-display font-bold text-slate-900">
                    {list.length}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-violet-100 flex items-center justify-center">
                  <Calendar className="w-6 h-6 text-violet-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm hover:shadow-md transition-shadow duration-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600 mb-1">Active</p>
                  <p className="text-3xl font-display font-bold text-green-600">
                    {list.filter((s) => s?.active).length}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center">
                  <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm hover:shadow-md transition-shadow duration-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600 mb-1">Paused</p>
                  <p className="text-3xl font-display font-bold text-slate-400">
                    {list.filter((s) => !s?.active).length}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center">
                  <div className="w-3 h-3 rounded-full bg-slate-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="border-slate-200 bg-white shadow-sm">
          <CardHeader className="border-b border-slate-100">
            <CardTitle className="text-lg font-semibold text-slate-900">
              Your Schedules
            </CardTitle>
            <CardDescription className="text-slate-600">
              {list.length === 0
                ? "No schedules configured yet"
                : `${list.length} schedule${list.length === 1 ? "" : "s"} configured`}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <ScheduleTable schedules={list} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
