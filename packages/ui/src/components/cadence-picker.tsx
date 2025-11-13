"use client"

import { cn } from "../lib/utils"
import { Label } from "./ui/label"
import { RadioGroup, RadioGroupItem } from "./ui/radio-group"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"
import { TimePicker } from "./time-picker"

type Cadence = "weekly" | "monthly"

interface CadencePickerProps {
  cadence: Cadence
  onCadenceChange: (cadence: Cadence) => void
  weekday?: string
  onWeekdayChange?: (weekday: string) => void
  monthDay?: number
  onMonthDayChange?: (day: number) => void
  time: string
  onTimeChange: (time: string) => void
  className?: string
}

const weekdays = [
  { value: "monday", label: "Monday" },
  { value: "tuesday", label: "Tuesday" },
  { value: "wednesday", label: "Wednesday" },
  { value: "thursday", label: "Thursday" },
  { value: "friday", label: "Friday" },
  { value: "saturday", label: "Saturday" },
  { value: "sunday", label: "Sunday" },
]

export function CadencePicker({
  cadence,
  onCadenceChange,
  weekday = "monday",
  onWeekdayChange,
  monthDay = 1,
  onMonthDayChange,
  time,
  onTimeChange,
  className,
}: CadencePickerProps) {
  return (
    <div className={cn("space-y-6", className)}>
      <RadioGroup value={cadence} onValueChange={(value) => onCadenceChange(value as Cadence)}>
        <div className="space-y-4">
          <div className="flex items-start space-x-3">
            <RadioGroupItem value="weekly" id="weekly" className="mt-1" />
            <div className="flex-1 space-y-3">
              <Label htmlFor="weekly" className="text-base font-medium cursor-pointer">
                Weekly
              </Label>
              {cadence === "weekly" && (
                <div className="space-y-3 pl-1">
                  <div className="space-y-2">
                    <Label htmlFor="weekday" className="text-sm text-muted-foreground">
                      Day of week
                    </Label>
                    <Select value={weekday} onValueChange={onWeekdayChange}>
                      <SelectTrigger id="weekday" className="w-full max-w-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {weekdays.map((day) => (
                          <SelectItem key={day.value} value={day.value}>
                            {day.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <RadioGroupItem value="monthly" id="monthly" className="mt-1" />
            <div className="flex-1 space-y-3">
              <Label htmlFor="monthly" className="text-base font-medium cursor-pointer">
                Monthly
              </Label>
              {cadence === "monthly" && (
                <div className="space-y-3 pl-1">
                  <div className="space-y-2">
                    <Label htmlFor="monthday" className="text-sm text-muted-foreground">
                      Day of month
                    </Label>
                    <Select
                      value={monthDay.toString()}
                      onValueChange={(value) => onMonthDayChange?.(Number.parseInt(value))}
                    >
                      <SelectTrigger id="monthday" className="w-full max-w-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => (
                          <SelectItem key={day} value={day.toString()}>
                            {day}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </RadioGroup>

      <div className="space-y-2">
        <Label htmlFor="time" className="text-sm text-muted-foreground">
          Time (24-hour format)
        </Label>
        <TimePicker value={time} onChange={onTimeChange} />
      </div>
    </div>
  )
}
