"use client"

import { cn } from "@/lib/utils"
import type { ReportBuilderState, ReportType, LookbackDays } from "../types"
import { REPORT_TYPE_CONFIG, LOOKBACK_OPTIONS } from "../types"

interface ReportTypeSectionProps {
  reportType: ReportType
  lookbackDays: LookbackDays
  onChange: (updates: Partial<ReportBuilderState>) => void
}

const reportTypes: ReportType[] = [
  "market_snapshot",
  "new_listings_gallery",
  "closed",
  "inventory",
  "price_bands",
  "open_houses",
]

export function ReportTypeSection({ reportType, lookbackDays, onChange }: ReportTypeSectionProps) {
  return (
    <div className="space-y-6">
      <div>
        <p className="mb-4 text-sm text-muted-foreground">What type of report do you want to create?</p>
        <div className="grid grid-cols-3 gap-3">
          {reportTypes.map((type) => {
            const config = REPORT_TYPE_CONFIG[type]
            const Icon = config.icon
            const isSelected = reportType === type

            return (
              <button
                key={type}
                onClick={() => onChange({ reportType: type })}
                className={cn(
                  "relative flex flex-col items-center gap-2 rounded-xl border-2 p-4 text-center transition-all",
                  isSelected
                    ? "border-violet-500 bg-violet-50 dark:bg-violet-950/30"
                    : "border-border hover:border-violet-200 hover:bg-muted/50",
                )}
              >
                {isSelected && (
                  <div className="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full bg-violet-500 text-white">
                    <svg className="h-3 w-3" viewBox="0 0 12 12" fill="none">
                      <path
                        d="M2 6L5 9L10 3"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                )}
                <Icon className={cn("h-6 w-6", isSelected ? "text-violet-600" : "text-muted-foreground")} />
                <div>
                  <p className="font-medium text-sm">{config.label}</p>
                  <p className={cn("text-xs", isSelected ? "text-violet-600" : "text-muted-foreground")}>
                    {config.description}
                  </p>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      <div className="border-t pt-6">
        <p className="mb-3 text-sm font-medium text-muted-foreground">Lookback Period</p>
        <p className="mb-4 text-sm text-muted-foreground">How far back should the report look for data?</p>
        <div className="flex flex-wrap gap-2">
          {LOOKBACK_OPTIONS.map((days) => (
            <button
              key={days}
              onClick={() => onChange({ lookbackDays: days })}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                lookbackDays === days
                  ? "bg-violet-600 text-white"
                  : "bg-muted hover:bg-muted/80"
              )}
            >
              {days} days
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

