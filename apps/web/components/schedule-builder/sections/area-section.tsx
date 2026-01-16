"use client"

import { useState } from "react"
import { Search, X, MapPin, Check } from "lucide-react"
import { cn } from "@/lib/utils"
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

  const showDropdown = showSuggestions && citySearch && !city && filteredCities.length > 0

  return (
    <AccordionSection stepNumber={stepNumber} title="Area" subtitle="Define the geographic region for your report" summary={summary} status={status} isExpanded={isExpanded} onToggle={onToggle}>
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground text-center">What area should this report cover?</p>

        {/* Area Type Toggle */}
        <div className="flex justify-center gap-6">
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
          <div 
            className={cn(
              "transition-all duration-300 ease-out",
              showDropdown ? "min-h-[280px]" : "min-h-0"
            )}
          >
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
                className="pl-10 pr-10 h-12 text-base"
              />
              {city && <Check className="absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-emerald-500" />}
            </div>

            {showDropdown && (
              <div className="mt-2 rounded-xl border-2 border-violet-100 bg-white shadow-xl overflow-hidden dark:bg-slate-900 dark:border-violet-900">
                <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider bg-slate-50 dark:bg-slate-800">
                  Select a city
                </div>
                <div className="max-h-[200px] overflow-auto">
                  {filteredCities.map((c) => (
                    <button
                      key={c}
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => handleSelectCity(c)}
                      className={cn(
                        "flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-violet-50 dark:hover:bg-violet-900/30 transition-colors",
                        c === city && "bg-violet-50 text-violet-900 dark:bg-violet-900/50",
                      )}
                    >
                      <MapPin className="h-4 w-4 text-violet-500" />
                      <span className="font-medium">{c}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ZIP Code Tags */}
        {areaType === "zip" && (
          <div className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={zipInput}
                onChange={(e) => setZipInput(e.target.value.replace(/\D/g, "").slice(0, 5))}
                onKeyDown={(e) => e.key === "Enter" && handleAddZip()}
                placeholder="Add ZIP code (press Enter)..."
                className="pl-10 h-12 text-base"
                maxLength={5}
              />
            </div>

            {zipCodes.length > 0 && (
              <div className="flex flex-wrap justify-center gap-2">
                {zipCodes.map((zip) => (
                  <span
                    key={zip}
                    className="inline-flex items-center gap-1 rounded-full bg-violet-100 px-3 py-1.5 text-sm font-medium text-violet-800 dark:bg-violet-950 dark:text-violet-300"
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
              <p className="text-sm text-muted-foreground text-center">
                {zipCodes.length} ZIP code{zipCodes.length !== 1 ? "s" : ""} selected
              </p>
            )}
          </div>
        )}
      </div>
    </AccordionSection>
  )
}
