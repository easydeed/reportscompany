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
  Users,
  Check,
} from "lucide-react"
import { cn } from "../lib/utils"

// Import shared types and presets from schedules module
import { 
  type ReportType, 
  type ReportFilters, 
  AUDIENCE_OPTIONS,
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

  // Build filters - include ALL filter properties
  const filters: ReportFilters = {}
  if (state.filters.minbeds) filters.minbeds = state.filters.minbeds
  if (state.filters.minbaths) filters.minbaths = state.filters.minbaths
  if (state.filters.minprice) filters.minprice = state.filters.minprice
  if (state.filters.maxprice) filters.maxprice = state.filters.maxprice
  if (state.filters.subtype) filters.subtype = state.filters.subtype
  // Include market-adaptive price_strategy
  if (state.filters.price_strategy) filters.price_strategy = state.filters.price_strategy
  // Include preset_display_name for PDF headers
  if (state.filters.preset_display_name) filters.preset_display_name = state.filters.preset_display_name

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
  { id: "type", label: "Report" },
  { id: "area", label: "Area" },
  { id: "review", label: "Review" },
]

const lookbackOptions = [7, 14, 30, 60, 90]

// Three main report categories
type ReportTab = "new_listings" | "market_update" | "closed_sales"

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

// Step 1: Simplified Report Selection (Three Cards + Pill Audience Selector)
function StepBasics({
  state,
  setState,
  setError,
}: {
  state: WizardState
  setState: (s: WizardState) => void
  setError: (e: string | null) => void
}) {
  const [activeTab, setActiveTab] = useState<ReportTab>("new_listings")
  const [selectedAudience, setSelectedAudience] = useState<string>("all")

  // Handle tab selection
  const handleTabSelect = (tab: ReportTab) => {
    setActiveTab(tab)
    if (tab === "new_listings") {
      const audience = AUDIENCE_OPTIONS.find(a => a.key === selectedAudience) || AUDIENCE_OPTIONS[0]
      setState({
        ...state,
        report_type: "new_listings_gallery",
        filters: audience.filters,
        preset_key: selectedAudience !== "all" ? selectedAudience : undefined
      })
    } else if (tab === "market_update") {
      setState({
        ...state,
        report_type: "market_snapshot",
        filters: {},
        preset_key: undefined
      })
    } else if (tab === "closed_sales") {
      setState({
        ...state,
        report_type: "closed",
        filters: {},
        preset_key: undefined
      })
    }
    setError(null)
  }

  // Handle audience selection
  const handleAudienceChange = (audienceKey: string) => {
    setSelectedAudience(audienceKey)
    const audience = AUDIENCE_OPTIONS.find(a => a.key === audienceKey) || AUDIENCE_OPTIONS[0]
    setState({
      ...state,
      report_type: "new_listings_gallery",
      filters: audience.filters,
      preset_key: audienceKey !== "all" ? audienceKey : undefined
    })
    setError(null)
  }

  // Initialize on mount
  useState(() => {
    if (!state.report_type) {
      handleTabSelect("new_listings")
    }
  })

  const selectedAudienceOption = AUDIENCE_OPTIONS.find(a => a.key === selectedAudience)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">What do you want to share?</h2>
        <p className="text-sm text-muted-foreground">Choose a report type to generate</p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-6">
          {/* Three Report Type Cards */}
          <div className="space-y-3">
            <Label>Report Type <span className="text-destructive">*</span></Label>
            <div className="grid grid-cols-3 gap-3">
              {/* New Listings */}
              <button
                type="button"
                onClick={() => handleTabSelect("new_listings")}
                className={cn(
                  "relative flex flex-col items-center p-4 rounded-xl border-2 transition-all text-center",
                  activeTab === "new_listings"
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-muted-foreground/50"
                )}
              >
                {activeTab === "new_listings" && (
                  <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                    <Check className="w-3 h-3 text-primary-foreground" />
                  </div>
                )}
                <div className={cn(
                  "w-12 h-12 rounded-xl flex items-center justify-center mb-2",
                  activeTab === "new_listings" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                )}>
                  <Image className="w-6 h-6" />
                </div>
                <span className={cn("font-semibold text-sm", activeTab === "new_listings" && "text-primary")}>New Listings</span>
                <span className="text-xs text-muted-foreground mt-0.5">Photo gallery</span>
              </button>

              {/* Market Update */}
              <button
                type="button"
                onClick={() => handleTabSelect("market_update")}
                className={cn(
                  "relative flex flex-col items-center p-4 rounded-xl border-2 transition-all text-center",
                  activeTab === "market_update"
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-muted-foreground/50"
                )}
              >
                {activeTab === "market_update" && (
                  <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                    <Check className="w-3 h-3 text-primary-foreground" />
                  </div>
                )}
                <div className={cn(
                  "w-12 h-12 rounded-xl flex items-center justify-center mb-2",
                  activeTab === "market_update" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                )}>
                  <TrendingUp className="w-6 h-6" />
                </div>
                <span className={cn("font-semibold text-sm", activeTab === "market_update" && "text-primary")}>Market Update</span>
                <span className="text-xs text-muted-foreground mt-0.5">Stats & trends</span>
              </button>

              {/* Closed Sales */}
              <button
                type="button"
                onClick={() => handleTabSelect("closed_sales")}
                className={cn(
                  "relative flex flex-col items-center p-4 rounded-xl border-2 transition-all text-center",
                  activeTab === "closed_sales"
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-muted-foreground/50"
                )}
              >
                {activeTab === "closed_sales" && (
                  <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                    <Check className="w-3 h-3 text-primary-foreground" />
                  </div>
                )}
                <div className={cn(
                  "w-12 h-12 rounded-xl flex items-center justify-center mb-2",
                  activeTab === "closed_sales" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                )}>
                  <DollarSign className="w-6 h-6" />
                </div>
                <span className={cn("font-semibold text-sm", activeTab === "closed_sales" && "text-primary")}>Closed Sales</span>
                <span className="text-xs text-muted-foreground mt-0.5">Recent solds</span>
              </button>
            </div>
          </div>

          {/* Audience Pill Buttons - Only for New Listings */}
          {activeTab === "new_listings" && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-muted-foreground" />
                <Label className="text-sm">Who is this for?</Label>
              </div>
              <div className="flex flex-wrap gap-2">
                {AUDIENCE_OPTIONS.map((audience) => {
                  const isSelected = selectedAudience === audience.key
                  return (
                    <button
                      key={audience.key}
                      type="button"
                      onClick={() => handleAudienceChange(audience.key)}
                      className={cn(
                        "px-3 py-2 rounded-lg text-sm font-medium transition-all border",
                        isSelected
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-background text-foreground border-border hover:border-muted-foreground"
                      )}
                    >
                      {audience.name}
                    </button>
                  )
                })}
              </div>
              
              {/* Show applied filters as subtle hint */}
              {selectedAudience !== "all" && selectedAudienceOption && (
                <p className="text-xs text-muted-foreground pl-1">
                  {selectedAudienceOption.description}
                </p>
              )}
            </div>
          )}

          {/* Lookback Period */}
          <div className="space-y-3">
            <Label>Time Period <span className="text-destructive">*</span></Label>
            <div className="flex flex-wrap gap-2">
              {lookbackOptions.map((days) => (
                <button
                  key={days}
                  type="button"
                  onClick={() => setState({ ...state, lookback_days: days })}
                  className={cn(
                    "px-4 py-2 rounded-lg border font-medium text-sm transition-all",
                    state.lookback_days === days
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-background border-border hover:border-muted-foreground"
                  )}
                >
                  {days} days
                </button>
              ))}
            </div>
          </div>
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

// Step 3: Review - Simplified version
function StepReview({ state }: { state: WizardState }) {
  const isNewListings = state.report_type === "new_listings_gallery" || state.report_type === "featured_listings"
  const isMarketUpdate = state.report_type === "market_snapshot"
  const isClosedSales = state.report_type === "closed"
  
  // Get audience name from filters
  const audienceName = state.filters?.preset_display_name || (isNewListings ? "All Listings" : null)
  
  const hasFilters = state.filters && Object.keys(state.filters).filter(k => k !== 'preset_display_name').length > 0

  // Get report display name and icon
  const getReportInfo = () => {
    if (isNewListings) return { name: "New Listings", icon: Image, color: "bg-primary" }
    if (isMarketUpdate) return { name: "Market Update", icon: TrendingUp, color: "bg-primary" }
    if (isClosedSales) return { name: "Closed Sales", icon: DollarSign, color: "bg-primary" }
    return { name: "Report", icon: FileText, color: "bg-primary" }
  }
  
  const reportInfo = getReportInfo()
  const ReportIcon = reportInfo.icon

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Ready to generate!</h2>
        <p className="text-sm text-muted-foreground">Review your report settings</p>
      </div>

      {/* Main Summary Card */}
      <div className="relative overflow-hidden rounded-2xl border-2 border-primary/20 bg-gradient-to-br from-primary/5 via-background to-background">
        {/* Header with report type */}
        <div className="flex items-center gap-4 p-5 border-b border-primary/10">
          <div className={cn("w-14 h-14 rounded-xl flex items-center justify-center", reportInfo.color)}>
            <ReportIcon className="w-7 h-7 text-primary-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">Report</p>
            <h3 className="font-display font-bold text-xl truncate">{reportInfo.name}</h3>
            {audienceName && audienceName !== "All Listings" && (
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="secondary" className="text-xs bg-primary/10 text-primary">
                  <Users className="w-3 h-3 mr-1" />
                  {audienceName}
                </Badge>
              </div>
            )}
          </div>
        </div>

        {/* Details Grid */}
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
                <Calendar className="w-4 h-4 text-green-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Time Period</p>
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

          {/* Filters Summary - only if audience filters applied */}
          {hasFilters && (
            <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-4 h-4 text-primary" />
                <span className="text-xs font-medium text-primary">Audience Filters</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {state.filters.minbeds && (
                  <Badge variant="outline" className="text-xs">{state.filters.minbeds}+ Beds</Badge>
                )}
                {state.filters.minbaths && (
                  <Badge variant="outline" className="text-xs">{state.filters.minbaths}+ Baths</Badge>
                )}
                {state.filters.price_strategy?.mode === "maxprice_pct_of_median_list" && (
                  <Badge variant="outline" className="text-xs text-blue-600 border-blue-200 bg-blue-50">
                    ≤{Math.round(state.filters.price_strategy.value * 100)}% of median
                  </Badge>
                )}
                {state.filters.price_strategy?.mode === "minprice_pct_of_median_list" && (
                  <Badge variant="outline" className="text-xs text-blue-600 border-blue-200 bg-blue-50">
                    ≥{Math.round(state.filters.price_strategy.value * 100)}% of median
                  </Badge>
                )}
                {state.filters.subtype && (
                  <Badge variant="outline" className="text-xs">
                    {state.filters.subtype === "SingleFamilyResidence" ? "Single Family" : "Condos"}
                  </Badge>
                )}
              </div>
              {state.filters.price_strategy && (
                <p className="text-[10px] text-muted-foreground mt-2">
                  💡 Price auto-adjusts based on {state.city || "area"}'s market
                </p>
              )}
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
