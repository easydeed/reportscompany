"use client"

import { Target, Check } from "lucide-react"
import { cn } from "@/lib/utils"
import { AccordionSection } from "../accordion-section"
import { AUDIENCE_FILTERS, type AudienceFilter } from "@/lib/schedule-types"

interface AudienceFilterSectionProps {
  value: AudienceFilter
  onChange: (filter: AudienceFilter, name: string | null) => void
}

export function AudienceFilterSection({ value, onChange }: AudienceFilterSectionProps) {
  const status = value && value !== "all" ? "complete" : "optional"
  const selectedFilter = AUDIENCE_FILTERS.find((f) => f.id === value)
  const summary = value && value !== "all" ? selectedFilter?.name : undefined

  return (
    <AccordionSection
      id="audience"
      title="Audience Filter"
      status={status}
      summary={summary}
      summaryIcon={summary ? <Target className="h-3.5 w-3.5" /> : undefined}
    >
      <div className="space-y-4">
        <label className="text-sm text-muted-foreground block">Target a specific audience (optional)</label>

        <div className="border rounded-lg overflow-hidden divide-y">
          {AUDIENCE_FILTERS.map((filter) => (
            <button
              key={filter.id}
              onClick={() => onChange(filter.id, filter.id === "all" ? null : filter.name)}
              className={cn(
                "w-full flex items-center justify-between p-3 text-left transition-colors",
                value === filter.id ? "bg-primary/5" : "hover:bg-muted/50",
              )}
            >
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "h-4 w-4 rounded-full border-2 flex items-center justify-center",
                    value === filter.id ? "border-primary bg-primary" : "border-muted-foreground/30",
                  )}
                >
                  {value === filter.id && <div className="h-1.5 w-1.5 rounded-full bg-white" />}
                </div>
                <div>
                  <div className="font-medium text-sm">{filter.name}</div>
                  <div className="text-xs text-muted-foreground">{filter.description}</div>
                </div>
              </div>
              {value === filter.id && <Check className="h-4 w-4 text-primary" />}
            </button>
          ))}
        </div>
      </div>
    </AccordionSection>
  )
}
