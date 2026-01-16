"use client"

import { useState, useEffect } from "react"
import { Search, X, Check, MapPin } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import type { ReportBuilderState, AreaType } from "../types"

interface AreaSectionProps {
  areaType: AreaType
  city: string | null
  zipCodes: string[]
  onChange: (updates: Partial<ReportBuilderState>) => void
}

// Sample cities for autocomplete - will be enhanced with API later
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

export function AreaSection({ areaType, city, zipCodes, onChange }: AreaSectionProps) {
  const [citySearch, setCitySearch] = useState(city || "")
  const [showCitySuggestions, setShowCitySuggestions] = useState(false)
  const [zipInput, setZipInput] = useState("")

  // Sync city search with city prop
  useEffect(() => {
    if (city) {
      setCitySearch(city)
    }
  }, [city])

  const filteredCities = SAMPLE_CITIES.filter((c) => 
    c.toLowerCase().includes(citySearch.toLowerCase())
  )

  const handleCitySelect = (selectedCity: string) => {
    setCitySearch(selectedCity)
    onChange({ city: selectedCity })
    setShowCitySuggestions(false)
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

  const handleAreaTypeChange = (value: AreaType) => {
    onChange({ areaType: value })
    if (value === "city") {
      onChange({ zipCodes: [] })
    } else {
      onChange({ city: null })
      setCitySearch("")
    }
  }

  const showDropdown = showCitySuggestions && citySearch && !city && filteredCities.length > 0

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground text-center">What area should this report cover?</p>

      {/* Area Type Toggle */}
      <div className="flex justify-center gap-6">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="areaType"
            checked={areaType === "city"}
            onChange={() => handleAreaTypeChange("city")}
            className="h-4 w-4 text-violet-600 accent-violet-600"
          />
          <span className="text-sm font-medium">City</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="areaType"
            checked={areaType === "zip"}
            onChange={() => handleAreaTypeChange("zip")}
            className="h-4 w-4 text-violet-600 accent-violet-600"
          />
          <span className="text-sm font-medium">ZIP Codes</span>
        </label>
      </div>

      {areaType === "city" ? (
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
                setShowCitySuggestions(true)
                if (!e.target.value) {
                  onChange({ city: null })
                }
              }}
              onFocus={() => setShowCitySuggestions(true)}
              onBlur={() => setTimeout(() => setShowCitySuggestions(false), 200)}
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
                    onClick={() => handleCitySelect(c)}
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
      ) : (
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={zipInput}
              onChange={(e) => setZipInput(e.target.value.replace(/\D/g, "").slice(0, 5))}
              onKeyDown={handleZipAdd}
              placeholder="Add ZIP code (press Enter)..."
              className="pl-10 h-12 text-base"
            />
          </div>

          {zipCodes.length > 0 && (
            <div className="flex flex-wrap justify-center gap-2">
              {zipCodes.map((zip) => (
                <Badge key={zip} variant="secondary" className="flex items-center gap-1 px-3 py-1.5 text-sm">
                  {zip}
                  <button onClick={() => handleZipRemove(zip)} className="ml-1 rounded-full hover:bg-muted">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
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
  )
}
