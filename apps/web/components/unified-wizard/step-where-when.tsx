"use client"

import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import { X } from "lucide-react"
import { CityCombobox } from "@/components/shared/city-combobox"
import type { WizardState } from "./types"

interface StepWhereWhenProps {
  state: WizardState
  onChange: (patch: Partial<WizardState>) => void
}

const LOOKBACK_OPTIONS = [7, 14, 30, 60, 90] as const

export function StepWhereWhen({ state, onChange }: StepWhereWhenProps) {
  const [zipInput, setZipInput] = useState("")

  const addZip = () => {
    const zip = zipInput.trim()
    if (zip.length === 5 && /^\d{5}$/.test(zip) && !state.zipCodes.includes(zip)) {
      onChange({ zipCodes: [...state.zipCodes, zip] })
      setZipInput("")
    }
  }

  const removeZip = (zip: string) => {
    onChange({ zipCodes: state.zipCodes.filter((z) => z !== zip) })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Where &amp; When?</h2>
        <p className="text-sm text-gray-500 mt-1">Choose the area and time window for your report.</p>
      </div>

      {/* Area selection */}
      <div className="space-y-3">
        <Label className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Area</Label>

        <div className="flex gap-2">
          <button
            onClick={() => onChange({ areaType: "city" })}
            className={cn(
              "flex-1 rounded-lg border-2 py-2 text-xs font-medium transition-all",
              state.areaType === "city" ? "border-primary bg-primary/5 text-primary" : "border-gray-200 text-gray-500 hover:border-gray-300"
            )}
          >
            City
          </button>
          <button
            onClick={() => onChange({ areaType: "zip" })}
            className={cn(
              "flex-1 rounded-lg border-2 py-2 text-xs font-medium transition-all",
              state.areaType === "zip" ? "border-primary bg-primary/5 text-primary" : "border-gray-200 text-gray-500 hover:border-gray-300"
            )}
          >
            ZIP Codes
          </button>
        </div>

        {state.areaType === "city" ? (
          <CityCombobox
            value={state.city}
            onChange={(city) => onChange({ city: city?.city || null })}
            placeholder="Search for a city..."
          />
        ) : (
          <div className="space-y-2">
            <div className="flex gap-2">
              <Input
                value={zipInput}
                onChange={(e) => setZipInput(e.target.value.replace(/\D/g, "").slice(0, 5))}
                onKeyDown={(e) => e.key === "Enter" && addZip()}
                placeholder="Enter ZIP code"
                className="h-14 flex-1"
                maxLength={5}
              />
              <button
                onClick={addZip}
                disabled={zipInput.length !== 5}
                className="px-4 h-14 rounded-lg bg-primary text-white text-xs font-medium disabled:opacity-40 transition-opacity"
              >
                Add
              </button>
            </div>
            {state.zipCodes.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {state.zipCodes.map((zip) => (
                  <span key={zip} className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-700">
                    {zip}
                    <button onClick={() => removeZip(zip)} className="hover:text-red-500 transition-colors">
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
            <p className="text-[10px] text-gray-400">Up to 5 ZIP codes</p>
          </div>
        )}
      </div>

      {/* Timeframe */}
      <div className="space-y-3">
        <Label className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Timeframe</Label>
        <div className="grid grid-cols-5 gap-2">
          {LOOKBACK_OPTIONS.map((days) => (
            <button
              key={days}
              onClick={() => onChange({ lookbackDays: days })}
              className={cn(
                "rounded-lg border-2 py-2.5 text-center transition-all",
                state.lookbackDays === days
                  ? "border-primary bg-primary/5 text-primary font-semibold"
                  : "border-gray-200 text-gray-500 hover:border-gray-300"
              )}
            >
              <div className="text-sm font-semibold">{days}</div>
              <div className="text-[10px]">days</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
