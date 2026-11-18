"use client"

import { ArrowUpCircle } from "lucide-react"
import { StepHeader } from "./wizard-ui"

// The wizard's "limit reached" panel. Its own component so the Upgrade rule
// can be rendered and tested on its own: during the sponsored pilot the API
// refuses checkout for sponsored accounts, so this offers no Upgrade there.
export function LimitReached({
  error,
  offerUpgrade,
  onBack,
  onUpgrade,
}: {
  error: string | null
  offerUpgrade: boolean
  onBack: () => void
  onUpgrade: () => void
}) {
  return (
    <>
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[#FEF3C7]">
        <ArrowUpCircle className="h-[22px] w-[22px] text-[#B45309]" />
      </span>
      <StepHeader
        title={error?.split(" — ")[0] || "Limit Reached"}
        sub={error?.split(" — ")[1] || error || "You've used all your reports for this billing period."}
      />
      <p className="m-0 text-[15px] text-[#475569]">
        {offerUpgrade
          ? "Upgrade your plan to continue, or wait until your limit resets next month."
          : "You can make more when your limit resets next month."}
      </p>
      <div className="mt-auto flex gap-2.5">
        <button
          type="button"
          onClick={onBack}
          className="h-[46px] rounded-[9px] border border-[#D6D3CB] px-[18px] text-sm font-semibold"
        >
          Go Back
        </button>
        {offerUpgrade && (
          <button
            type="button"
            onClick={onUpgrade}
            className="inline-flex h-[46px] items-center gap-2 rounded-[9px] bg-[#0F172A] px-5 text-sm font-semibold text-white"
          >
            <ArrowUpCircle className="h-4 w-4" /> Upgrade Plan
          </button>
        )}
      </div>
    </>
  )
}
