"use client"

import { useState, useMemo } from "react"
import { Building2, MapPin, Search, X } from "lucide-react"
import { Input } from "@/components/ui/input"
import type { ReportBuilderState } from "./types"
import { SIMULATED_CITIES, RECENT_AREAS } from "./types"

interface StepAreaProps {
  state: ReportBuilderState
  onChange: (patch: Partial<ReportBuilderState>) => void
}

export function StepArea({ state, onChange }: StepAreaProps) {
  const [cityQuery, setCityQuery] = useState("")
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [zipInput, setZipInput] = useState("")

  const filteredCities = useMemo(() => {
    if (!cityQuery.trim()) return []
    return SIMULATED_CITIES.filter((c) =>
      c.toLowerCase().includes(cityQuery.toLowerCase())
    )
  }, [cityQuery])

  function selectCity(city: string) {
    onChange({ city })
    setCityQuery(city)
    setShowSuggestions(false)
  }

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
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search for a city..."
            value={cityQuery}
            onChange={(e) => {
              setCityQuery(e.target.value)
              setShowSuggestions(true)
              if (!e.target.value.trim()) onChange({ city: null })
            }}
            onFocus={() => setShowSuggestions(true)}
            className="pl-10"
          />
          {showSuggestions && filteredCities.length > 0 && (
            <div className="absolute z-10 mt-1 w-full rounded-lg border border-border bg-card shadow-lg">
              {filteredCities.map((city) => (
                <button
                  key={city}
                  type="button"
                  onClick={() => selectCity(city)}
                  className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm hover:bg-muted"
                >
                  <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                  {city}
                </button>
              ))}
            </div>
          )}

          {/* Recent areas */}
          {!state.city && (
            <div className="mt-4">
              <p className="text-sm font-medium text-muted-foreground">Recent areas</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {RECENT_AREAS.map((area) => (
                  <button
                    key={area}
                    type="button"
                    onClick={() => selectCity(area)}
                    className="rounded-full border border-border bg-card px-3.5 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                  >
                    {area}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
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
