"use client"

import { cn } from "@/lib/utils"
import { AccordionSection } from "../accordion-section"
import type { ReportType, ScheduleBuilderState } from "../types"

interface ReportTypeSectionProps {
  stepNumber?: number
  reportType: ReportType
  lookbackDays: ScheduleBuilderState["lookbackDays"]
  onChange: (updates: Partial<ScheduleBuilderState>) => void
  isExpanded: boolean
  onToggle: () => void
}

const mainReportTypes: { value: ReportType; icon: string; label: string; description: string }[] = [
  { value: "new_listings_gallery", icon: "📸", label: "New Listings", description: "Photo gallery of new homes" },
  { value: "market_snapshot", icon: "📊", label: "Market Update", description: "Stats & trends for the area" },
  { value: "closed", icon: "🏠", label: "Closed Sales", description: "Recently sold properties" },
]

const moreReportTypes: { value: ReportType; icon: string; label: string }[] = [
  { value: "inventory", icon: "📦", label: "Inventory" },
  { value: "price_bands", icon: "💰", label: "Price Bands" },
  { value: "open_houses", icon: "🚪", label: "Open Houses" },
]

const lookbackOptions: ScheduleBuilderState["lookbackDays"][] = [7, 14, 30, 60, 90]

const reportTypeLabels: Record<ReportType, string> = {
  new_listings: "📸 New Listings",
  new_listings_gallery: "📸 New Listings",
  market_snapshot: "📊 Market Update",
  closed: "🏠 Closed Sales",
  inventory: "📦 Inventory",
  price_bands: "💰 Price Bands",
  open_houses: "🚪 Open Houses",
  featured_listings: "⭐ Featured Listings",
}

export function ReportTypeSection({
  stepNumber,
  reportType,
  lookbackDays,
  onChange,
  isExpanded,
  onToggle,
}: ReportTypeSectionProps) {
  const summary = `${reportTypeLabels[reportType] || reportType} · Last ${lookbackDays} days`

  return (
    <AccordionSection
      stepNumber={stepNumber}
      title="Report Type"
      subtitle="Choose the type of market report to generate"
      summary={summary}
      status="complete"
      isExpanded={isExpanded}
      onToggle={onToggle}
    >
      <div className="space-y-6">
        <div>
          <label className="text-sm text-muted-foreground">What type of report should be generated?</label>

          {/* Main Report Types */}
          <div className="mt-3 grid grid-cols-3 gap-3">
            {mainReportTypes.map((type) => (
              <button
                key={type.value}
                onClick={() => onChange({ reportType: type.value })}
                className={cn(
                  "relative rounded-xl border-2 p-4 text-left transition-all hover:border-violet-300",
                  reportType === type.value ? "border-violet-500 bg-violet-50 dark:bg-violet-950/50" : "border-border",
                )}
              >
                {reportType === type.value && <div className="absolute right-2 top-2 text-sm text-violet-600">✓</div>}
                <div className="text-2xl">{type.icon}</div>
                <div className="mt-2 font-medium">{type.label}</div>
                <div className="mt-1 text-xs text-muted-foreground">{type.description}</div>
              </button>
            ))}
          </div>

          {/* More Report Types */}
          <div className="mt-4">
            <div className="mb-3 flex items-center gap-2 text-xs text-muted-foreground">
              <div className="h-px flex-1 bg-border" />
              <span>More Report Types</span>
              <div className="h-px flex-1 bg-border" />
            </div>
            <div className="grid grid-cols-3 gap-3">
              {moreReportTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => onChange({ reportType: type.value })}
                  className={cn(
                    "rounded-xl border-2 p-3 text-center transition-all hover:border-violet-300",
                    reportType === type.value ? "border-violet-500 bg-violet-50 dark:bg-violet-950/50" : "border-border",
                  )}
                >
                  <div className="text-xl">{type.icon}</div>
                  <div className="mt-1 text-sm font-medium">{type.label}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Lookback Period */}
        <div>
          <div className="mb-3 flex items-center gap-2 text-xs text-muted-foreground">
            <div className="h-px flex-1 bg-border" />
            <span>Lookback Period</span>
            <div className="h-px flex-1 bg-border" />
          </div>
          <label className="text-sm text-muted-foreground">How far back should the report look for data?</label>
          <div className="mt-3 flex gap-2">
            {lookbackOptions.map((days) => (
              <button
                key={days}
                onClick={() => onChange({ lookbackDays: days })}
                className={cn(
                  "flex-1 rounded-lg border-2 px-3 py-2 text-sm font-medium transition-all",
                  lookbackDays === days
                    ? "border-violet-500 bg-violet-50 text-violet-700 dark:bg-violet-950/50 dark:text-violet-300"
                    : "border-border hover:border-violet-300",
                )}
              >
                {days} days
              </button>
            ))}
          </div>
        </div>
      </div>
    </AccordionSection>
  )
}

