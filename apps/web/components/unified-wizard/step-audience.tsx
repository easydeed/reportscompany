"use client"

/**
 * Step 2 — who it is for. Design's `Wizards v3` radio list. The options and
 * their descriptions are still AUDIENCES, so what each one says is what its
 * filter preset does.
 */
import { AUDIENCES, type AudienceFilter } from "./types"
import { RadioList, RadioRow, StepHeader } from "./wizard-ui"

interface StepAudienceProps {
  selected: AudienceFilter
  onSelect: (audience: AudienceFilter) => void
}

export function StepAudience({ selected, onSelect }: StepAudienceProps) {
  return (
    <div className="flex flex-col gap-[22px]">
      <StepHeader
        title="Who is it for?"
        sub={'Filters which homes make the page. "All" is right for a general sphere.'}
      />
      <div role="radiogroup" aria-label="Audience">
        <RadioList>
          {AUDIENCES.map((a) => (
            <RadioRow
              key={a.id}
              on={selected === a.id}
              onClick={() => onSelect(a.id)}
              label={a.label}
              desc={a.description}
            />
          ))}
        </RadioList>
      </div>
    </div>
  )
}
