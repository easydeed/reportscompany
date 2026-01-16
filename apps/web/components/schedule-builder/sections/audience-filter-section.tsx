"use client"

import { Lightbulb } from "lucide-react"
import { cn } from "@/lib/utils"
import { AccordionSection } from "../accordion-section"
import type { AudienceFilter, SectionStatus } from "../types"

interface AudienceFilterSectionProps {
  value: AudienceFilter
  onChange: (value: AudienceFilter) => void
  isExpanded: boolean
  onToggle: () => void
}

const audienceOptions: { value: AudienceFilter; label: string; description: string }[] = [
  { value: "all", label: "All Listings", description: "No filters - show everything" },
  { value: "first_time", label: "First-Time Buyers", description: "2+ beds, 2+ baths, SFR, ≤70% median price" },
  { value: "luxury", label: "Luxury Clients", description: "SFR, ≥150% median price" },
  { value: "families", label: "Families", description: "3+ beds, 2+ baths, SFR" },
  { value: "condo", label: "Condo Buyers", description: "Condos only" },
  { value: "investors", label: "Investors", description: "≤50% median price" },
]

const audienceLabels: Record<string, string> = {
  all: "All Listings",
  first_time: "🎯 First-Time Buyers",
  luxury: "🎯 Luxury Clients",
  families: "🎯 Families",
  condo: "🎯 Condo Buyers",
  investors: "🎯 Investors",
}

export function AudienceFilterSection({ value, onChange, isExpanded, onToggle }: AudienceFilterSectionProps) {
  const status: SectionStatus = "optional"
  const summary = value ? audienceLabels[value] : undefined

  return (
    <AccordionSection
      title="Audience Filter"
      summary={summary}
      status={status}
      isExpanded={isExpanded}
      onToggle={onToggle}
    >
      <div className="space-y-4">
        <label className="text-sm text-muted-foreground">Target a specific audience (optional)</label>

        <div className="space-y-2">
          {audienceOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => onChange(option.value)}
              className={cn(
                "flex w-full items-center justify-between rounded-lg border-2 px-4 py-3 text-left transition-all",
                value === option.value ? "border-violet-500 bg-violet-50 dark:bg-violet-950/50" : "border-border hover:border-violet-300",
              )}
            >
              <div>
                <div className="font-medium">{option.label}</div>
                <div className="text-sm text-muted-foreground">{option.description}</div>
              </div>
              {value === option.value && <span className="text-violet-600">✓</span>}
            </button>
          ))}
        </div>

        <div className="flex items-start gap-2 rounded-lg bg-violet-50 px-3 py-2 text-sm text-violet-800 dark:bg-violet-950/50 dark:text-violet-300">
          <Lightbulb className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>Prices auto-adjust to local market. "70% of median" = ~$1.68M in Irvine, ~$350K in Riverside</span>
        </div>
      </div>
    </AccordionSection>
  )
}

