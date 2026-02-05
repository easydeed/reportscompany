"use client"

import { Images, BarChart3, Home, Check } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ScheduleBuilderState, ReportType, AudienceFilter } from "../types"

interface ReportTypeSectionProps {
  reportType: ReportType | null
  audienceFilter: AudienceFilter
  audienceFilterName: string | null
  onChange: (updates: Partial<ScheduleBuilderState>) => void
  onAudienceChange: (filter: AudienceFilter, name: string | null) => void
  isComplete: boolean
  stepNumber?: number
}

// Only 3 report types as per design system
const REPORT_TYPES = [
  { 
    id: "new_listings_gallery" as const, 
    label: "New Listings", 
    description: "Photo gallery of new homes",
    icon: Images 
  },
  { 
    id: "market_snapshot" as const, 
    label: "Market Update", 
    description: "Stats & trends for the area",
    icon: BarChart3 
  },
  { 
    id: "closed" as const, 
    label: "Closed Sales", 
    description: "Recent sales in the area",
    icon: Home 
  },
]

// Audience presets - only shown for New Listings
const AUDIENCE_PRESETS = [
  { id: "all" as const, label: "All Listings", description: "No filters" },
  { id: "first_time" as const, label: "First-Time Buyers", description: "2+ beds, 2+ baths, SFR, ≤70% median" },
  { id: "luxury" as const, label: "Luxury Clients", description: "SFR, ≥150% median" },
  { id: "families" as const, label: "Families", description: "3+ beds, 2+ baths, SFR" },
  { id: "condo" as const, label: "Condo Buyers", description: "Condos only" },
  { id: "investors" as const, label: "Investors", description: "≤50% median" },
]

export function ReportTypeSection({
  reportType,
  audienceFilter,
  audienceFilterName,
  onChange,
  onAudienceChange,
  isComplete,
  stepNumber = 2,
}: ReportTypeSectionProps) {
  const handleTypeSelect = (type: ReportType) => {
    onChange({ reportType: type })
    if (type !== "new_listings_gallery") {
      onAudienceChange(null, null)
    } else if (!audienceFilter) {
      onAudienceChange("all", "All Listings")
    }
  }

  const handleAudienceSelect = (preset: typeof AUDIENCE_PRESETS[0]) => {
    onAudienceChange(preset.id, preset.label)
  }

  const selectedAudience = AUDIENCE_PRESETS.find(p => p.id === audienceFilter)
  const showAudiencePills = reportType === "new_listings_gallery"

  return (
    <section className={cn(
      "bg-white rounded-xl border transition-all duration-200",
      isComplete ? "border-gray-200 shadow-sm" : "border-gray-200/80 shadow-sm"
    )}>
      <div className="flex items-center gap-3 px-5 py-4">
        <div className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors",
          isComplete ? "bg-emerald-500 text-white" : "bg-gray-100 text-gray-500"
        )}>
          {isComplete ? <Check className="w-3.5 h-3.5" /> : stepNumber}
        </div>
        <h3 className="text-sm font-medium text-gray-900">Report Type</h3>
      </div>

      <div className="px-5 pb-5">
        <div className="grid grid-cols-3 gap-3 mb-4">
          {REPORT_TYPES.map((type) => {
            const isSelected = reportType === type.id
            const Icon = type.icon
            return (
              <button
                key={type.id}
                onClick={() => handleTypeSelect(type.id)}
                className={cn(
                  "group relative flex flex-col items-center p-4 rounded-xl border-2 transition-all duration-150 text-center",
                  isSelected
                    ? "bg-primary/5 border-primary shadow-sm shadow-primary/10"
                    : "bg-white border-transparent shadow-sm hover:shadow-md hover:-translate-y-0.5"
                )}
              >
                <div className={cn(
                  "w-10 h-10 rounded-lg flex items-center justify-center mb-2.5 transition-colors",
                  isSelected ? "bg-primary/10" : "bg-gray-50 group-hover:bg-gray-100"
                )}>
                  <Icon className={cn(
                    "w-5 h-5 transition-colors",
                    isSelected ? "text-primary" : "text-gray-400 group-hover:text-gray-600"
                  )} />
                </div>
                <span className={cn(
                  "text-sm font-medium transition-colors",
                  isSelected ? "text-foreground" : "text-gray-600"
                )}>
                  {type.label}
                </span>
                <span className="text-xs text-gray-400 mt-0.5 leading-tight">
                  {type.description}
                </span>
                {isSelected && (
                  <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-primary" />
                )}
              </button>
            )
          })}
        </div>

        {showAudiencePills && (
          <div className="pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-500 mb-2">Target audience (optional)</p>
            <div className="flex flex-wrap gap-2">
              {AUDIENCE_PRESETS.map((preset) => {
                const isSelected = audienceFilter === preset.id
                return (
                  <button
                    key={preset.id}
                    onClick={() => handleAudienceSelect(preset)}
                    className={cn(
                      "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full border transition-all duration-150",
                      isSelected
                        ? "bg-primary/10 text-primary border-primary/20 shadow-sm shadow-primary/5"
                        : "bg-white text-gray-500 border-gray-200 hover:border-gray-300 hover:text-gray-700"
                    )}
                  >
                    {isSelected && <Check className="w-3 h-3" strokeWidth={2.5} />}
                    {preset.label}
                  </button>
                )
              })}
            </div>
            {selectedAudience && selectedAudience.id !== "all" && (
              <p className="text-xs text-gray-400 mt-2">{selectedAudience.description}</p>
            )}
          </div>
        )}
      </div>
    </section>
  )
}
