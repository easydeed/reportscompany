"use client"

import { Lightbulb } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ReportBuilderState, AudienceFilter } from "../types"
import { AUDIENCE_FILTERS } from "../types"

interface AudienceSectionProps {
  audienceFilter: AudienceFilter
  onChange: (updates: Partial<ReportBuilderState>) => void
}

export function AudienceSection({ audienceFilter, onChange }: AudienceSectionProps) {
  const handleChange = (value: AudienceFilter) => {
    const filter = AUDIENCE_FILTERS.find(f => f.value === value)
    const filterName = value && value !== "all" ? (filter?.label || null) : null
    onChange({ audienceFilter: value, audienceFilterName: filterName })
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Target a specific audience (optional)</p>

      <div className="divide-y rounded-lg border">
        {AUDIENCE_FILTERS.map((option) => {
          const isSelected = audienceFilter === option.value

          return (
            <button
              key={option.value}
              onClick={() => handleChange(option.value)}
              className={cn(
                "flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-muted/50",
                isSelected && "bg-violet-50 dark:bg-violet-950/30",
              )}
            >
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "flex h-4 w-4 items-center justify-center rounded-full border-2",
                    isSelected ? "border-violet-500 bg-violet-500" : "border-muted-foreground/30",
                  )}
                >
                  {isSelected && <div className="h-1.5 w-1.5 rounded-full bg-white" />}
                </div>
                <div>
                  <p className={cn("font-medium text-sm", isSelected && "text-violet-900 dark:text-violet-100")}>
                    {option.label}
                  </p>
                  <p className="text-xs text-muted-foreground">{option.description}</p>
                </div>
              </div>
              {isSelected && option.value !== "all" && <span className="text-violet-500">✓</span>}
            </button>
          )
        })}
      </div>

      <div className="flex items-start gap-2 rounded-lg bg-violet-50 px-3 py-2 text-sm text-violet-800 dark:bg-violet-950/50 dark:text-violet-300">
        <Lightbulb className="mt-0.5 h-4 w-4 flex-shrink-0" />
        <span>Prices auto-adjust to local market. "70% of median" = ~$1.68M in Irvine, ~$350K in Riverside</span>
      </div>
    </div>
  )
}

