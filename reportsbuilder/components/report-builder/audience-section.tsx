"use client"

import { cn } from "@/lib/utils"
import type { ReportBuilderState, AudienceFilter } from "@/components/report-builder"

interface AudienceSectionProps {
  state: ReportBuilderState
  updateState: <K extends keyof ReportBuilderState>(key: K, value: ReportBuilderState[K]) => void
}

const audienceOptions: { value: AudienceFilter; label: string; description: string }[] = [
  { value: "all", label: "All Listings", description: "No filters - show everything" },
  { value: "first_time", label: "First-Time Buyers", description: "2+ beds, 2+ baths, SFR, ≤70% median price" },
  { value: "luxury", label: "Luxury Clients", description: "SFR, ≥150% median price" },
  { value: "families", label: "Families", description: "3+ beds, 2+ baths, SFR" },
  { value: "condo", label: "Condo Buyers", description: "Condos only" },
  { value: "investors", label: "Investors", description: "≤50% median price" },
]

export function AudienceSection({ state, updateState }: AudienceSectionProps) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Target a specific audience (optional)</p>

      <div className="divide-y rounded-lg border">
        {audienceOptions.map((option) => {
          const isSelected = state.audienceFilter === option.value

          return (
            <button
              key={option.value}
              onClick={() => updateState("audienceFilter", option.value)}
              className={cn(
                "flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-muted/50",
                isSelected && "bg-violet-50",
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
                  <p className={cn("font-medium text-sm", isSelected && "text-violet-900")}>{option.label}</p>
                  <p className="text-xs text-muted-foreground">{option.description}</p>
                </div>
              </div>
              {isSelected && option.value !== "all" && <span className="text-violet-500">✓</span>}
            </button>
          )
        })}
      </div>
    </div>
  )
}
