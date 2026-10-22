"use client"

/**
 * Step 1 — what the report is. Design's `Wizards v3` grid: two columns, a
 * thumbnail of each kind's first page, a name and one line.
 *
 * Open Houses is shown and greyed rather than hidden, as Design draws it,
 * with the reason. It stays unselectable: `disabled` in REPORT_TYPES is still
 * what decides that.
 */
import { cn } from "@/lib/utils"
import { SharedPDFPreview } from "@/components/shared/pdf-preview"
import type { PreviewReportType } from "@/components/shared/email-preview/sample-data"
import { REPORT_TYPES } from "./types"
import { StepHeader } from "./wizard-ui"

/** Design's order and one-line notes. New Listings Analytics is not in the deck. */
const NOTES: Record<string, string> = {
  market_snapshot: "Median, days, list-to-sale. The monthly one.",
  closed: "Who sold, for how much. Seller prospecting.",
  new_listings_gallery: "What just hit. Buyer prospecting.",
  inventory: "Everything for sale and months of supply.",
  price_bands: "Which price range is moving.",
  featured_listings: "Four homes to show off.",
  new_listings: "How new supply is pricing.",
  open_houses: "Paused — open-house data isn't reliable yet.",
}
const ORDER = Object.keys(NOTES)

interface StepStoryProps {
  selected: string | null
  onSelect: (reportType: string) => void
  primaryColor: string
  accentColor: string
}

export function StepStory({ selected, onSelect, primaryColor, accentColor }: StepStoryProps) {
  const kinds = ORDER.flatMap((id) => {
    const rt = REPORT_TYPES.find((r) => r.id === id)
    return rt ? [rt] : []
  })

  return (
    <div className="flex flex-col gap-[22px]">
      <StepHeader
        title="What should your sphere hear about?"
        sub="Snapshot is the one most agents send monthly. Pick another to see it on the right."
      />
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {kinds.map((rt) => {
          const active = selected === rt.id
          const off = !!rt.disabled
          return (
            <button
              key={rt.id}
              type="button"
              disabled={off}
              aria-pressed={active}
              onClick={() => !off && onSelect(rt.id)}
              className={cn(
                "flex items-center gap-3 rounded-xl border-[1.5px] py-2.5 pl-2.5 pr-3 text-left transition-colors",
                active ? "border-[#0F172A] bg-[#FAFAF7]" : "border-[#ECEAE3] bg-white",
                off ? "cursor-not-allowed opacity-50" : "hover:border-[#0F172A]",
              )}
            >
              <span
                className="h-11 w-[34px] shrink-0 overflow-hidden rounded-[2px] bg-white"
                style={{ boxShadow: "0 0 0 1px rgba(15,23,42,0.1)" }}
                aria-hidden
              >
                <span className="block" style={{ width: 480, transform: `scale(${34 / 480})`, transformOrigin: "0 0" }}>
                  <SharedPDFPreview
                    primaryColor={primaryColor}
                    accentColor={accentColor}
                    headerLogoUrl={null}
                    displayName={null}
                    agentName=""
                    agentTitle={null}
                    agentPhone={null}
                    agentEmail=""
                    agentPhotoUrl={null}
                    reportType={rt.id as PreviewReportType}
                    audienceLabel={null}
                    areaName=""
                    lookbackDays={rt.defaultLookback}
                  />
                </span>
              </span>
              <span className="flex min-w-0 flex-col">
                <span className="text-sm font-bold text-[#0F172A]">{rt.title}</span>
                <span className="text-xs leading-[1.35] text-[#64748B]">{NOTES[rt.id]}</span>
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
