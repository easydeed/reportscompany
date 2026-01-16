"use client"

import { Lightbulb } from "lucide-react"
import { Input } from "@/components/ui/input"
import { AccordionSection } from "../accordion-section"
import type { SectionStatus } from "../types"

interface ScheduleNameSectionProps {
  stepNumber?: number
  value: string
  onChange: (value: string) => void
  isExpanded: boolean
  onToggle: () => void
}

export function ScheduleNameSection({ stepNumber, value, onChange, isExpanded, onToggle }: ScheduleNameSectionProps) {
  const status: SectionStatus = value.trim().length > 0 ? "complete" : "warning"

  return (
    <AccordionSection
      stepNumber={stepNumber}
      title="Schedule Name"
      subtitle="Give your schedule a memorable name"
      summary={value || undefined}
      status={status}
      isExpanded={isExpanded}
      onToggle={onToggle}
    >
      <div className="space-y-4">
        <div>
          <label className="text-sm text-muted-foreground">Give your schedule a name</label>
          <Input
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="e.g., Irvine Weekly Market Update"
            className="mt-2"
          />
        </div>

        <div className="flex items-start gap-2 rounded-lg bg-violet-50 px-3 py-2 text-sm text-violet-800 dark:bg-violet-950/50 dark:text-violet-300">
          <Lightbulb className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>
            Tip: Use a descriptive name like "La Verne Monthly New Listings" to easily identify this schedule later.
          </span>
        </div>
      </div>
    </AccordionSection>
  )
}

