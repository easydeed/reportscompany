"use client"

import { cn } from "@/lib/utils"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import type { ReportBuilderState, ReportType, LookbackDays } from "@/components/report-builder"
import { reportTypeConfig } from "@/components/report-builder"

interface ReportTypeSectionProps {
  state: ReportBuilderState
  updateState: <K extends keyof ReportBuilderState>(key: K, value: ReportBuilderState[K]) => void
}

const reportTypes: ReportType[] = [
  "market_snapshot",
  "new_listings_gallery",
  "closed",
  "inventory",
  "price_bands",
  "open_houses",
]

const lookbackOptions: { value: LookbackDays; label: string }[] = [
  { value: 7, label: "7 days" },
  { value: 14, label: "14 days" },
  { value: 30, label: "30 days" },
  { value: 60, label: "60 days" },
  { value: 90, label: "90 days" },
]

export function ReportTypeSection({ state, updateState }: ReportTypeSectionProps) {
  return (
    <div className="space-y-6">
      <div>
        <p className="mb-4 text-sm text-muted-foreground">What type of report do you want to create?</p>
        <div className="grid grid-cols-3 gap-3">
          {reportTypes.map((type) => {
            const config = reportTypeConfig[type]
            const Icon = config.icon
            const isSelected = state.reportType === type

            return (
              <button
                key={type}
                onClick={() => updateState("reportType", type)}
                className={cn(
                  "relative flex flex-col items-center gap-2 rounded-xl border-2 p-4 text-center transition-all",
                  isSelected
                    ? "border-violet-500 bg-violet-50 text-violet-900"
                    : "border-border hover:border-violet-200 hover:bg-muted/50",
                )}
              >
                {isSelected && (
                  <div className="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full bg-violet-500 text-white">
                    <svg className="h-3 w-3" viewBox="0 0 12 12" fill="none">
                      <path
                        d="M2 6L5 9L10 3"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                )}
                <Icon className={cn("h-6 w-6", isSelected ? "text-violet-600" : "text-muted-foreground")} />
                <div>
                  <p className="font-medium text-sm">{config.label}</p>
                  <p className={cn("text-xs", isSelected ? "text-violet-600" : "text-muted-foreground")}>
                    {config.description}
                  </p>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      <div className="border-t pt-6">
        <p className="mb-4 text-sm font-medium text-muted-foreground">Lookback Period</p>
        <p className="mb-4 text-sm text-muted-foreground">How far back should the report look for data?</p>
        <RadioGroup
          value={state.lookbackDays.toString()}
          onValueChange={(value) => updateState("lookbackDays", Number.parseInt(value) as LookbackDays)}
          className="flex flex-wrap gap-4"
        >
          {lookbackOptions.map((option) => (
            <div key={option.value} className="flex items-center space-x-2">
              <RadioGroupItem
                value={option.value.toString()}
                id={`lookback-${option.value}`}
                className="border-violet-500 text-violet-600"
              />
              <Label htmlFor={`lookback-${option.value}`} className="cursor-pointer text-sm">
                {option.label}
              </Label>
            </div>
          ))}
        </RadioGroup>
      </div>
    </div>
  )
}
