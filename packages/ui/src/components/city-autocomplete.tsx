"use client"

import { useState, useRef, useEffect } from "react"
import { Input } from "./ui/input"
import { cn } from "../lib/utils"
import { MapPin, Search, Check } from "lucide-react"
import { SOCAL_CITIES } from "./schedules/types"

interface CityAutocompleteProps {
  value: string
  onChange: (city: string) => void
  placeholder?: string
  className?: string
}

export function CityAutocomplete({
  value,
  onChange,
  placeholder = "Start typing a city...",
  className,
}: CityAutocompleteProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [inputValue, setInputValue] = useState(value)
  const [highlightedIndex, setHighlightedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLUListElement>(null)

  // Filter cities based on input
  const filteredCities = inputValue.trim()
    ? SOCAL_CITIES.filter((city) =>
        city.toLowerCase().startsWith(inputValue.toLowerCase())
      ).slice(0, 8) // Limit to 8 suggestions
    : []

  // Sync external value changes
  useEffect(() => {
    setInputValue(value)
  }, [value])

  // Scroll highlighted item into view
  useEffect(() => {
    if (listRef.current && highlightedIndex >= 0) {
      const item = listRef.current.children[highlightedIndex] as HTMLElement
      if (item) {
        item.scrollIntoView({ block: "nearest" })
      }
    }
  }, [highlightedIndex])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    setIsOpen(true)
    setHighlightedIndex(0)
    // Don't call onChange until selection - allows typing freely
  }

  const handleSelectCity = (city: string) => {
    setInputValue(city)
    onChange(city)
    setIsOpen(false)
    inputRef.current?.blur()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || filteredCities.length === 0) {
      if (e.key === "Enter") {
        // Allow submitting custom city
        onChange(inputValue)
      }
      return
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault()
        setHighlightedIndex((prev) =>
          prev < filteredCities.length - 1 ? prev + 1 : prev
        )
        break
      case "ArrowUp":
        e.preventDefault()
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : 0))
        break
      case "Enter":
        e.preventDefault()
        if (filteredCities[highlightedIndex]) {
          handleSelectCity(filteredCities[highlightedIndex])
        } else {
          onChange(inputValue)
          setIsOpen(false)
        }
        break
      case "Escape":
        setIsOpen(false)
        break
      case "Tab":
        if (filteredCities[highlightedIndex]) {
          handleSelectCity(filteredCities[highlightedIndex])
        }
        break
    }
  }

  const handleBlur = () => {
    // Small delay to allow click on list item
    setTimeout(() => {
      setIsOpen(false)
      // If input doesn't match any city exactly, still allow it
      if (inputValue && inputValue !== value) {
        onChange(inputValue)
      }
    }, 150)
  }

  const isExactMatch = SOCAL_CITIES.some(
    (city) => city.toLowerCase() === inputValue.toLowerCase()
  )

  return (
    <div className={cn("relative", className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="h-11 pl-10 pr-10"
          autoComplete="off"
        />
        {isExactMatch && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <Check className="w-4 h-4 text-green-600" />
          </div>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && filteredCities.length > 0 && (
        <ul
          ref={listRef}
          className="absolute z-50 w-full mt-1 bg-background border border-border rounded-lg shadow-lg overflow-hidden"
        >
          {filteredCities.map((city, index) => (
            <li
              key={city}
              onClick={() => handleSelectCity(city)}
              className={cn(
                "flex items-center gap-2 px-3 py-2.5 cursor-pointer transition-colors",
                index === highlightedIndex
                  ? "bg-primary/10 text-primary"
                  : "hover:bg-muted"
              )}
            >
              <MapPin className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <span className="font-medium">{city}</span>
              {city.toLowerCase() === inputValue.toLowerCase() && (
                <Check className="w-4 h-4 text-green-600 ml-auto" />
              )}
            </li>
          ))}
        </ul>
      )}

      {/* Hint when no matches */}
      {isOpen && inputValue.length >= 2 && filteredCities.length === 0 && (
        <div className="absolute z-50 w-full mt-1 bg-background border border-border rounded-lg shadow-lg p-3">
          <p className="text-sm text-muted-foreground">
            No cities found matching "{inputValue}"
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Press Enter to use this name anyway
          </p>
        </div>
      )}
    </div>
  )
}
