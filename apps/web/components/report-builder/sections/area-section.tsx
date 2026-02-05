"use client"

import { useState, useEffect } from "react"
import { Search, MapPin, X, Check, Hash } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import type { ReportBuilderState, AreaType } from "../types"

interface AreaSectionProps {
  areaType: AreaType
  city: string | null
  zipCodes: string[]
  onChange: (updates: Partial<ReportBuilderState>) => void
  isComplete: boolean
  stepNumber?: number
}

// Sample cities for autocomplete
const SAMPLE_CITIES = [
  "Irvine, CA",
  "Los Angeles, CA",
  "San Francisco, CA",
  "San Diego, CA",
  "Sacramento, CA",
  "Fresno, CA",
  "Oakland, CA",
  "Long Beach, CA",
  "Anaheim, CA",
  "Santa Ana, CA",
  "Pasadena, CA",
  "Newport Beach, CA",
  "Huntington Beach, CA",
  "La Verne, CA",
]

export function AreaSection({ areaType, city, zipCodes, onChange, isComplete, stepNumber = 2 }: AreaSectionProps) {
  const [citySearch, setCitySearch] = useState(city || "")
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [zipInput, setZipInput] = useState("")

  useEffect(() => {
    if (city) setCitySearch(city)
  }, [city])

  const filteredCities = SAMPLE_CITIES.filter((c) =>
    c.toLowerCase().includes(citySearch.toLowerCase())
  )

  const handleCitySelect = (selectedCity: string) => {
    setCitySearch(selectedCity)
    onChange({ city: selectedCity })
    setShowSuggestions(false)
  }

  const handleClearCity = () => {
    setCitySearch("")
    onChange({ city: null })
  }

  const handleZipAdd = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && zipInput.trim()) {
      const zip = zipInput.trim()
      if (/^\d{5}$/.test(zip) && !zipCodes.includes(zip)) {
        onChange({ zipCodes: [...zipCodes, zip] })
        setZipInput("")
      }
    }
  }

  const handleZipRemove = (zip: string) => {
    onChange({ zipCodes: zipCodes.filter((z) => z !== zip) })
  }

  const handleAreaTypeChange = (type: AreaType) => {
    onChange({ areaType: type })
    if (type === "city") {
      onChange({ zipCodes: [] })
    } else {
      onChange({ city: null })
      setCitySearch("")
    }
  }

  const showDropdown = showSuggestions && citySearch && !city && filteredCities.length > 0

  return (
    <section className={cn(
      "bg-white rounded-xl border transition-all duration-200",
      isComplete ? "border-gray-200 shadow-sm" : "border-gray-200/80 shadow-sm"
    )}>
      {/* Section Header */}
      <div className="flex items-center gap-3 px-5 py-4">
        <div className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors",
          isComplete
            ? "bg-emerald-500 text-white"
            : "bg-gray-100 text-gray-500"
        )}>
          {isComplete ? <Check className="w-3.5 h-3.5" /> : stepNumber}
        </div>
        <h3 className="text-sm font-medium text-gray-900">Area</h3>
      </div>

      <div className="px-5 pb-5">
        {/* Area Type Toggle */}
        <div className="flex gap-2 mb-3">
          <button
            onClick={() => handleAreaTypeChange("city")}
            className={cn(
              "flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-all duration-150",
              areaType === "city"
                ? "bg-primary/5 border-primary text-primary shadow-sm shadow-primary/10"
                : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50 hover:border-gray-300"
            )}
          >
            <MapPin className="w-4 h-4" />
            City
          </button>
          <button
            onClick={() => handleAreaTypeChange("zip")}
            className={cn(
              "flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-all duration-150",
              areaType === "zip"
                ? "bg-primary/5 border-primary text-primary shadow-sm shadow-primary/10"
                : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50 hover:border-gray-300"
            )}
          >
            <Hash className="w-4 h-4" />
            ZIP Codes
          </button>
        </div>

      {/* City Input */}
      {areaType === "city" && (
        <div>
          {city ? (
            // Selected city display
            <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
              <MapPin className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-700 flex-1">{city}</span>
              <button 
                onClick={handleClearCity}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            // City search input
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                value={citySearch}
                onChange={(e) => {
                  setCitySearch(e.target.value)
                  setShowSuggestions(true)
                }}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                placeholder="Search city..."
                className="pl-9 border-gray-200 focus:border-violet-600 focus:ring-violet-600"
              />
              
              {/* Dropdown */}
              {showDropdown && (
                <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden">
                  <div className="max-h-48 overflow-auto">
                    {filteredCities.map((c) => (
                      <button
                        key={c}
                        onClick={() => handleCitySelect(c)}
                        className="flex items-center gap-2 w-full px-3 py-2 text-sm text-left hover:bg-gray-50"
                      >
                        <MapPin className="w-4 h-4 text-gray-400" />
                        {c}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ZIP Input */}
      {areaType === "zip" && (
        <div className="space-y-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              value={zipInput}
              onChange={(e) => setZipInput(e.target.value.replace(/\D/g, "").slice(0, 5))}
              onKeyDown={handleZipAdd}
              placeholder="Add ZIP code (press Enter)"
              className="pl-9 border-gray-200 focus:border-violet-600 focus:ring-violet-600"
              maxLength={5}
            />
          </div>
          
          {/* ZIP tags */}
          {zipCodes.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {zipCodes.map((zip) => (
                <span
                  key={zip}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-sm text-gray-700"
                >
                  {zip}
                  <button
                    onClick={() => handleZipRemove(zip)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      )}
      </div>
    </section>
  )
}
