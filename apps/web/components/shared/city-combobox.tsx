"use client"

import { useState, useMemo } from "react"
import { Check, ChevronsUpDown, MapPin, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import { CRMLS_CITIES, type CRMLSCity } from "@/lib/crmls-cities"

interface CityComboboxProps {
  value: string | null
  onChange: (city: CRMLSCity | null) => void
  placeholder?: string
  recentCities?: string[]
  disabled?: boolean
}

function filterCities(query: string): CRMLSCity[] {
  if (!query || query.length < 2) return []
  const q = query.toLowerCase().trim()

  const exactPrefix = CRMLS_CITIES.filter((c) =>
    c.city.toLowerCase().startsWith(q)
  )
  const fuzzy = CRMLS_CITIES.filter(
    (c) => c.searchTerms.includes(q) && !c.city.toLowerCase().startsWith(q)
  )
  return [...exactPrefix, ...fuzzy].slice(0, 20)
}

function groupByCounty(cities: CRMLSCity[]): Record<string, CRMLSCity[]> {
  const groups: Record<string, CRMLSCity[]> = {}
  for (const city of cities) {
    if (!groups[city.county]) groups[city.county] = []
    groups[city.county].push(city)
  }
  return groups
}

export function CityCombobox({
  value,
  onChange,
  placeholder = "Search for a city...",
  recentCities,
  disabled = false,
}: CityComboboxProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState("")

  const selectedCity = useMemo(
    () => CRMLS_CITIES.find((c) => c.city === value) || null,
    [value]
  )

  const filtered = useMemo(() => filterCities(search), [search])
  const grouped = useMemo(() => groupByCounty(filtered), [filtered])

  const recentCityObjects = useMemo(() => {
    if (!recentCities?.length) return []
    return recentCities
      .map((name) => CRMLS_CITIES.find((c) => c.city === name))
      .filter(Boolean) as CRMLSCity[]
  }, [recentCities])

  function handleSelect(city: CRMLSCity) {
    onChange(city)
    setOpen(false)
    setSearch("")
  }

  function handleClear() {
    onChange(null)
    setSearch("")
  }

  return (
    <div className="space-y-2">
      {/* Recent cities pills */}
      {recentCityObjects.length > 0 && !value && (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] text-gray-400 font-medium">Recent:</span>
          {recentCityObjects.map((city) => (
            <button
              key={city.city}
              type="button"
              onClick={() => handleSelect(city)}
              className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-[11px] font-medium text-gray-600 hover:bg-gray-200 transition-colors"
            >
              {city.city}
            </button>
          ))}
        </div>
      )}

      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild disabled={disabled}>
          <button
            type="button"
            role="combobox"
            aria-expanded={open}
            className={cn(
              "flex h-10 w-full items-center justify-between rounded-lg border border-gray-200 bg-white px-3 text-sm transition-colors",
              "hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary",
              disabled && "opacity-50 cursor-not-allowed",
              !value && "text-gray-400"
            )}
          >
            <div className="flex items-center gap-2 min-w-0">
              <MapPin className="h-4 w-4 flex-shrink-0 text-gray-400" />
              {selectedCity ? (
                <span className="truncate text-gray-900">
                  {selectedCity.label}
                  <span className="ml-1.5 text-gray-400 text-xs">
                    {selectedCity.county.replace(" County", "")}
                  </span>
                </span>
              ) : (
                <span className="truncate">{placeholder}</span>
              )}
            </div>
            <div className="flex items-center gap-1 flex-shrink-0">
              {value && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleClear()
                  }}
                  className="rounded p-0.5 hover:bg-gray-100 transition-colors"
                >
                  <X className="h-3.5 w-3.5 text-gray-400" />
                </button>
              )}
              <ChevronsUpDown className="h-3.5 w-3.5 text-gray-400" />
            </div>
          </button>
        </PopoverTrigger>

        <PopoverContent
          className="w-[var(--radix-popover-trigger-width)] p-0"
          align="start"
          sideOffset={4}
        >
          <Command shouldFilter={false}>
            <CommandInput
              placeholder="Type a city name..."
              value={search}
              onValueChange={setSearch}
            />
            <CommandList>
              {search.length < 2 ? (
                <div className="py-4 text-center text-xs text-gray-400">
                  Type at least 2 characters to search
                </div>
              ) : filtered.length === 0 ? (
                <CommandEmpty>
                  <div className="space-y-1">
                    <p className="text-gray-500">No cities found.</p>
                    <p className="text-[11px] text-gray-400">
                      Try a different spelling or search by ZIP code instead.
                    </p>
                  </div>
                </CommandEmpty>
              ) : (
                Object.entries(grouped).map(([county, cities]) => (
                  <CommandGroup
                    key={county}
                    heading={county}
                  >
                    {cities.map((city) => (
                      <CommandItem
                        key={city.city}
                        value={city.city}
                        onSelect={() => handleSelect(city)}
                        className="flex items-center justify-between"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <Check
                            className={cn(
                              "h-3.5 w-3.5 flex-shrink-0",
                              value === city.city ? "opacity-100 text-primary" : "opacity-0"
                            )}
                          />
                          <span className="truncate">{city.label}</span>
                        </div>
                        <span className="flex-shrink-0 text-[10px] text-gray-400">
                          {county.replace(" County", "")}
                        </span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                ))
              )}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  )
}
