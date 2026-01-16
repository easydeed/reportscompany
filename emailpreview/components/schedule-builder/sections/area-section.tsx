"use client"

import { useState, useRef, useEffect } from "react"
import { Search, MapPin, X, Check } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { AccordionSection } from "../accordion-section"
import type { ScheduleBuilderState } from "@/lib/schedule-types"

interface AreaSectionProps {
  areaType: ScheduleBuilderState["areaType"]
  city: string | null
  zipCodes: string[]
  onAreaTypeChange: (value: ScheduleBuilderState["areaType"]) => void
  onCityChange: (value: string | null) => void
  onZipCodesChange: (value: string[]) => void
}

const SAMPLE_CITIES = [
  "Irvine, CA",
  "Los Angeles, CA",
  "San Diego, CA",
  "San Francisco, CA",
  "La Verne, CA",
  "Pasadena, CA",
  "Newport Beach, CA",
  "Huntington Beach, CA",
]

export function AreaSection({
  areaType,
  city,
  zipCodes,
  onAreaTypeChange,
  onCityChange,
  onZipCodesChange,
}: AreaSectionProps) {
  const [citySearch, setCitySearch] = useState("")
  const [showCitySuggestions, setShowCitySuggestions] = useState(false)
  const [zipInput, setZipInput] = useState("")
  const cityInputRef = useRef<HTMLInputElement>(null)

  const status =
    (areaType === "city" && city) || (areaType === "zip" && zipCodes.length > 0) ? "complete" : "incomplete"

  const summary =
    areaType === "city" && city
      ? city
      : areaType === "zip" && zipCodes.length > 0
        ? `${zipCodes.length} ZIP code${zipCodes.length > 1 ? "s" : ""}`
        : undefined

  const filteredCities = SAMPLE_CITIES.filter((c) => c.toLowerCase().includes(citySearch.toLowerCase()))

  const handleCitySelect = (selectedCity: string) => {
    onCityChange(selectedCity)
    setCitySearch(selectedCity)
    setShowCitySuggestions(false)
  }

  const handleAddZip = () => {
    const zip = zipInput.trim()
    if (zip && /^\d{5}$/.test(zip) && !zipCodes.includes(zip)) {
      onZipCodesChange([...zipCodes, zip])
      setZipInput("")
    }
  }

  const handleRemoveZip = (zip: string) => {
    onZipCodesChange(zipCodes.filter((z) => z !== zip))
  }

  useEffect(() => {
    if (city) {
      setCitySearch(city)
    }
  }, [city])

  return (
    <AccordionSection
      id="area"
      title="Area"
      status={status}
      summary={summary}
      summaryIcon={summary ? <MapPin className="h-3.5 w-3.5" /> : undefined}
    >
      <div className="space-y-4">
        <label className="text-sm text-muted-foreground block">What area should this report cover?</label>

        {/* Area Type Toggle */}
        <div className="flex gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="areaType"
              checked={areaType === "city"}
              onChange={() => onAreaTypeChange("city")}
              className="h-4 w-4 text-primary"
            />
            <span className="text-sm font-medium">City</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="areaType"
              checked={areaType === "zip"}
              onChange={() => onAreaTypeChange("zip")}
              className="h-4 w-4 text-primary"
            />
            <span className="text-sm font-medium">ZIP Codes</span>
          </label>
        </div>

        {/* City Autocomplete */}
        {areaType === "city" && (
          <div className="relative">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                ref={cityInputRef}
                value={citySearch}
                onChange={(e) => {
                  setCitySearch(e.target.value)
                  setShowCitySuggestions(true)
                  if (!e.target.value) onCityChange(null)
                }}
                onFocus={() => setShowCitySuggestions(true)}
                placeholder="Search for a city..."
                className="pl-9 pr-9"
              />
              {city && <Check className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-500" />}
            </div>

            {showCitySuggestions && citySearch && !city && (
              <div className="absolute z-10 w-full mt-1 bg-popover border rounded-md shadow-lg max-h-48 overflow-auto">
                {filteredCities.length > 0 ? (
                  filteredCities.map((c) => (
                    <button
                      key={c}
                      onClick={() => handleCitySelect(c)}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-muted transition-colors"
                    >
                      {c}
                    </button>
                  ))
                ) : (
                  <div className="px-3 py-2 text-sm text-muted-foreground">No cities found</div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ZIP Code Input */}
        {areaType === "zip" && (
          <div className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={zipInput}
                onChange={(e) => setZipInput(e.target.value.replace(/\D/g, ""))}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault()
                    handleAddZip()
                  }
                }}
                placeholder="Add ZIP code..."
                maxLength={5}
                className="pl-9"
              />
            </div>

            {zipCodes.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {zipCodes.map((zip) => (
                  <Badge key={zip} variant="secondary" className="gap-1 pr-1.5">
                    {zip}
                    <button
                      onClick={() => handleRemoveZip(zip)}
                      className="ml-1 hover:bg-muted-foreground/20 rounded-full p-0.5"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}

            {zipCodes.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {zipCodes.length} ZIP code{zipCodes.length > 1 ? "s" : ""} selected
              </p>
            )}
          </div>
        )}
      </div>
    </AccordionSection>
  )
}
