"use client"

import type React from "react"

import { useState } from "react"
import { Search, X, Check, MapPin } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import type { ReportBuilderState, AreaType } from "@/components/report-builder"

interface AreaSectionProps {
  state: ReportBuilderState
  updateState: <K extends keyof ReportBuilderState>(key: K, value: ReportBuilderState[K]) => void
}

// Mock city data for autocomplete
const mockCities = [
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
]

export function AreaSection({ state, updateState }: AreaSectionProps) {
  const [citySearch, setCitySearch] = useState(state.city || "")
  const [showCitySuggestions, setShowCitySuggestions] = useState(false)
  const [zipInput, setZipInput] = useState("")

  const filteredCities = mockCities.filter((city) => city.toLowerCase().includes(citySearch.toLowerCase()))

  const handleCitySelect = (city: string) => {
    setCitySearch(city)
    updateState("city", city)
    setShowCitySuggestions(false)
  }

  const handleZipAdd = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && zipInput.trim()) {
      const zip = zipInput.trim()
      if (/^\d{5}$/.test(zip) && !state.zipCodes.includes(zip)) {
        updateState("zipCodes", [...state.zipCodes, zip])
        setZipInput("")
      }
    }
  }

  const handleZipRemove = (zip: string) => {
    updateState(
      "zipCodes",
      state.zipCodes.filter((z) => z !== zip),
    )
  }

  const handleAreaTypeChange = (value: AreaType) => {
    updateState("areaType", value)
    if (value === "city") {
      updateState("zipCodes", [])
    } else {
      updateState("city", null)
      setCitySearch("")
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">What area should this report cover?</p>

      <RadioGroup
        value={state.areaType}
        onValueChange={(value) => handleAreaTypeChange(value as AreaType)}
        className="flex gap-6"
      >
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="city" id="area-city" className="border-violet-500 text-violet-600" />
          <Label htmlFor="area-city" className="cursor-pointer">
            City
          </Label>
        </div>
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="zip" id="area-zip" className="border-violet-500 text-violet-600" />
          <Label htmlFor="area-zip" className="cursor-pointer">
            ZIP Codes
          </Label>
        </div>
      </RadioGroup>

      {state.areaType === "city" ? (
        <div className="relative">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={citySearch}
              onChange={(e) => {
                setCitySearch(e.target.value)
                setShowCitySuggestions(true)
                if (!e.target.value) {
                  updateState("city", null)
                }
              }}
              onFocus={() => setShowCitySuggestions(true)}
              onBlur={() => setTimeout(() => setShowCitySuggestions(false), 200)}
              placeholder="Search for a city..."
              className="pl-10 pr-10"
            />
            {state.city && <Check className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-emerald-500" />}
          </div>

          {showCitySuggestions && citySearch && filteredCities.length > 0 && (
            <div className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg border bg-popover shadow-lg">
              {filteredCities.map((city) => (
                <button
                  key={city}
                  onClick={() => handleCitySelect(city)}
                  className={cn(
                    "flex w-full items-center gap-2 px-4 py-2 text-left text-sm hover:bg-muted",
                    city === state.city && "bg-violet-50 text-violet-900",
                  )}
                >
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                  {city}
                </button>
              ))}
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
              placeholder="Add ZIP code..."
              className="pl-10"
            />
          </div>

          {state.zipCodes.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {state.zipCodes.map((zip) => (
                <Badge key={zip} variant="secondary" className="flex items-center gap-1 px-3 py-1.5">
                  {zip}
                  <button onClick={() => handleZipRemove(zip)} className="ml-1 rounded-full hover:bg-muted">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}

          {state.zipCodes.length > 0 && (
            <p className="text-sm text-muted-foreground">
              {state.zipCodes.length} ZIP code{state.zipCodes.length !== 1 ? "s" : ""} selected
            </p>
          )}
        </div>
      )}
    </div>
  )
}
