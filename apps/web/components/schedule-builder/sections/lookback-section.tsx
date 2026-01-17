"use client"

import { Check } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ScheduleBuilderState } from "../types"

interface LookbackSectionProps {
  lookbackDays: ScheduleBuilderState["lookbackDays"]
  onChange: (updates: Partial<ScheduleBuilderState>) => void
  isComplete: boolean
}

const LOOKBACK_OPTIONS: NonNullable<ScheduleBuilderState["lookbackDays"]>[] = [7, 14, 30, 60, 90]

export function LookbackSection({ lookbackDays, onChange, isComplete }: LookbackSectionProps) {
  return (
    <section className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-900">Lookback Period</h3>
        {isComplete && (
          <div className="w-5 h-5 rounded-full bg-green-50 flex items-center justify-center">
            <Check className="w-3 h-3 text-green-500" />
          </div>
        )}
      </div>

      <div className="flex gap-2">
        {LOOKBACK_OPTIONS.map((days) => (
          <button
            key={days}
            onClick={() => onChange({ lookbackDays: days })}
            className={cn(
              "px-3 py-1.5 text-sm rounded-lg transition-colors",
              lookbackDays === days
                ? "bg-violet-600 text-white"
                : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
            )}
          >
            {days}d
          </button>
        ))}
      </div>
    </section>
  )
}

