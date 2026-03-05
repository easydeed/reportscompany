"use client"

import { useState } from "react"
import { Building2, MapPin, X } from "lucide-react"
import { Input } from "@/components/ui/input"
import { CityCombobox } from "@/components/shared/city-combobox"
import type { ReportBuilderState } from "./types"

interface StepAreaProps {
  state: ReportBuilderState
  onChange: (patch: Partial<ReportBuilderState>) => void
}

export function StepArea({ state, onChange }: StepAreaProps) {
  const [zipInput, setZipInput] = useState("")

  function addZip(zip: string) {
    const trimmed = zip.trim()
    if (
      trimmed.length === 5 &&
      /^\d{5}$/.test(trimmed) &&
      !state.zipCodes.includes(trimmed) &&
      state.zipCodes.length < 5
    ) {
      onChange({ zipCodes: [...state.zipCodes, trimmed] })
      setZipInput("")
    }
  }

  function removeZip(zip: string) {
    onChange({ zipCodes: state.zipCodes.filter((z) => z !== zip) })
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-foreground">
          Where is your market?
        </h2>
        <p className="mt-1 text-muted-foreground">
          Choose how you&apos;d like to define your area.
        </p>
      </div>

      {/* Area type cards */}
      <div className="grid grid-cols-2 gap-4">
        <button
          type="button"
          onClick={() => onChange({ areaType: "city", zipCodes: [] })}
          className={`flex flex-col items-start gap-2 rounded-xl border-2 p-5 text-left transition-all ${
            state.areaType === "city"
              ? "border-[#6366F1] bg-[#EEF2FF]"
              : "border-border bg-card hover:border-[#C7D2FE]"
          }`}
        >
          <Building2
            className={`h-6 w-6 ${state.areaType === "city" ? "text-[#6366F1]" : "text-muted-foreground"}`}
          />
          <div>
            <p className="font-semibold text-foreground">City</p>
            <p className="text-sm text-muted-foreground">Search by city name</p>
          </div>
        </button>
        <button
          type="button"
          onClick={() => onChange({ areaType: "zip", city: null })}
          className={`flex flex-col items-start gap-2 rounded-xl border-2 p-5 text-left transition-all ${
            state.areaType === "zip"
              ? "border-[#6366F1] bg-[#EEF2FF]"
              : "border-border bg-card hover:border-[#C7D2FE]"
          }`}
        >
          <MapPin
            className={`h-6 w-6 ${state.areaType === "zip" ? "text-[#6366F1]" : "text-muted-foreground"}`}
          />
          <div>
            <p className="font-semibold text-foreground">ZIP Codes</p>
            <p className="text-sm text-muted-foreground">Enter up to 5 ZIP codes</p>
          </div>
        </button>
      </div>

      {/* City search */}
      {state.areaType === "city" && (
        <CityCombobox
          value={state.city}
          onChange={(c) => onChange({ city: c?.city || null })}
          placeholder="Search for a city..."
        />
      )}

      {/* ZIP entry */}
      {state.areaType === "zip" && (
        <div>
          <div className="flex items-center gap-2">
            <Input
              placeholder="Enter a 5-digit ZIP code..."
              value={zipInput}
              maxLength={5}
              onChange={(e) => setZipInput(e.target.value.replace(/\D/g, ""))}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault()
                  addZip(zipInput)
                }
              }}
            />
            <span className="shrink-0 text-sm text-muted-foreground">
              {state.zipCodes.length}/5
            </span>
          </div>
          {state.zipCodes.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {state.zipCodes.map((z) => (
                <span
                  key={z}
                  className="inline-flex items-center gap-1.5 rounded-full bg-[#EEF2FF] px-3 py-1 text-sm font-medium text-[#4338CA]"
                >
                  {z}
                  <button
                    type="button"
                    onClick={() => removeZip(z)}
                    className="rounded-full p-0.5 hover:bg-[#C7D2FE]"
                    aria-label={`Remove ZIP ${z}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
