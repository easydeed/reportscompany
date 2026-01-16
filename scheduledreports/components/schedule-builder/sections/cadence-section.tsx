"use client"

import { Calendar } from "lucide-react"
import { cn } from "@/lib/utils"
import { AccordionSection } from "../accordion-section"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { ScheduleBuilderState } from "../types"

interface CadenceSectionProps {
  cadence: ScheduleBuilderState["cadence"]
  weeklyDow: ScheduleBuilderState["weeklyDow"]
  monthlyDom: number
  sendHour: number
  sendMinute: number
  timezone: string
  onChange: (updates: Partial<ScheduleBuilderState>) => void
  isExpanded: boolean
  onToggle: () => void
}

const dayNames = ["S", "M", "T", "W", "T", "F", "S"]
const fullDayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
const timezones = [
  { value: "America/Los_Angeles", label: "Pacific Time (PT)" },
  { value: "America/Denver", label: "Mountain Time (MT)" },
  { value: "America/Chicago", label: "Central Time (CT)" },
  { value: "America/New_York", label: "Eastern Time (ET)" },
]

export function CadenceSection({
  cadence,
  weeklyDow,
  monthlyDom,
  sendHour,
  sendMinute,
  timezone,
  onChange,
  isExpanded,
  onToggle,
}: CadenceSectionProps) {
  const timezoneShort =
    timezone === "America/Los_Angeles"
      ? "PT"
      : timezone === "America/New_York"
        ? "ET"
        : timezone === "America/Chicago"
          ? "CT"
          : "MT"

  const summary =
    cadence === "weekly"
      ? `📅 Every ${fullDayNames[weeklyDow]} at ${sendHour.toString().padStart(2, "0")}:${sendMinute.toString().padStart(2, "0")} ${timezoneShort}`
      : `📅 Monthly on the ${monthlyDom}${getOrdinalSuffix(monthlyDom)} at ${sendHour.toString().padStart(2, "0")}:${sendMinute.toString().padStart(2, "0")} ${timezoneShort}`

  // Calculate next scheduled run
  const nextRun = getNextRunDate(cadence, weeklyDow, monthlyDom, sendHour, sendMinute, timezoneShort)

  return (
    <AccordionSection
      title="Cadence & Timing"
      summary={summary}
      status="complete"
      isExpanded={isExpanded}
      onToggle={onToggle}
    >
      <div className="space-y-6">
        <div>
          <label className="text-sm text-muted-foreground">How often should this report be sent?</label>
          <div className="mt-3 flex gap-3">
            <button
              onClick={() => onChange({ cadence: "weekly" })}
              className={cn(
                "flex-1 rounded-lg border-2 px-4 py-3 font-medium transition-all",
                cadence === "weekly"
                  ? "border-violet-500 bg-violet-50 text-violet-700"
                  : "border-border hover:border-violet-300",
              )}
            >
              Weekly
            </button>
            <button
              onClick={() => onChange({ cadence: "monthly" })}
              className={cn(
                "flex-1 rounded-lg border-2 px-4 py-3 font-medium transition-all",
                cadence === "monthly"
                  ? "border-violet-500 bg-violet-50 text-violet-700"
                  : "border-border hover:border-violet-300",
              )}
            >
              Monthly
            </button>
          </div>
        </div>

        {/* Day Selector */}
        {cadence === "weekly" ? (
          <div>
            <div className="mb-3 flex items-center gap-2 text-xs text-muted-foreground">
              <div className="h-px flex-1 bg-border" />
              <span>Day of Week</span>
              <div className="h-px flex-1 bg-border" />
            </div>
            <div className="flex gap-2">
              {dayNames.map((day, index) => (
                <button
                  key={index}
                  onClick={() => onChange({ weeklyDow: index as ScheduleBuilderState["weeklyDow"] })}
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-full text-sm font-medium transition-all",
                    weeklyDow === index ? "bg-violet-600 text-white" : "bg-muted hover:bg-violet-100",
                  )}
                >
                  {day}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div>
            <div className="mb-3 flex items-center gap-2 text-xs text-muted-foreground">
              <div className="h-px flex-1 bg-border" />
              <span>Day of Month</span>
              <div className="h-px flex-1 bg-border" />
            </div>
            <div className="grid grid-cols-7 gap-2">
              {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => (
                <button
                  key={day}
                  onClick={() => onChange({ monthlyDom: day })}
                  className={cn(
                    "flex h-9 w-9 items-center justify-center rounded text-sm font-medium transition-all",
                    monthlyDom === day ? "bg-violet-600 text-white" : "bg-muted hover:bg-violet-100",
                  )}
                >
                  {day}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Time Picker */}
        <div>
          <div className="mb-3 flex items-center gap-2 text-xs text-muted-foreground">
            <div className="h-px flex-1 bg-border" />
            <span>Time</span>
            <div className="h-px flex-1 bg-border" />
          </div>
          <div className="flex items-center gap-3">
            <Select value={sendHour.toString()} onValueChange={(v) => onChange({ sendHour: Number.parseInt(v) })}>
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Array.from({ length: 24 }, (_, i) => (
                  <SelectItem key={i} value={i.toString()}>
                    {i.toString().padStart(2, "0")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <span className="text-lg font-medium">:</span>
            <Select value={sendMinute.toString()} onValueChange={(v) => onChange({ sendMinute: Number.parseInt(v) })}>
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[0, 15, 30, 45].map((m) => (
                  <SelectItem key={m} value={m.toString()}>
                    {m.toString().padStart(2, "0")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={timezone} onValueChange={(v) => onChange({ timezone: v })}>
              <SelectTrigger className="flex-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {timezones.map((tz) => (
                  <SelectItem key={tz.value} value={tz.value}>
                    {tz.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Next Run Display */}
        <div className="flex items-center gap-2 rounded-lg bg-violet-50 px-3 py-2 text-sm text-violet-800">
          <Calendar className="h-4 w-4" />
          <span>Next scheduled run: {nextRun}</span>
        </div>
      </div>
    </AccordionSection>
  )
}

function getOrdinalSuffix(n: number): string {
  const s = ["th", "st", "nd", "rd"]
  const v = n % 100
  return s[(v - 20) % 10] || s[v] || s[0]
}

function getNextRunDate(
  cadence: string,
  weeklyDow: number,
  monthlyDom: number,
  hour: number,
  minute: number,
  tzShort: string,
): string {
  const now = new Date()
  const targetDate = new Date(now)

  if (cadence === "weekly") {
    const currentDay = now.getDay()
    const daysUntilTarget = (weeklyDow - currentDay + 7) % 7 || 7
    targetDate.setDate(now.getDate() + daysUntilTarget)
  } else {
    if (now.getDate() >= monthlyDom) {
      targetDate.setMonth(now.getMonth() + 1)
    }
    targetDate.setDate(monthlyDom)
  }

  const dateStr = targetDate.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  })

  return `${dateStr} at ${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")} ${tzShort}`
}
