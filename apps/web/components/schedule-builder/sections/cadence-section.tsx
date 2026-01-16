"use client"

import { Check, Calendar, Clock } from "lucide-react"
import { cn } from "@/lib/utils"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { ScheduleBuilderState } from "../types"

interface CadenceSectionProps {
  cadence: ScheduleBuilderState["cadence"]
  weeklyDow: ScheduleBuilderState["weeklyDow"]
  monthlyDom: ScheduleBuilderState["monthlyDom"]
  sendHour: number
  sendMinute: number
  timezone: string
  onChange: (updates: Partial<ScheduleBuilderState>) => void
  isComplete: boolean
}

const DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
const HOURS = Array.from({ length: 24 }, (_, i) => i)
const TIMEZONES = [
  { value: "America/Los_Angeles", label: "Pacific" },
  { value: "America/Denver", label: "Mountain" },
  { value: "America/Chicago", label: "Central" },
  { value: "America/New_York", label: "Eastern" },
]

export function CadenceSection({
  cadence,
  weeklyDow,
  monthlyDom,
  sendHour,
  sendMinute,
  timezone,
  onChange,
  isComplete,
}: CadenceSectionProps) {
  const formatHour = (h: number) => {
    const ampm = h >= 12 ? "PM" : "AM"
    const hour12 = h % 12 || 12
    return `${hour12}:00 ${ampm}`
  }

  return (
    <section className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-900">Cadence</h3>
        {isComplete && (
          <div className="w-5 h-5 rounded-full bg-green-50 flex items-center justify-center">
            <Check className="w-3 h-3 text-green-500" />
          </div>
        )}
      </div>

      {/* Frequency Toggle */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => onChange({ cadence: "weekly" })}
          className={cn(
            "flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors",
            cadence === "weekly"
              ? "bg-violet-50 border-violet-600 text-violet-700"
              : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
          )}
        >
          <Calendar className="w-4 h-4" />
          Weekly
        </button>
        <button
          onClick={() => onChange({ cadence: "monthly" })}
          className={cn(
            "flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors",
            cadence === "monthly"
              ? "bg-violet-50 border-violet-600 text-violet-700"
              : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
          )}
        >
          <Calendar className="w-4 h-4" />
          Monthly
        </button>
      </div>

      {/* Timing Dropdowns */}
      <div className="flex items-center gap-2 flex-wrap">
        {cadence === "weekly" ? (
          <Select value={weeklyDow.toString()} onValueChange={(v) => onChange({ weeklyDow: parseInt(v) as any })}>
            <SelectTrigger className="w-28 h-9 text-sm border-gray-200">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DAYS_OF_WEEK.map((day, i) => (
                <SelectItem key={i} value={i.toString()}>{day}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <Select value={monthlyDom.toString()} onValueChange={(v) => onChange({ monthlyDom: parseInt(v) })}>
            <SelectTrigger className="w-20 h-9 text-sm border-gray-200">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => (
                <SelectItem key={day} value={day.toString()}>Day {day}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        <span className="text-gray-400 text-sm">at</span>

        <Select value={sendHour.toString()} onValueChange={(v) => onChange({ sendHour: parseInt(v) })}>
          <SelectTrigger className="w-24 h-9 text-sm border-gray-200">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {HOURS.map((h) => (
              <SelectItem key={h} value={h.toString()}>{formatHour(h)}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={timezone} onValueChange={(v) => onChange({ timezone: v })}>
          <SelectTrigger className="w-24 h-9 text-sm border-gray-200">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {TIMEZONES.map((tz) => (
              <SelectItem key={tz.value} value={tz.value}>{tz.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </section>
  )
}
