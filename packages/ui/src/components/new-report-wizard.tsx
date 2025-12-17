"use client"

import { useState } from "react"
import { Button } from "./ui/button"
import { Card, CardContent } from "./ui/card"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { Badge } from "./ui/badge"
import { HorizontalStepper } from "./horizontal-stepper"
import {
  FileText,
  TrendingUp,
  Home,
  DollarSign,
  BarChart3,
  MapPin,
  Hash,
  X,
  ArrowRight,
  ArrowLeft,
  Image,
  Star,
  Calendar,
  Building,
} from "lucide-react"

// Types
// NOTE: ReportType is now imported from shared module to ensure consistency
// See apps/web/app/lib/reportTypes.ts for the canonical list
export type ReportType = 
  | "market_snapshot" 
  | "new_listings" 
  | "inventory" 
  | "closed" 
  | "price_bands" 
  | "open_houses" 
  | "new_listings_gallery" 
  | "featured_listings"

export type AreaMode = "city" | "zips"

export interface ReportPayload {
  report_type: ReportType
  city?: string
  zips?: string[]
  lookback_days: number
  filters?: {
    minprice?: number
    maxprice?: number
    type?: string
    subtype?: string
  }
}

interface WizardState {
  report_type: ReportType | null
  area_mode: AreaMode
  city: string
  zips: string[]
  lookback_days: number
  property_types: string[]
  property_subtype: string  // SingleFamilyResidence, Condominium, Townhouse, or empty for all
  minprice: string
  maxprice: string
}

interface NewReportWizardProps {
  onSubmit: (payload: ReportPayload) => void
  onCancel: () => void
}

// Helper function to build API payload
export function buildPayload(state: WizardState): ReportPayload {
  const payload: ReportPayload = {
    report_type: state.report_type!,
    lookback_days: state.lookback_days,
  }

  if (state.area_mode === "city" && state.city) {
    payload.city = state.city
  } else if (state.area_mode === "zips" && state.zips.length > 0) {
    payload.zips = state.zips
  }

  const filters: any = {}
  if (state.minprice) filters.minprice = Number.parseInt(state.minprice)
  if (state.maxprice) filters.maxprice = Number.parseInt(state.maxprice)
  if (state.property_types.length > 0) filters.type = state.property_types.join(",")
  if (state.property_subtype) filters.subtype = state.property_subtype

  if (Object.keys(filters).length > 0) {
    payload.filters = filters
  }

  return payload
}

// Validation for each step
function validateStep(state: WizardState, step: number): { valid: boolean; error?: string } {
  switch (step) {
    case 0:
      return state.report_type ? { valid: true } : { valid: false, error: "Select a report type" }
    case 1:
      if (state.area_mode === "city") {
        return state.city.trim() ? { valid: true } : { valid: false, error: "Enter a city name" }
      } else {
        return state.zips.length > 0 && state.zips.length <= 10
          ? { valid: true }
          : { valid: false, error: state.zips.length === 0 ? "Add at least one ZIP" : "Maximum 10 ZIPs allowed" }
      }
    case 2:
      return state.lookback_days > 0 ? { valid: true } : { valid: false, error: "Select a lookback period" }
    case 3:
      return { valid: true }
    default:
      return { valid: false }
  }
}

const steps = [
  { id: "type", label: "Type" },
  { id: "area", label: "Area" },
  { id: "options", label: "Options" },
  { id: "review", label: "Review" },
]

const reportTypes = [
  { id: "market_snapshot" as ReportType, name: "Market Snapshot", icon: TrendingUp, description: "Complete market overview" },
  { id: "new_listings" as ReportType, name: "New Listings", icon: Home, description: "Recently listed properties" },
  { id: "inventory" as ReportType, name: "Inventory Report", icon: BarChart3, description: "Active listings analysis" },
  { id: "closed" as ReportType, name: "Closed Sales", icon: DollarSign, description: "Recent sold properties" },
  { id: "new_listings_gallery" as ReportType, name: "Photo Gallery", icon: Image, description: "Visual listing showcase" },
  { id: "featured_listings" as ReportType, name: "Featured Listings", icon: Star, description: "Highlighted properties" },
  { id: "open_houses" as ReportType, name: "Open Houses", icon: Calendar, description: "Upcoming showings" },
]

const lookbackOptions = [7, 14, 30, 60, 90]

// Property types (broad category)
const propertyTypes = [
  { id: "RES", name: "Residential", icon: Home },
  { id: "CND", name: "Condo", icon: Building },
  { id: "MUL", name: "Multi-Family", icon: Building },
  { id: "LND", name: "Land", icon: MapPin },
  { id: "COM", name: "Commercial", icon: Building },
]

// Property subtypes (more specific - verified working with SimplyRETS)
const propertySubtypes = [
  { id: "", name: "All Types", description: "Include all property types" },
  { id: "SingleFamilyResidence", name: "Single Family", description: "Detached single-family homes" },
  { id: "Condominium", name: "Condo", description: "Condominiums" },
  { id: "Townhouse", name: "Townhouse", description: "Attached townhomes" },
]

export function NewReportWizard({ onSubmit, onCancel }: NewReportWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [state, setState] = useState<WizardState>({
    report_type: null,
    area_mode: "city",
    city: "",
    zips: [],
    lookback_days: 30,
    property_types: ["RES"],  // Default to Residential
    property_subtype: "",     // Empty = all subtypes
    minprice: "",
    maxprice: "",
  })
  const [error, setError] = useState<string | null>(null)

  const handleNext = () => {
    const validation = validateStep(state, currentStep)
    if (!validation.valid) {
      setError(validation.error || "Please complete this step")
      return
    }
    setError(null)
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    setError(null)
    setCurrentStep(Math.max(0, currentStep - 1))
  }

  const handleSubmit = () => {
    const payload = buildPayload(state)
    onSubmit(payload)
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-3xl mb-2">New Report</h1>
          <p className="text-muted-foreground">Generate a one-time market report</p>
        </div>
        <Button variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>

      <HorizontalStepper steps={steps} currentStep={currentStep} />

      {error && (
        <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive" role="alert">
          <p className="font-medium text-sm">{error}</p>
        </div>
      )}

      <div className="min-h-[400px]">
        {currentStep === 0 && <Step1ReportType state={state} setState={setState} setError={setError} />}
        {currentStep === 1 && <Step2Area state={state} setState={setState} setError={setError} />}
        {currentStep === 2 && <Step3Options state={state} setState={setState} setError={setError} />}
        {currentStep === 3 && <Step4Review state={state} />}
      </div>

      <div className="flex justify-between pt-4 border-t border-border">
        <Button variant="outline" onClick={handleBack} disabled={currentStep === 0} className="gap-2 h-11 bg-transparent">
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>
        {currentStep < steps.length - 1 ? (
          <Button onClick={handleNext} className="gap-2 h-11">
            Next
            <ArrowRight className="w-4 h-4" />
          </Button>
        ) : (
          <Button onClick={handleSubmit} className="gap-2 h-11">
            <FileText className="w-4 h-4" />
            Generate Report
          </Button>
        )}
      </div>
    </div>
  )
}

// Step 1: Report Type
function Step1ReportType({
  state,
  setState,
  setError,
}: {
  state: WizardState
  setState: (s: WizardState) => void
  setError: (e: string | null) => void
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">What type of report?</h2>
        <p className="text-sm text-muted-foreground">Select the analysis that fits your needs</p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {reportTypes.map((type) => {
          const Icon = type.icon
          const isSelected = state.report_type === type.id
          return (
            <button
              key={type.id}
              type="button"
              onClick={() => {
                setState({ ...state, report_type: type.id })
                setError(null)
              }}
              className={`group relative flex flex-col p-4 rounded-xl border-2 transition-all text-left ${
                isSelected
                  ? "border-primary bg-primary/5 shadow-md shadow-primary/10"
                  : "border-border hover:border-primary/50 hover:shadow-sm"
              }`}
              aria-pressed={isSelected}
            >
              {isSelected && (
                <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              )}
              <div
                className={`w-11 h-11 rounded-xl flex items-center justify-center mb-3 transition-colors ${
                  isSelected
                    ? "bg-primary text-primary-foreground"
                    : "bg-primary/10 text-primary group-hover:bg-primary/15"
                }`}
              >
                <Icon className="w-5 h-5" />
              </div>
              <span className="font-semibold text-sm">{type.name}</span>
              <span className="text-xs text-muted-foreground mt-0.5">{type.description}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

// Step 2: Area
function Step2Area({
  state,
  setState,
  setError,
}: {
  state: WizardState
  setState: (s: WizardState) => void
  setError: (e: string | null) => void
}) {
  const [zipInput, setZipInput] = useState("")

  const addZip = () => {
    const zip = zipInput.trim()
    if (zip && /^\d{5}$/.test(zip) && !state.zips.includes(zip) && state.zips.length < 10) {
      setState({ ...state, zips: [...state.zips, zip] })
      setZipInput("")
      setError(null)
    }
  }

  const removeZip = (zip: string) => {
    setState({ ...state, zips: state.zips.filter((z) => z !== zip) })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Select Area</h2>
        <p className="text-sm text-muted-foreground">Define the geographic area for your report</p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-6">
          <div className="space-y-3">
            <Label>Area Type</Label>
            <div className="flex gap-3">
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
            </div>
          </div>

          {state.area_mode === "city" && (
            <div className="space-y-2">
              <Label htmlFor="city">
                City Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="city"
                type="text"
                placeholder="e.g., San Francisco"
                value={state.city}
                onChange={(e) => {
                  setState({ ...state, city: e.target.value })
                  setError(null)
                }}
                aria-required="true"
                className="h-11"
              />
            </div>
          )}

          {state.area_mode === "zips" && (
            <div className="space-y-3">
              <Label htmlFor="zip-input">
                ZIP Codes <span className="text-destructive">*</span>
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
                  maxLength={5}
                  className="h-11"
                />
                <Button type="button" onClick={addZip} disabled={!zipInput || zipInput.length !== 5 || state.zips.length >= 10}>
                  Add
                </Button>
              </div>
              {state.zips.length > 0 && (
                <div className="flex flex-wrap gap-2 p-3 rounded-lg bg-muted/50 border border-border">
                  {state.zips.map((zip) => (
                    <Badge key={zip} variant="secondary" className="gap-1.5 pl-3 pr-2 py-1.5">
                      {zip}
                      <button
                        type="button"
                        onClick={() => removeZip(zip)}
                        className="hover:bg-background/50 rounded-sm p-0.5"
                        aria-label={`Remove ZIP ${zip}`}
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
              <p className="text-xs text-muted-foreground">Maximum 10 ZIP codes allowed</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// Step 3: Options
function Step3Options({
  state,
  setState,
  setError,
}: {
  state: WizardState
  setState: (s: WizardState) => void
  setError: (e: string | null) => void
}) {
  const togglePropertyType = (type: string) => {
    const types = state.property_types.includes(type)
      ? state.property_types.filter((t) => t !== type)
      : [...state.property_types, type]
    setState({ ...state, property_types: types })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Report Options</h2>
        <p className="text-sm text-muted-foreground">Refine your data parameters and filters</p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-6">
          {/* Lookback Period */}
          <div className="space-y-3">
            <Label>
              Lookback Period <span className="text-destructive">*</span>
            </Label>
            <div className="flex flex-wrap gap-2">
              {lookbackOptions.map((days) => (
                <button
                  key={days}
                  type="button"
                  onClick={() => {
                    setState({ ...state, lookback_days: days })
                    setError(null)
                  }}
                  className={`px-4 py-2.5 rounded-lg border-2 font-medium transition-all ${
                    state.lookback_days === days
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border hover:border-primary/50"
                  }`}
                  aria-pressed={state.lookback_days === days}
                >
                  {days} days
                </button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">How far back to include data in the report</p>
          </div>

          {/* Property SubType (More User-Friendly) */}
          <div className="space-y-3">
            <Label>Property Type</Label>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {propertySubtypes.map((subtype) => (
                <button
                  key={subtype.id}
                  type="button"
                  onClick={() => setState({ ...state, property_subtype: subtype.id })}
                  className={`flex flex-col items-start p-4 rounded-lg border-2 transition-all text-left ${
                    state.property_subtype === subtype.id
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-primary/50"
                  }`}
                  aria-pressed={state.property_subtype === subtype.id}
                >
                  <span className="font-medium">{subtype.name}</span>
                  <span className="text-xs text-muted-foreground mt-1">{subtype.description}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Price Range */}
          <div className="space-y-3">
            <Label>Price Range (optional)</Label>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="minprice" className="text-xs text-muted-foreground">
                  Minimum Price
                </Label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="minprice"
                    type="number"
                    placeholder="0"
                    value={state.minprice}
                    onChange={(e) => setState({ ...state, minprice: e.target.value })}
                    className="h-11 pl-9"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxprice" className="text-xs text-muted-foreground">
                  Maximum Price
                </Label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="maxprice"
                    type="number"
                    placeholder="No limit"
                    value={state.maxprice}
                    onChange={(e) => setState({ ...state, maxprice: e.target.value })}
                    className="h-11 pl-9"
                  />
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Step 4: Review
function Step4Review({ state }: { state: WizardState }) {
  const selectedType = reportTypes.find((t) => t.id === state.report_type)
  const selectedSubtype = propertySubtypes.find((t) => t.id === state.property_subtype)
  const TypeIcon = selectedType?.icon || FileText

  const formatPriceRange = () => {
    if (!state.minprice && !state.maxprice) return null
    const min = state.minprice ? `$${Number(state.minprice).toLocaleString()}` : "$0"
    const max = state.maxprice ? `$${Number(state.maxprice).toLocaleString()}` : "No limit"
    return `${min} – ${max}`
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Ready to generate!</h2>
        <p className="text-sm text-muted-foreground">Review your report settings below</p>
      </div>

      {/* Main Summary Card */}
      <div className="relative overflow-hidden rounded-2xl border-2 border-primary/20 bg-gradient-to-br from-primary/5 via-background to-background">
        {/* Header with report type */}
        <div className="flex items-center gap-4 p-5 border-b border-primary/10">
          <div className="w-14 h-14 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
            <TypeIcon className="w-7 h-7 text-white" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">Report Type</p>
            <h3 className="font-display font-bold text-xl">{selectedType?.name}</h3>
          </div>
        </div>

        {/* Details Grid */}
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {/* Location */}
            <div className="flex items-start gap-3 p-3 rounded-lg bg-background/80 border border-border/50">
              <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                <MapPin className="w-4 h-4 text-blue-600" />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">Location</p>
                <p className="font-semibold text-sm truncate">
                  {state.area_mode === "city" ? state.city : `${state.zips.length} ZIP code${state.zips.length !== 1 ? "s" : ""}`}
                </p>
              </div>
            </div>

            {/* Time Period */}
            <div className="flex items-start gap-3 p-3 rounded-lg bg-background/80 border border-border/50">
              <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center flex-shrink-0">
                <Calendar className="w-4 h-4 text-green-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Time Period</p>
                <p className="font-semibold text-sm">Last {state.lookback_days} days</p>
              </div>
            </div>

            {/* Property Type */}
            <div className="flex items-start gap-3 p-3 rounded-lg bg-background/80 border border-border/50">
              <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0">
                <Home className="w-4 h-4 text-purple-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Property Type</p>
                <p className="font-semibold text-sm">{selectedSubtype?.name || "All Types"}</p>
              </div>
            </div>

            {/* Price Range (if set) */}
            {formatPriceRange() && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-background/80 border border-border/50">
                <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <DollarSign className="w-4 h-4 text-amber-600" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Price Range</p>
                  <p className="font-semibold text-sm">{formatPriceRange()}</p>
                </div>
              </div>
            )}
          </div>

          {/* ZIP Codes List */}
          {state.area_mode === "zips" && state.zips.length > 0 && (
            <div className="p-3 rounded-lg bg-background/80 border border-border/50">
              <p className="text-xs text-muted-foreground mb-2">ZIP Codes</p>
              <div className="flex flex-wrap gap-1.5">
                {state.zips.map((zip) => (
                  <Badge key={zip} variant="secondary" className="bg-primary/10 text-primary font-mono">
                    {zip}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer hint */}
        <div className="px-5 py-3 bg-muted/30 border-t border-border/50">
          <p className="text-xs text-muted-foreground text-center">
            Click <strong>Generate Report</strong> to create your PDF
          </p>
        </div>
      </div>
    </div>
  )
}
