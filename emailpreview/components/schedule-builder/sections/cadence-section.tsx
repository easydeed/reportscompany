"use client"

import { useMemo } from "react"
import { Calendar } from "lucide-react"
import { cn } from "@/lib/utils"
import { AccordionSection } from "../accordion-section"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DAYS_OF_WEEK, DAY_NAMES, type ScheduleBuilderState } from "@/lib/schedule-types"

interface CadenceSectionProps {
  cadence: ScheduleBuilderState["cadence"]
  weeklyDow: ScheduleBuilderState["weeklyDow"]
  monthlyDom: number
  sendHour: number
  sendMinute: number
  timezone: string
  onCadenceChange: (value: ScheduleBuilderState["cadence"]) => void
  onWeeklyDowChange: (value: ScheduleBuilderState["weeklyDow"]) => void
  onMonthlyDomChange: (value: number) => void
  onSendHourChange: (value: number) => void
  onSendMinuteChange: (value: number) => void
  onTimezoneChange: (value: string) => void
}

const TIMEZONES = [
  { value: "America/Los_Angeles", label: "Pacific Time" },
  { value: "America/Denver", label: "Mountain Time" },
  { value: "America/Chicago", label: "Central Time" },
  { value: "America/New_York", label: "Eastern Time" },
]

export function CadenceSection({
  cadence,
  weeklyDow,
  monthlyDom,
  sendHour,
  sendMinute,
  timezone,
  onCadenceChange,
  onWeeklyDowChange,
  onMonthlyDomChange,
  onSendHourChange,
  onSendMinuteChange,
  onTimezoneChange,
}: CadenceSectionProps) {
  const summary = useMemo(() => {
    const timeStr = `${sendHour}:${sendMinute.toString().padStart(2, "0")} ${sendHour >= 12 ? "PM" : "AM"} PT`
    if (cadence === "weekly") {
      return `Every ${DAY_NAMES[weeklyDow]} at ${timeStr}`
    }
    return `Monthly on the ${monthlyDom}${getOrdinalSuffix(monthlyDom)} at ${timeStr}`
  }, [cadence, weeklyDow, monthlyDom, sendHour, sendMinute])

  const nextRunDate = useMemo(() => {
    const now = new Date()
    if (cadence === "weekly") {
      const daysUntil = (weeklyDow - now.getDay() + 7) % 7 || 7
      const nextDate = new Date(now)
      nextDate.setDate(now.getDate() + daysUntil)
      return `${DAY_NAMES[weeklyDow]}, ${nextDate.toLocaleDateString("en-US", { month: "long", day: "numeric" })} at ${sendHour}:${sendMinute.toString().padStart(2, "0")} AM PT`
    } else {
      const nextDate = new Date(now.getFullYear(), now.getMonth(), monthlyDom)
      if (nextDate <= now) {
        nextDate.setMonth(nextDate.getMonth() + 1)
      }
      return `${nextDate.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })} at ${sendHour}:${sendMinute.toString().padStart(2, "0")} AM PT`
    }
  }, [cadence, weeklyDow, monthlyDom, sendHour, sendMinute])

  return (
    <AccordionSection
      id="cadence"
      title="Cadence & Timing"
      status="complete"
      summary={summary}
      summaryIcon={<Calendar className="h-3.5 w-3.5" />}
    >
      <div className="space-y-6">
        {/* Frequency Toggle */}
        <div>
          <label className="text-sm text-muted-foreground mb-3 block">How often should this report be sent?</label>
          <div className="flex gap-3">
            <button
              onClick={() => onCadenceChange("weekly")}
              className={cn(
                "flex-1 py-2.5 px-4 rounded-lg border-2 font-medium text-sm transition-all",
                cadence === "weekly" ? "border-primary bg-primary/5" : "border-border hover:border-muted-foreground/30",
              )}
            >
              <div className="flex items-center justify-center gap-2">
                <div
                  className={cn(
                    "h-4 w-4 rounded-full border-2 flex items-center justify-center",
                    cadence === "weekly" ? "border-primary" : "border-muted-foreground/30",
                  )}
                >
                  {cadence === "weekly" && <div className="h-2 w-2 rounded-full bg-primary" />}
                </div>
                Weekly
              </div>
            </button>
            <button
              onClick={() => onCadenceChange("monthly")}
              className={cn(
                "flex-1 py-2.5 px-4 rounded-lg border-2 font-medium text-sm transition-all",
                cadence === "monthly"
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-muted-foreground/30",
              )}
            >
              <div className="flex items-center justify-center gap-2">
                <div
                  className={cn(
                    "h-4 w-4 rounded-full border-2 flex items-center justify-center",
                    cadence === "monthly" ? "border-primary" : "border-muted-foreground/30",
                  )}
                >
                  {cadence === "monthly" && <div className="h-2 w-2 rounded-full bg-primary" />}
                </div>
                Monthly
              </div>
            </button>
          </div>
        </div>

        {/* Day Selector */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-muted-foreground font-medium">
              {cadence === "weekly" ? "Day of Week" : "Day of Month"}
            </span>
            <div className="h-px flex-1 bg-border" />
          </div>

          {cadence === "weekly" ? (
            <div className="flex justify-between gap-1">
              {DAYS_OF_WEEK.map((day, index) => (
                <button
                  key={index}
                  onClick={() => onWeeklyDowChange(index as ScheduleBuilderState["weeklyDow"])}
                  className={cn(
                    "h-10 w-10 rounded-full text-sm font-medium transition-all",
                    weeklyDow === index ? "bg-primary text-primary-foreground" : "bg-muted hover:bg-muted/80",
                  )}
                >
                  {day}
                </button>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-7 gap-1">
              {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => (
                <button
                  key={day}
                  onClick={() => onMonthlyDomChange(day)}
                  className={cn(
                    "h-9 rounded-md text-sm font-medium transition-all",
                    monthlyDom === day ? "bg-primary text-primary-foreground" : "bg-muted hover:bg-muted/80",
                  )}
                >
                  {day}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Time Picker */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-muted-foreground font-medium">Time</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          <div className="flex items-center gap-2">
            <Select value={sendHour.toString()} onValueChange={(v) => onSendHourChange(Number.parseInt(v))}>
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

            <Select value={sendMinute.toString()} onValueChange={(v) => onSendMinuteChange(Number.parseInt(v))}>
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

            <Select value={timezone} onValueChange={onTimezoneChange}>
              <SelectTrigger className="flex-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TIMEZONES.map((tz) => (
                  <SelectItem key={tz.value} value={tz.value}>
                    {tz.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Next Run */}
        <div className="flex items-center gap-2 text-sm bg-muted/50 rounded-md p-3">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span className="text-muted-foreground">Next scheduled run:</span>
          <span className="font-medium">{nextRunDate}</span>
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
