"use client"

import { useState } from "react"
import { Search, X, MapPin, Check } from "lucide-react"
import { Input } from "@/components/ui/input"
import { AccordionSection } from "../accordion-section"
import type { ScheduleBuilderState, SectionStatus } from "../types"

interface AreaSectionProps {
  stepNumber?: number
  areaType: ScheduleBuilderState["areaType"]
  city: string | null
  zipCodes: string[]
  onChange: (updates: Partial<ScheduleBuilderState>) => void
  isExpanded: boolean
  onToggle: () => void
}

// Popular California cities for quick selection
const citySuggestions = [
  "Irvine, CA",
  "La Verne, CA",
  "Riverside, CA",
  "Newport Beach, CA",
  "Anaheim, CA",
  "Santa Ana, CA",
  "Costa Mesa, CA",
  "Tustin, CA",
  "Huntington Beach, CA",
  "Corona, CA",
  "Ontario, CA",
  "Rancho Cucamonga, CA",
  "Pasadena, CA",
  "Los Angeles, CA",
  "San Diego, CA",
]

export function AreaSection({ stepNumber, areaType, city, zipCodes, onChange, isExpanded, onToggle }: AreaSectionProps) {
  const [citySearch, setCitySearch] = useState(city || "")
  const [zipInput, setZipInput] = useState("")
  const [showSuggestions, setShowSuggestions] = useState(false)

  const status: SectionStatus =
    (areaType === "city" && city) || (areaType === "zip" && zipCodes.length > 0) ? "complete" : "warning"

  const summary =
    areaType === "city"
      ? city
        ? `📍 ${city}`
        : undefined
      : zipCodes.length > 0
        ? `📍 ${zipCodes.length} ZIP codes`
        : undefined

  const filteredCities = citySuggestions.filter((c) => c.toLowerCase().includes(citySearch.toLowerCase()))

  const handleSelectCity = (selectedCity: string) => {
    onChange({ city: selectedCity })
    setCitySearch(selectedCity)
    setShowSuggestions(false)
  }

  const handleAddZip = () => {
    const zip = zipInput.trim()
    if (zip && /^\d{5}$/.test(zip) && !zipCodes.includes(zip)) {
      onChange({ zipCodes: [...zipCodes, zip] })
      setZipInput("")
    }
  }

  const handleRemoveZip = (zip: string) => {
    onChange({ zipCodes: zipCodes.filter((z) => z !== zip) })
  }

  return (
    <AccordionSection stepNumber={stepNumber} title="Area" subtitle="Define the geographic region for your report" summary={summary} status={status} isExpanded={isExpanded} onToggle={onToggle}>
      <div className="space-y-4">
        <label className="text-sm text-muted-foreground">What area should this report cover?</label>

        {/* Area Type Toggle */}
        <div className="flex gap-4">
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="radio"
              name="areaType"
              checked={areaType === "city"}
              onChange={() => onChange({ areaType: "city", zipCodes: [] })}
              className="h-4 w-4 accent-violet-600"
            />
            <span className="text-sm font-medium">City</span>
          </label>
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="radio"
              name="areaType"
              checked={areaType === "zip"}
              onChange={() => onChange({ areaType: "zip", city: null })}
              className="h-4 w-4 accent-violet-600"
            />
            <span className="text-sm font-medium">ZIP Codes</span>
          </label>
        </div>

        {/* City Autocomplete */}
        {areaType === "city" && (
          <div className="relative">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={citySearch}
                onChange={(e) => {
                  setCitySearch(e.target.value)
                  setShowSuggestions(true)
                  if (!e.target.value) onChange({ city: null })
                }}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                placeholder="Search for a city..."
                className="pl-9 pr-9"
              />
              {city && <Check className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-emerald-500" />}
            </div>

            {showSuggestions && citySearch && (
              <div className="absolute z-10 mt-1 w-full rounded-lg border bg-background shadow-lg max-h-64 overflow-auto">
                {filteredCities.length > 0 ? (
                  filteredCities.map((c) => (
                    <button
                      key={c}
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => handleSelectCity(c)}
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-muted"
                    >
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                      {c}
                    </button>
                  ))
                ) : (
                  <div className="px-3 py-2 text-sm text-muted-foreground">
                    No suggestions. Type the full city name.
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ZIP Code Tags */}
        {areaType === "zip" && (
          <div className="space-y-3">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={zipInput}
                  onChange={(e) => setZipInput(e.target.value.replace(/\D/g, "").slice(0, 5))}
                  onKeyDown={(e) => e.key === "Enter" && handleAddZip()}
                  placeholder="Add ZIP code..."
                  className="pl-9"
                  maxLength={5}
                />
              </div>
            </div>

            {zipCodes.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {zipCodes.map((zip) => (
                  <span
                    key={zip}
                    className="inline-flex items-center gap-1 rounded-full bg-violet-100 px-3 py-1 text-sm text-violet-800 dark:bg-violet-950 dark:text-violet-300"
                  >
                    {zip}
                    <button onClick={() => handleRemoveZip(zip)} className="ml-1 rounded-full hover:bg-violet-200 dark:hover:bg-violet-800">
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}

            {zipCodes.length > 0 && (
              <div className="text-sm text-muted-foreground">
                {zipCodes.length} ZIP code{zipCodes.length !== 1 ? "s" : ""} selected
              </div>
            )}
          </div>
        )}
      </div>
    </AccordionSection>
  )
}

