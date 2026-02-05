"use client"

import { Check } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ReportBuilderState, LookbackDays } from "../types"

interface LookbackSectionProps {
  lookbackDays: LookbackDays | null
  onChange: (updates: Partial<ReportBuilderState>) => void
  isComplete: boolean
  stepNumber?: number
}

const LOOKBACK_OPTIONS: LookbackDays[] = [7, 14, 30, 60, 90]

export function LookbackSection({ lookbackDays, onChange, isComplete, stepNumber = 3 }: LookbackSectionProps) {
  return (
    <section className={cn(
      "bg-white rounded-xl border transition-all duration-200",
      isComplete ? "border-gray-200 shadow-sm" : "border-gray-200/80 shadow-sm"
    )}>
      {/* Section Header */}
      <div className="flex items-center gap-3 px-5 py-4">
        <div className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors",
          isComplete
            ? "bg-emerald-500 text-white"
            : "bg-gray-100 text-gray-500"
        )}>
          {isComplete ? <Check className="w-3.5 h-3.5" /> : stepNumber}
        </div>
        <h3 className="text-sm font-medium text-gray-900">Lookback Period</h3>
      </div>

      <div className="px-5 pb-5">
        {/* Lookback Pills */}
        <div className="flex gap-2">
          {LOOKBACK_OPTIONS.map((days) => (
            <button
              key={days}
              onClick={() => onChange({ lookbackDays: days })}
              className={cn(
                "px-4 py-2 text-sm font-medium rounded-lg transition-all duration-150",
                lookbackDays === days
                  ? "bg-primary text-white shadow-sm shadow-primary/25"
                  : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:-translate-y-0.5 hover:shadow-sm"
              )}
            >
              {days}d
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
