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
  Sparkles,
  LayoutGrid,
} from "lucide-react"
import { cn } from "../lib/utils"

// Import shared types and presets from schedules module
import { 
  type ReportType, 
  type ReportFilters, 
  type PresetDefinition,
  SMART_PRESETS 
} from "./schedules/types"

export type AreaMode = "city" | "zips"

export interface ReportPayload {
  report_type: ReportType
  city?: string
  zips?: string[]
  lookback_days: number
  filters?: ReportFilters
  preset_key?: string // Track which preset was used
}

interface WizardState {
  report_type: ReportType | null
  area_mode: AreaMode
  city: string
  zips: string[]
  lookback_days: number
  filters: ReportFilters
  preset_key?: string
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

  // Only include filters if they have values
  const filters: ReportFilters = {}
  if (state.filters.minbeds) filters.minbeds = state.filters.minbeds
  if (state.filters.minbaths) filters.minbaths = state.filters.minbaths
  if (state.filters.minprice) filters.minprice = state.filters.minprice
  if (state.filters.maxprice) filters.maxprice = state.filters.maxprice
  if (state.filters.subtype) filters.subtype = state.filters.subtype

  if (Object.keys(filters).length > 0) {
    payload.filters = filters
  }

  if (state.preset_key) {
    payload.preset_key = state.preset_key
  }

  return payload
}

// Validation for each step
function validateStep(state: WizardState, step: number): { valid: boolean; error?: string } {
  switch (step) {
    case 0:
      if (!state.report_type) return { valid: false, error: "Select a report type" }
      return { valid: true }
    case 1:
      if (state.area_mode === "city") {
        return state.city.trim() ? { valid: true } : { valid: false, error: "Enter a city name" }
      } else {
        return state.zips.length > 0 && state.zips.length <= 10
          ? { valid: true }
          : { valid: false, error: state.zips.length === 0 ? "Add at least one ZIP" : "Maximum 10 ZIPs allowed" }
      }
    case 2:
      return { valid: true }
    default:
      return { valid: false }
  }
}

const steps = [
  { id: "type", label: "Basics" },
  { id: "area", label: "Area" },
  { id: "review", label: "Review" },
]

const reportTypes = [
  { id: "market_snapshot" as ReportType, name: "Market Snapshot", icon: TrendingUp, description: "Complete market overview" },
  { id: "new_listings" as ReportType, name: "New Listings", icon: Home, description: "Recently listed properties" },
  { id: "inventory" as ReportType, name: "Inventory Report", icon: BarChart3, description: "Active listings analysis" },
  { id: "closed" as ReportType, name: "Closed Sales", icon: DollarSign, description: "Recent sold properties" },
  { id: "new_listings_gallery" as ReportType, name: "Photo Gallery", icon: Image, description: "Visual listing showcase" },
  { id: "featured_listings" as ReportType, name: "Featured Listings", icon: Star, description: "Highlighted properties" },
]

const lookbackOptions = [7, 14, 30, 60, 90]

// Tab type for Step 1
type ReportTab = "presets" | "standard"

export function NewReportWizard({ onSubmit, onCancel }: NewReportWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [state, setState] = useState<WizardState>({
    report_type: null,
    area_mode: "city",
    city: "",
    zips: [],
    lookback_days: 30,
    filters: {},
    preset_key: undefined,
  })
  const [error, setError] = useState<string | null>(null)

  const handleNext = () => {
    const validation = validateStep(state, currentStep)
    if (!validation.valid) {
      setError(validation.error || "Please complete this step")
      return
    }
    setError(null)
    if (currentStep < steps.length - 1) {
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
        {currentStep === 0 && <StepBasics state={state} setState={setState} setError={setError} />}
        {currentStep === 1 && <StepArea state={state} setState={setState} setError={setError} />}
        {currentStep === 2 && <StepReview state={state} />}
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

// Step 1: Basics (with Tabs - identical styling to ScheduleWizard)
function StepBasics({
  state,
  setState,
  setError,
}: {
  state: WizardState
  setState: (s: WizardState) => void
  setError: (e: string | null) => void
}) {
  const [activeTab, setActiveTab] = useState<ReportTab>("presets")

  // Handle preset selection - auto-fills form
  const handlePresetSelect = (presetKey: string) => {
    const preset = SMART_PRESETS.find(p => p.key === presetKey)
    if (!preset) return
    
    setState({
      ...state,
      report_type: preset.report_type,
      lookback_days: preset.lookback_days,
      filters: preset.filters,
      preset_key: presetKey
    })
    setError(null)
  }

  // Handle standard report type selection
  const handleReportTypeSelect = (reportType: ReportType) => {
    setState({
      ...state,
      report_type: reportType,
      filters: {},
      preset_key: undefined
    })
    setError(null)
  }

  // Check if a preset is selected
  const isPresetSelected = (presetKey: string) => state.preset_key === presetKey

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Report Basics</h2>
        <p className="text-sm text-muted-foreground">Choose a preset or select a standard report type</p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-6">
          {/* Tab Toggle - identical to ScheduleWizard */}
          <div className="space-y-3">
            <Label>
              Report Type <span className="text-destructive">*</span>
            </Label>
            
            {/* Tab Buttons */}
            <div className="flex gap-2 p-1 bg-muted/50 rounded-lg w-fit">
              <button
                type="button"
                onClick={() => setActiveTab("presets")}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-md font-medium text-sm transition-all",
                  activeTab === "presets"
                    ? "bg-background text-primary shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Sparkles className="w-4 h-4" />
                Smart Presets
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("standard")}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-md font-medium text-sm transition-all",
                  activeTab === "standard"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <LayoutGrid className="w-4 h-4" />
                Standard Reports
              </button>
            </div>

            {/* Smart Presets Tab */}
            {activeTab === "presets" && (
              <div className="space-y-3">
                <p className="text-xs text-muted-foreground">
                  Pre-configured reports for common audiences. Filters and settings are auto-filled.
                </p>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {SMART_PRESETS.map((preset) => {
                    const isSelected = isPresetSelected(preset.key)
                    return (
                      <button
                        key={preset.key}
                        type="button"
                        onClick={() => handlePresetSelect(preset.key)}
                        className={cn(
                          "group relative flex flex-col p-4 rounded-xl border-2 transition-all text-left",
                          isSelected
                            ? "border-primary bg-gradient-to-br from-primary/10 to-primary/5 shadow-md shadow-primary/10"
                            : "border-border hover:border-primary/50 hover:shadow-sm"
                        )}
                        aria-pressed={isSelected}
                      >
                        {isSelected && (
                          <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                        )}
                        <div className={cn(
                          "w-10 h-10 rounded-xl flex items-center justify-center mb-2 text-xl transition-colors",
                          isSelected ? "bg-primary/20" : "bg-muted"
                        )}>
                          {preset.icon}
                        </div>
                        <span className="font-semibold text-sm">{preset.name}</span>
                        <span className="text-xs text-muted-foreground mt-0.5">{preset.tagline}</span>
                        {/* Show what's included */}
                        <div className="flex flex-wrap gap-1 mt-2">
                          {preset.filters.minbeds && (
                            <Badge variant="outline" className="text-[10px] px-1.5 py-0">{preset.filters.minbeds}+ bed</Badge>
                          )}
                          {preset.filters.maxprice && (
                            <Badge variant="outline" className="text-[10px] px-1.5 py-0">≤${(preset.filters.maxprice/1000000).toFixed(1)}M</Badge>
                          )}
                          {preset.filters.minprice && (
                            <Badge variant="outline" className="text-[10px] px-1.5 py-0">≥${(preset.filters.minprice/1000000).toFixed(1)}M</Badge>
                          )}
                          {preset.filters.subtype === "Condominium" && (
                            <Badge variant="outline" className="text-[10px] px-1.5 py-0">Condo</Badge>
                          )}
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Standard Reports Tab */}
            {activeTab === "standard" && (
              <div className="space-y-3">
                <p className="text-xs text-muted-foreground">
                  Classic reports without pre-configured filters. Full control over settings.
                </p>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {reportTypes.map((type) => {
                    const Icon = type.icon
                    const isSelected = state.report_type === type.id && !state.preset_key
                    return (
                      <button
                        key={type.id}
                        type="button"
                        onClick={() => handleReportTypeSelect(type.id)}
                        className={cn(
                          "group relative flex flex-col p-4 rounded-xl border-2 transition-all text-left",
                          isSelected
                            ? "border-primary bg-primary/5 shadow-md shadow-primary/10"
                            : "border-border hover:border-primary/50 hover:shadow-sm"
                        )}
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
                          className={cn(
                            "w-10 h-10 rounded-xl flex items-center justify-center mb-2 transition-colors",
                            isSelected
                              ? "bg-primary text-primary-foreground"
                              : "bg-primary/10 text-primary group-hover:bg-primary/15"
                          )}
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
            )}
          </div>

          {/* Lookback Period - identical to ScheduleWizard */}
          <div className="space-y-3">
            <Label>
              Lookback Period <span className="text-destructive">*</span>
            </Label>
            <div className="flex flex-wrap gap-2">
              {lookbackOptions.map((days) => (
                <button
                  key={days}
                  type="button"
                  onClick={() => setState({ ...state, lookback_days: days })}
                  className={cn(
                    "px-4 py-2.5 rounded-lg border-2 font-medium transition-all",
                    state.lookback_days === days
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border hover:border-primary/50"
                  )}
                  aria-pressed={state.lookback_days === days}
                >
                  {days} days
                </button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">How far back to include data in your report</p>
          </div>

          {/* Filters Summary (show when preset is selected) */}
          {state.preset_key && state.filters && Object.keys(state.filters).length > 0 && (
            <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium text-primary">Preset Filters Applied</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {state.filters.minbeds && (
                  <Badge variant="secondary">{state.filters.minbeds}+ Bedrooms</Badge>
                )}
                {state.filters.minbaths && (
                  <Badge variant="secondary">{state.filters.minbaths}+ Bathrooms</Badge>
                )}
                {state.filters.minprice && (
                  <Badge variant="secondary">Min ${state.filters.minprice.toLocaleString()}</Badge>
                )}
                {state.filters.maxprice && (
                  <Badge variant="secondary">Max ${state.filters.maxprice.toLocaleString()}</Badge>
                )}
                {state.filters.subtype && (
                  <Badge variant="secondary">
                    {state.filters.subtype === "SingleFamilyResidence" ? "Single Family" : "Condo"}
                  </Badge>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// Step 2: Area - identical styling to ScheduleWizard
function StepArea({
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
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// Step 3: Review - identical styling to ScheduleWizard
function StepReview({ state }: { state: WizardState }) {
  const selectedType = reportTypes.find((t) => t.id === state.report_type)
  const selectedPreset = state.preset_key ? SMART_PRESETS.find(p => p.key === state.preset_key) : null
  const TypeIcon = selectedType?.icon || FileText

  const hasFilters = state.filters && Object.keys(state.filters).length > 0

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Ready to generate!</h2>
        <p className="text-sm text-muted-foreground">Review your report settings below</p>
      </div>

      {/* Main Summary Card - identical to ScheduleWizard */}
      <div className="relative overflow-hidden rounded-2xl border-2 border-primary/20 bg-gradient-to-br from-primary/5 via-background to-background">
        {/* Header with report type */}
        <div className="flex items-center gap-4 p-5 border-b border-primary/10">
          {selectedPreset ? (
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center shadow-lg shadow-primary/10 text-2xl">
              {selectedPreset.icon}
            </div>
          ) : (
            <div className="w-14 h-14 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
              <TypeIcon className="w-7 h-7 text-white" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">Report</p>
              {selectedPreset && (
                <Badge variant="secondary" className="text-[10px] bg-primary/10 text-primary">
                  <Sparkles className="w-3 h-3 mr-1" />
                  Smart Preset
                </Badge>
              )}
            </div>
            <h3 className="font-display font-bold text-xl truncate">
              {selectedPreset?.name || selectedType?.name}
            </h3>
            {selectedPreset && (
              <p className="text-sm text-muted-foreground">{selectedType?.name}</p>
            )}
          </div>
        </div>

        {/* Details Grid - gap-3 to match ScheduleWizard */}
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {/* Location */}
            <div className="flex items-start gap-3 p-3 rounded-lg bg-background/80 border border-border/50">
              <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                <MapPin className="w-4 h-4 text-blue-600" />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">Location</p>
                <p className="font-semibold text-sm truncate">
                  {state.area_mode === "city" ? state.city : `${state.zips.length} ZIP codes`}
                </p>
              </div>
            </div>

            {/* Time Period */}
            <div className="flex items-start gap-3 p-3 rounded-lg bg-background/80 border border-border/50">
              <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center flex-shrink-0">
                <BarChart3 className="w-4 h-4 text-green-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Data Range</p>
                <p className="font-semibold text-sm">Last {state.lookback_days} days</p>
              </div>
            </div>
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

          {/* Filters Summary (NEW) */}
          {hasFilters && (
            <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-primary" />
                <span className="text-xs font-medium text-primary">Filters Applied</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {state.filters.minbeds && (
                  <Badge variant="outline" className="text-xs">{state.filters.minbeds}+ Beds</Badge>
                )}
                {state.filters.minbaths && (
                  <Badge variant="outline" className="text-xs">{state.filters.minbaths}+ Baths</Badge>
                )}
                {state.filters.minprice && (
                  <Badge variant="outline" className="text-xs">≥${(state.filters.minprice/1000).toLocaleString()}K</Badge>
                )}
                {state.filters.maxprice && (
                  <Badge variant="outline" className="text-xs">≤${(state.filters.maxprice/1000).toLocaleString()}K</Badge>
                )}
                {state.filters.subtype && (
                  <Badge variant="outline" className="text-xs">
                    {state.filters.subtype === "SingleFamilyResidence" ? "Single Family" : "Condo"}
                  </Badge>
                )}
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
