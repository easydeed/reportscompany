"use client"

import { cn } from "@/lib/utils"
import { AccordionSection } from "../accordion-section"
import { type ReportType, type ScheduleBuilderState, REPORT_TYPE_LABELS, REPORT_TYPE_ICONS } from "@/lib/schedule-types"

interface ReportTypeSectionProps {
  reportType: ReportType
  lookbackDays: ScheduleBuilderState["lookbackDays"]
  onReportTypeChange: (value: ReportType) => void
  onLookbackChange: (value: ScheduleBuilderState["lookbackDays"]) => void
}

const REPORT_TYPES: { type: ReportType; description: string }[] = [
  { type: "market_snapshot", description: "Stats & trends" },
  { type: "new_listings_gallery", description: "Photo gallery" },
  { type: "closed", description: "Recently sold" },
  { type: "inventory", description: "Active inventory" },
  { type: "price_bands", description: "Price breakdown" },
  { type: "open_houses", description: "Weekend tours" },
]

const LOOKBACK_OPTIONS: ScheduleBuilderState["lookbackDays"][] = [7, 14, 30, 60, 90]

export function ReportTypeSection({
  reportType,
  lookbackDays,
  onReportTypeChange,
  onLookbackChange,
}: ReportTypeSectionProps) {
  return (
    <AccordionSection
      id="report-type"
      title="Report Type"
      status="complete"
      summary={`${REPORT_TYPE_ICONS[reportType]} ${REPORT_TYPE_LABELS[reportType]} · Last ${lookbackDays} days`}
    >
      <div className="space-y-6">
        <div>
          <label className="text-sm text-muted-foreground mb-3 block">What type of report should be generated?</label>
          <div className="grid grid-cols-3 gap-3">
            {REPORT_TYPES.map(({ type, description }) => (
              <button
                key={type}
                onClick={() => onReportTypeChange(type)}
                className={cn(
                  "flex flex-col items-center gap-1 p-4 rounded-lg border-2 text-center transition-all",
                  reportType === type
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-muted-foreground/30",
                )}
              >
                <span className="text-2xl">{REPORT_TYPE_ICONS[type]}</span>
                {reportType === type && (
                  <span className="text-[10px] font-medium text-primary uppercase tracking-wide">Selected</span>
                )}
                <span className="font-medium text-sm">{REPORT_TYPE_LABELS[type]}</span>
                <span className="text-xs text-muted-foreground">{description}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-3">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-muted-foreground font-medium">Lookback Period</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          <label className="text-sm text-muted-foreground mb-3 block">
            How far back should the report look for data?
          </label>

          <div className="flex gap-2">
            {LOOKBACK_OPTIONS.map((days) => (
              <button
                key={days}
                onClick={() => onLookbackChange(days)}
                className={cn(
                  "flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all",
                  lookbackDays === days ? "bg-primary text-primary-foreground" : "bg-muted hover:bg-muted/80",
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
