"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import {
  FileText,
  TrendingUp,
  Home,
  DollarSign,
  BarChart3,
  Calendar,
  MapPin,
  Hash,
  PentagonIcon as PolygonIcon,
  X,
  Plus,
  Minus,
  ArrowRight,
  ArrowLeft,
  Info,
} from "lucide-react"
import { Stepper } from "@/components/stepper"

// Types
export type ReportType = "market_snapshot" | "new_listings" | "inventory" | "closed" | "price_bands" | "open_houses"

export type AreaMode = "city" | "zips" | "polygon"

export interface WizardFilters {
  minprice?: number
  maxprice?: number
  type?: string
  beds?: number
  baths?: number
}

export interface WizardState {
  report_type: ReportType | null
  area_mode: AreaMode
  city: string
  zips: string[]
  polygon: string | null
  lookback_days: number
  filters: WizardFilters
}

export interface WizardStep {
  title: string
  description: string
}

export interface WizardProps {
  onSubmit: (payload: any) => void
  onCancel: () => void
}

const reportTypes = [
  {
    id: "market_snapshot" as ReportType,
    name: "Market Snapshot",
    description: "Complete overview of current market conditions",
    icon: TrendingUp,
  },
  {
    id: "new_listings" as ReportType,
    name: "New Listings",
    description: "Recently listed properties in your area",
    icon: Home,
  },
  {
    id: "inventory" as ReportType,
    name: "Inventory Report",
    description: "Available properties and market supply",
    icon: BarChart3,
  },
  {
    id: "closed" as ReportType,
    name: "Closed Sales",
    description: "Recently sold properties and trends",
    icon: DollarSign,
  },
  {
    id: "price_bands" as ReportType,
    name: "Price Bands",
    description: "Market segmentation by price ranges",
    icon: BarChart3,
  },
  {
    id: "open_houses" as ReportType,
    name: "Open Houses",
    description: "Upcoming open house schedule",
    icon: Calendar,
  },
]

const propertyTypes = [
  { id: "RES", label: "Residential" },
  { id: "CND", label: "Condo" },
  { id: "MUL", label: "Multi-Family" },
  { id: "LND", label: "Land" },
  { id: "COM", label: "Commercial" },
]

const lookbackOptions = [
  { days: 7, label: "7 days" },
  { days: 14, label: "14 days" },
  { days: 30, label: "30 days" },
  { days: 60, label: "60 days" },
  { days: 90, label: "90 days" },
]

const steps: WizardStep[] = [
  { title: "Report Type", description: "Choose your report template" },
  { title: "Area", description: "Select location" },
  { title: "Filters", description: "Refine your criteria" },
  { title: "Review", description: "Generate report" },
]

// Validation function
export function validateStep(state: WizardState, step: number): { ok: boolean; error?: string } {
  switch (step) {
    case 0:
      if (!state.report_type) {
        return { ok: false, error: "Please select a report type" }
      }
      return { ok: true }
    case 1:
      if (state.area_mode === "city" && !state.city.trim()) {
        return { ok: false, error: "Please enter a city name" }
      }
      if (state.area_mode === "zips" && state.zips.length === 0) {
        return { ok: false, error: "Please add at least one ZIP code" }
      }
      if (state.area_mode === "polygon") {
        return { ok: false, error: "Polygon selection is not yet available" }
      }
      return { ok: true }
    case 2:
      if (!state.lookback_days) {
        return { ok: false, error: "Please select a lookback period" }
      }
      return { ok: true }
    case 3:
      return { ok: true }
    default:
      return { ok: false }
  }
}

// Build payload function
export function buildPayload(state: WizardState) {
  const payload: any = {
    report_type: state.report_type,
    lookback_days: state.lookback_days,
  }

  if (state.area_mode === "city" && state.city) {
    payload.city = state.city
  } else if (state.area_mode === "zips" && state.zips.length > 0) {
    payload.zips = state.zips
  } else if (state.area_mode === "polygon" && state.polygon) {
    payload.polygon = state.polygon
  }

  const filters: WizardFilters = {}
  if (state.filters.minprice) filters.minprice = state.filters.minprice
  if (state.filters.maxprice) filters.maxprice = state.filters.maxprice
  if (state.filters.type) filters.type = state.filters.type
  if (state.filters.beds) filters.beds = state.filters.beds
  if (state.filters.baths) filters.baths = state.filters.baths

  if (Object.keys(filters).length > 0) {
    payload.filters = filters
  }

  return payload
}

// Step 1: Report Type
function StepType({ state, setState }: { state: WizardState; setState: (s: WizardState) => void }) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Choose Report Type</h2>
        <p className="text-sm text-muted-foreground">Select the type of market report you want to generate</p>
      </div>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {reportTypes.map((type) => {
          const Icon = type.icon
          return (
            <Card
              key={type.id}
              className={`cursor-pointer transition-all hover:border-primary hover:shadow-md ${
                state.report_type === type.id ? "border-primary border-2 shadow-md" : ""
              }`}
              onClick={() => setState({ ...state, report_type: type.id })}
              role="button"
              tabIndex={0}
              aria-pressed={state.report_type === type.id}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault()
                  setState({ ...state, report_type: type.id })
                }
              }}
            >
              <CardHeader>
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center mb-3 transition-colors ${
                    state.report_type === type.id ? "bg-primary text-primary-foreground" : "bg-primary/10 text-primary"
                  }`}
                >
                  <Icon className="w-6 h-6" />
                </div>
                <CardTitle className="text-base font-display">{type.name}</CardTitle>
                <CardDescription className="text-sm">{type.description}</CardDescription>
              </CardHeader>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

// Step 2: Area
function StepArea({ state, setState }: { state: WizardState; setState: (s: WizardState) => void }) {
  const [zipInput, setZipInput] = useState("")

  const addZip = () => {
    const zip = zipInput.trim()
    if (zip && /^\d{5}$/.test(zip) && !state.zips.includes(zip)) {
      setState({ ...state, zips: [...state.zips, zip] })
      setZipInput("")
    }
  }

  const removeZip = (zip: string) => {
    setState({ ...state, zips: state.zips.filter((z) => z !== zip) })
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Select Area</h2>
        <p className="text-sm text-muted-foreground">Define the geographic area for your report</p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-6">
          {/* Area Mode Selection */}
          <div className="space-y-3">
            <Label className="text-base font-medium">Area Type</Label>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setState({ ...state, area_mode: "city" })}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border-2 transition-all ${
                  state.area_mode === "city"
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-border hover:border-primary/50"
                }`}
                aria-pressed={state.area_mode === "city"}
              >
                <MapPin className="w-4 h-4" />
                <span className="font-medium">City</span>
              </button>
              <button
                type="button"
                onClick={() => setState({ ...state, area_mode: "zips" })}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border-2 transition-all ${
                  state.area_mode === "zips"
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-border hover:border-primary/50"
                }`}
                aria-pressed={state.area_mode === "zips"}
              >
                <Hash className="w-4 h-4" />
                <span className="font-medium">ZIP Codes</span>
              </button>
              <div className="relative">
                <button
                  type="button"
                  disabled
                  className="flex items-center gap-2 px-4 py-2.5 rounded-lg border-2 border-border bg-muted/50 text-muted-foreground cursor-not-allowed opacity-60"
                  aria-label="Polygon selection (coming soon)"
                  title="Polygon selection coming soon"
                >
                  <PolygonIcon className="w-4 h-4" />
                  <span className="font-medium">Polygon</span>
                  <Info className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          {/* City Input */}
          {state.area_mode === "city" && (
            <div className="space-y-2">
              <Label htmlFor="city" className="text-base font-medium">
                City Name
              </Label>
              <Input
                id="city"
                type="text"
                placeholder="e.g., San Francisco"
                value={state.city}
                onChange={(e) => setState({ ...state, city: e.target.value })}
                className="text-base"
                aria-required="true"
              />
              <p className="text-xs text-muted-foreground">Enter the city name for your market report</p>
            </div>
          )}

          {/* ZIP Codes Input */}
          {state.area_mode === "zips" && (
            <div className="space-y-3">
              <Label htmlFor="zip-input" className="text-base font-medium">
                ZIP Codes
              </Label>
              <div className="flex gap-2">
                <Input
                  id="zip-input"
                  type="text"
                  placeholder="Enter 5-digit ZIP"
                  value={zipInput}
                  onChange={(e) => setZipInput(e.target.value.replace(/\D/g, "").slice(0, 5))}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault()
                      addZip()
                    }
                  }}
                  className="text-base"
                  maxLength={5}
                  aria-required="true"
                />
                <Button type="button" onClick={addZip} disabled={!zipInput || zipInput.length !== 5}>
                  Add
                </Button>
              </div>
              {state.zips.length > 0 && (
                <div className="flex flex-wrap gap-2 p-3 rounded-lg bg-muted/50 border border-border">
                  {state.zips.map((zip) => (
                    <Badge key={zip} variant="secondary" className="gap-1.5 pl-3 pr-2 py-1.5 text-sm">
                      {zip}
                      <button
                        type="button"
                        onClick={() => removeZip(zip)}
                        className="hover:bg-background/50 rounded-sm p-0.5 transition-colors"
                        aria-label={`Remove ZIP ${zip}`}
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
              <p className="text-xs text-muted-foreground">Add one or more ZIP codes to include in your report</p>
            </div>
          )}

          {/* Polygon Disabled Message */}
          {state.area_mode === "polygon" && (
            <div className="p-4 rounded-lg bg-muted/50 border border-border">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-muted-foreground mt-0.5" />
                <div>
                  <p className="font-medium text-sm mb-1">Polygon Selection Coming Soon</p>
                  <p className="text-sm text-muted-foreground">
                    Custom polygon drawing will be available in a future update. Please use City or ZIP codes for now.
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// Step 3: Filters
function StepFilters({ state, setState }: { state: WizardState; setState: (s: WizardState) => void }) {
  const updateFilter = (key: keyof WizardFilters, value: any) => {
    setState({
      ...state,
      filters: { ...state.filters, [key]: value },
    })
  }

  const incrementValue = (key: "beds" | "baths") => {
    const current = state.filters[key] || 0
    updateFilter(key, Math.min(current + 1, 10))
  }

  const decrementValue = (key: "beds" | "baths") => {
    const current = state.filters[key] || 0
    updateFilter(key, Math.max(current - 1, 0))
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Refine Filters</h2>
        <p className="text-sm text-muted-foreground">Customize your report criteria and data range</p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-6">
          {/* Lookback Period */}
          <div className="space-y-3">
            <Label className="text-base font-medium">
              Lookback Period <span className="text-destructive">*</span>
            </Label>
            <div className="flex flex-wrap gap-2">
              {lookbackOptions.map((option) => (
                <button
                  key={option.days}
                  type="button"
                  onClick={() => setState({ ...state, lookback_days: option.days })}
                  className={`px-4 py-2.5 rounded-lg border-2 font-medium transition-all ${
                    state.lookback_days === option.days
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border hover:border-primary/50"
                  }`}
                  aria-pressed={state.lookback_days === option.days}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">Select how far back to include data in your report</p>
          </div>

          {/* Property Type */}
          <div className="space-y-3">
            <Label className="text-base font-medium">Property Type</Label>
            <div className="flex flex-wrap gap-2">
              {propertyTypes.map((type) => (
                <button
                  key={type.id}
                  type="button"
                  onClick={() => updateFilter("type", state.filters.type === type.id ? undefined : type.id)}
                  className={`px-4 py-2.5 rounded-lg border-2 font-medium transition-all ${
                    state.filters.type === type.id
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border hover:border-primary/50"
                  }`}
                  aria-pressed={state.filters.type === type.id}
                >
                  {type.label}
                </button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">Filter by property type (optional)</p>
          </div>

          {/* Price Range */}
          <div className="space-y-3">
            <Label className="text-base font-medium">Price Range</Label>
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="minprice" className="text-sm text-muted-foreground">
                  Minimum Price
                </Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
                  <Input
                    id="minprice"
                    type="number"
                    placeholder="0"
                    value={state.filters.minprice || ""}
                    onChange={(e) => {
                      const val = e.target.value ? Math.max(0, Number.parseInt(e.target.value)) : undefined
                      updateFilter("minprice", val)
                    }}
                    className="pl-7"
                    min="0"
                    step="10000"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxprice" className="text-sm text-muted-foreground">
                  Maximum Price
                </Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
                  <Input
                    id="maxprice"
                    type="number"
                    placeholder="No limit"
                    value={state.filters.maxprice || ""}
                    onChange={(e) => {
                      const val = e.target.value ? Math.max(0, Number.parseInt(e.target.value)) : undefined
                      updateFilter("maxprice", val)
                    }}
                    className="pl-7"
                    min="0"
                    step="10000"
                  />
                </div>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">Set price boundaries for properties (optional)</p>
          </div>

          {/* Beds & Baths */}
          <div className="space-y-3">
            <Label className="text-base font-medium">Bedrooms & Bathrooms</Label>
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="beds" className="text-sm text-muted-foreground">
                  Minimum Bedrooms
                </Label>
                <div className="flex items-center gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={() => decrementValue("beds")}
                    disabled={(state.filters.beds || 0) === 0}
                    aria-label="Decrease bedrooms"
                  >
                    <Minus className="w-4 h-4" />
                  </Button>
                  <div className="flex-1 text-center">
                    <span className="text-2xl font-display font-semibold">{state.filters.beds || 0}</span>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={() => incrementValue("beds")}
                    disabled={(state.filters.beds || 0) >= 10}
                    aria-label="Increase bedrooms"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="baths" className="text-sm text-muted-foreground">
                  Minimum Bathrooms
                </Label>
                <div className="flex items-center gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={() => decrementValue("baths")}
                    disabled={(state.filters.baths || 0) === 0}
                    aria-label="Decrease bathrooms"
                  >
                    <Minus className="w-4 h-4" />
                  </Button>
                  <div className="flex-1 text-center">
                    <span className="text-2xl font-display font-semibold">{state.filters.baths || 0}</span>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={() => incrementValue("baths")}
                    disabled={(state.filters.baths || 0) >= 10}
                    aria-label="Increase bathrooms"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">Set minimum bed/bath requirements (optional)</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Step 4: Review
function StepReview({ state }: { state: WizardState }) {
  const payload = buildPayload(state)
  const selectedType = reportTypes.find((t) => t.id === state.report_type)

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Review & Generate</h2>
        <p className="text-sm text-muted-foreground">Verify your report configuration before generating</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-display">Report Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Report Type</p>
                <p className="font-medium">{selectedType?.name}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Area</p>
                {state.area_mode === "city" && <p className="font-medium">{state.city}</p>}
                {state.area_mode === "zips" && (
                  <div className="flex flex-wrap gap-1.5">
                    {state.zips.map((zip) => (
                      <Badge key={zip} variant="secondary">
                        {zip}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Lookback Period</p>
                <p className="font-medium">{state.lookback_days} days</p>
              </div>
              {state.filters.type && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Property Type</p>
                  <p className="font-medium">{propertyTypes.find((t) => t.id === state.filters.type)?.label}</p>
                </div>
              )}
              {(state.filters.minprice || state.filters.maxprice) && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Price Range</p>
                  <p className="font-medium">
                    {state.filters.minprice ? `$${state.filters.minprice.toLocaleString()}` : "$0"} -{" "}
                    {state.filters.maxprice ? `$${state.filters.maxprice.toLocaleString()}` : "No limit"}
                  </p>
                </div>
              )}
              {(state.filters.beds || state.filters.baths) && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Minimum Beds/Baths</p>
                  <p className="font-medium">
                    {state.filters.beds || 0} beds, {state.filters.baths || 0} baths
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Payload Preview */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-display">API Payload</CardTitle>
            <CardDescription>POST /v1/reports</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="text-xs bg-muted p-4 rounded-lg overflow-x-auto border border-border">
              <code>{JSON.stringify(payload, null, 2)}</code>
            </pre>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Main Wizard Component
export default function Wizard({ onSubmit, onCancel }: WizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [state, setState] = useState<WizardState>({
    report_type: null,
    area_mode: "city",
    city: "",
    zips: [],
    polygon: null,
    lookback_days: 30,
    filters: {},
  })

  const handleNext = () => {
    const validation = validateStep(state, currentStep)
    if (!validation.ok) {
      setError(validation.error || "Please complete all required fields")
      return
    }
    setError(null)
    setCurrentStep((prev) => Math.min(prev + 1, steps.length - 1))
  }

  const handleBack = () => {
    setError(null)
    setCurrentStep((prev) => Math.max(prev - 1, 0))
  }

  const handleSubmit = () => {
    const validation = validateStep(state, currentStep)
    if (!validation.ok) {
      setError(validation.error || "Please complete all required fields")
      return
    }
    const payload = buildPayload(state)
    onSubmit(payload)
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-3xl mb-2">Create New Report</h1>
          <p className="text-muted-foreground">Generate a custom market report with live MLS data</p>
        </div>
        <Button variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>

      <Stepper steps={steps} currentStep={currentStep} />

      {error && (
        <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive" role="alert">
          <p className="font-medium text-sm">{error}</p>
        </div>
      )}

      <div className="min-h-[400px]">
        {currentStep === 0 && <StepType state={state} setState={setState} />}
        {currentStep === 1 && <StepArea state={state} setState={setState} />}
        {currentStep === 2 && <StepFilters state={state} setState={setState} />}
        {currentStep === 3 && <StepReview state={state} />}
      </div>

      <div className="flex justify-between pt-4 border-t border-border">
        <Button variant="outline" onClick={handleBack} disabled={currentStep === 0} className="gap-2 bg-transparent">
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>
        {currentStep < steps.length - 1 ? (
          <Button onClick={handleNext} className="gap-2">
            Next
            <ArrowRight className="w-4 h-4" />
          </Button>
        ) : (
          <Button onClick={handleSubmit} className="gap-2 bg-primary">
            <FileText className="w-4 h-4" />
            Generate Report
          </Button>
        )}
      </div>
    </div>
  )
}
