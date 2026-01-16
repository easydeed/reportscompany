"use client"

import { Input } from "@/components/ui/input"
import { AccordionSection } from "../accordion-section"
import { Lightbulb } from "lucide-react"

interface ScheduleNameSectionProps {
  value: string
  onChange: (value: string) => void
}

export function ScheduleNameSection({ value, onChange }: ScheduleNameSectionProps) {
  const status = value.trim() ? "complete" : "incomplete"

  return (
    <AccordionSection id="name" title="Schedule Name" status={status} summary={value || undefined}>
      <div className="space-y-4">
        <div>
          <label className="text-sm text-muted-foreground mb-2 block">Give your schedule a name</label>
          <Input value={value} onChange={(e) => onChange(e.target.value)} placeholder="Irvine Weekly Market Update" />
        </div>

        <div className="flex items-start gap-2 text-sm text-muted-foreground bg-muted/50 rounded-md p-3">
          <Lightbulb className="h-4 w-4 mt-0.5 shrink-0" />
          <p>
            <strong className="font-medium">Tip:</strong> Use a descriptive name like &quot;La Verne Monthly New
            Listings&quot; to easily identify this schedule later.
          </p>
        </div>
      </div>
    </AccordionSection>
  )
}
