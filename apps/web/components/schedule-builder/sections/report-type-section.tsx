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
}: ReportTypeSectionProps) {
  const handleTypeSelect = (type: ReportType) => {
    onChange({ reportType: type })
    // Reset audience filter when switching away from new_listings_gallery
    if (type !== "new_listings_gallery") {
      onAudienceChange(null, null)
    } else if (!audienceFilter) {
      // Default to "all" when selecting new listings
      onAudienceChange("all", "All Listings")
    }
  }

  const handleAudienceSelect = (preset: typeof AUDIENCE_PRESETS[0]) => {
    onAudienceChange(preset.id, preset.label)
  }

  const selectedAudience = AUDIENCE_PRESETS.find(p => p.id === audienceFilter)
  const showAudiencePills = reportType === "new_listings_gallery"

  return (
    <section className="bg-white border border-gray-200 rounded-lg p-4">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-900">Report Type</h3>
        {isComplete && (
          <div className="w-5 h-5 rounded-full bg-green-50 flex items-center justify-center">
            <Check className="w-3 h-3 text-green-500" />
          </div>
        )}
      </div>

      {/* 3 Report Type Cards */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {REPORT_TYPES.map((type) => {
          const isSelected = reportType === type.id
          const Icon = type.icon
          return (
            <button
              key={type.id}
              onClick={() => handleTypeSelect(type.id)}
              className={cn(
                "flex flex-col items-center p-3 rounded-lg border transition-colors text-center",
                isSelected
                  ? "bg-violet-50 border-2 border-violet-600"
                  : "bg-white border-gray-200 hover:border-gray-300"
              )}
            >
              <Icon className={cn(
                "w-6 h-6 mb-2",
                isSelected ? "text-violet-600" : "text-gray-400"
              )} />
              <span className={cn(
                "text-sm font-medium",
                isSelected ? "text-gray-900" : "text-gray-700"
              )}>
                {type.label}
              </span>
              <span className="text-xs text-gray-500 mt-0.5 leading-tight">
                {type.description}
              </span>
            </button>
          )
        })}
      </div>

      {/* Audience Pills - Only for New Listings */}
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
                    "inline-flex items-center gap-1 px-3 py-1.5 text-sm rounded-full transition-colors",
                    isSelected
                      ? "bg-violet-50 text-violet-700 border border-violet-200"
                      : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
                  )}
                >
                  {isSelected && <Check className="w-3 h-3" />}
                  {preset.label}
                </button>
              )
            })}
          </div>
          {/* Hint text showing filter criteria */}
          {selectedAudience && selectedAudience.id !== "all" && (
            <p className="text-xs text-gray-400 mt-2">
              {selectedAudience.description}
            </p>
          )}
        </div>
      )}
    </section>
  )
}
