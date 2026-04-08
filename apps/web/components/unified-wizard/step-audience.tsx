"use client"

import { cn } from "@/lib/utils"
import { Check } from "lucide-react"
import { AUDIENCES, type AudienceFilter } from "./types"

interface StepAudienceProps {
  selected: AudienceFilter
  onSelect: (audience: AudienceFilter) => void
}

export function StepAudience({ selected, onSelect }: StepAudienceProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Who&apos;s it for?</h2>
        <p className="text-sm text-gray-500 mt-1">Filter listings to match your audience. This controls what homes appear in the gallery.</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {AUDIENCES.map((audience) => {
          const active = selected === audience.id
          return (
            <button
              key={audience.id}
              onClick={() => onSelect(audience.id)}
              className={cn(
                "relative rounded-xl border-2 p-4 text-left transition-all",
                active
                  ? "border-primary bg-primary/5 shadow-sm"
                  : "border-gray-200 hover:border-primary/40 hover:bg-gray-50/50"
              )}
            >
              <div className="flex items-center justify-between">
                <span className="text-base font-semibold text-gray-900">{audience.label}</span>
                {active && (
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary">
                    <Check className="h-3 w-3 text-white" />
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-500 mt-1">{audience.description}</p>
            </button>
          )
        })}
      </div>
    </div>
  )
}
