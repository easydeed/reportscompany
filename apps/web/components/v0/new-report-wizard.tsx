"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { SegmentedControl } from "./segmented-control"
import { TagInput } from "./tag-input"
import { cn } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"
import { Check, HelpCircle, ChevronRight, X } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

// Types
export type ReportType = "market_snapshot" | "new_listings" | "closed" | "inventory"
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
  }
}

interface WizardState {
  report_type: ReportType | null
  area_mode: AreaMode
  city: string
  zips: string[]
  lookback_days: number
  property_types: string[]
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

export function NewReportWizard({ onSubmit, onCancel }: NewReportWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [state, setState] = useState<WizardState>({
    report_type: null,
    area_mode: "city",
    city: "",
    zips: [],
    lookback_days: 30,
    property_types: [],
    minprice: "",
    maxprice: "",
  })
  const [error, setError] = useState<string | null>(null)

  const steps = [
    { number: 1, label: "Type" },
    { number: 2, label: "Area" },
    { number: 3, label: "Options" },
    { number: 4, label: "Review" },
  ]

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

  const handleSubmit = () => {
    const payload = buildPayload(state)
    onSubmit(payload)
  }

  const progress = ((currentStep + 1) / 4) * 100

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-display font-semibold text-foreground">New Report</h2>
          <p className="text-sm text-muted-foreground mt-1">Configure your market report parameters</p>
        </div>
        <Button variant="ghost" size="icon" onClick={onCancel} className="hover:bg-muted/50">
          <X className="w-5 h-5" />
          <span className="sr-only">Close wizard</span>
        </Button>
      </div>

      {/* Progress Steps */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.number} className="flex items-center flex-1">
              <div className="flex flex-col items-center gap-2 flex-1">
                <div
                  className={cn(
                    "w-10 h-10 rounded-xl flex items-center justify-center font-display font-semibold text-sm transition-all duration-220",
                    index < currentStep
                      ? "bg-primary text-primary-foreground shadow-md"
                      : index === currentStep
                        ? "bg-gradient-to-br from-primary to-accent text-white shadow-lg shadow-primary/30"
                        : "bg-muted text-muted-foreground border border-border",
                  )}
                >
                  {index < currentStep ? <Check className="w-5 h-5" /> : step.number}
                </div>
                <span
                  className={cn(
                    "text-xs font-medium transition-colors duration-220",
                    index <= currentStep ? "text-foreground" : "text-muted-foreground",
                  )}
                >
                  {step.label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div className="w-full h-0.5 bg-muted mx-2 relative overflow-hidden">
                  {index < currentStep && (
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: "100%" }}
                      transition={{ duration: 0.3 }}
                      className="absolute inset-y-0 left-0 bg-primary"
                    />
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Progress Bar */}
        <div className="w-full h-1 bg-muted rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-primary to-accent"
            initial={{ width: "25%" }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
          />
        </div>
      </div>

      {/* Error Message */}
      <AnimatePresence mode="wait">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm"
            role="alert"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Step Content */}
      <div className="min-h-[400px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {currentStep === 0 && <Step1ReportType state={state} setState={setState} setError={setError} />}
            {currentStep === 1 && <Step2Area state={state} setState={setState} setError={setError} />}
            {currentStep === 2 && <Step3Options state={state} setState={setState} setError={setError} />}
            {currentStep === 3 && <Step4Review state={state} />}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between pt-6 border-t border-border">
        <Button
          variant="outline"
          onClick={() => {
            setError(null)
            setCurrentStep(Math.max(0, currentStep - 1))
          }}
          disabled={currentStep === 0}
          className="border-border/50"
        >
          Back
        </Button>
        {currentStep < 3 ? (
          <Button onClick={handleNext} className="gap-2 bg-gradient-to-r from-primary to-accent hover:opacity-90">
            Next
            <ChevronRight className="w-4 h-4" />
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            className="gap-2 bg-gradient-to-r from-primary to-accent hover:opacity-90 min-w-[200px]"
          >
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
  const reportTypes: { label: string; value: ReportType }[] = [
    { label: "Market Snapshot", value: "market_snapshot" },
    { label: "New Listings", value: "new_listings" },
    { label: "Closed Sales", value: "closed" },
    { label: "Inventory", value: "inventory" },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <h3 className="text-lg font-display font-semibold">Report Type</h3>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button className="text-muted-foreground hover:text-primary transition-colors">
                <HelpCircle className="w-4 h-4" />
                <span className="sr-only">Why this?</span>
              </button>
            </TooltipTrigger>
            <TooltipContent className="bg-primary text-primary-foreground border-primary/20">
              <p className="text-xs">Choose the type of market analysis you need</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      <p className="text-sm text-muted-foreground">Pick your insight</p>

      <SegmentedControl
        options={reportTypes}
        value={state.report_type || "market_snapshot"}
        onChange={(value) => {
          setState({ ...state, report_type: value })
          setError(null)
        }}
        className="w-full"
      />
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
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <h3 className="text-lg font-display font-semibold">Area Selection</h3>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button className="text-muted-foreground hover:text-accent transition-colors">
                <HelpCircle className="w-4 h-4" />
                <span className="sr-only">Why this?</span>
              </button>
            </TooltipTrigger>
            <TooltipContent className="bg-accent text-accent-foreground">
              <p className="text-xs">Define the geographic scope of your report</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Area Mode Chips */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setState({ ...state, area_mode: "city" })}
          className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium border transition-all duration-180",
            state.area_mode === "city"
              ? "bg-primary/10 border-primary text-primary"
              : "bg-muted border-border text-muted-foreground hover:border-primary/50",
          )}
        >
          City
        </button>
        <button
          type="button"
          onClick={() => setState({ ...state, area_mode: "zips" })}
          className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium border transition-all duration-180",
            state.area_mode === "zips"
              ? "bg-primary/10 border-primary text-primary"
              : "bg-muted border-border text-muted-foreground hover:border-primary/50",
          )}
        >
          ZIP Codes
        </button>
      </div>

      {/* City Input */}
      {state.area_mode === "city" && (
        <div className="space-y-2">
          <Label htmlFor="city" className="text-sm font-medium">
            City Name
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
            className="h-11"
          />
          <p className="text-xs text-muted-foreground">Enter the city name for your market area</p>
        </div>
      )}

      {/* ZIP Input */}
      {state.area_mode === "zips" && (
        <div className="space-y-2">
          <Label htmlFor="zips" className="text-sm font-medium">
            ZIP Codes
          </Label>
          <TagInput
            tags={state.zips}
            onTagsChange={(zips) => {
              setState({ ...state, zips })
              setError(null)
            }}
            placeholder="Type ZIP and press Enter..."
            validate={(zip) => /^\d{5}$/.test(zip)}
          />
          <p className="text-xs text-muted-foreground">Max 10 ZIPs</p>
        </div>
      )}
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
  const lookbackOptions = [7, 14, 30, 60, 90]
  const propertyTypes = ["RES", "CND", "MUL", "LND", "COM"]

  const togglePropertyType = (type: string) => {
    const types = state.property_types.includes(type)
      ? state.property_types.filter((t) => t !== type)
      : [...state.property_types, type]
    setState({ ...state, property_types: types })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <h3 className="text-lg font-display font-semibold">Report Options</h3>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button className="text-muted-foreground hover:text-accent transition-colors">
                <HelpCircle className="w-4 h-4" />
                <span className="sr-only">Why this?</span>
              </button>
            </TooltipTrigger>
            <TooltipContent className="bg-accent text-accent-foreground">
              <p className="text-xs">Refine your data parameters and filters</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Lookback Period */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Lookback Period (days)</Label>
        <div className="flex gap-2">
          {lookbackOptions.map((days) => (
            <button
              key={days}
              type="button"
              onClick={() => {
                setState({ ...state, lookback_days: days })
                setError(null)
              }}
              className={cn(
                "flex-1 px-4 py-2.5 rounded-lg text-sm font-medium border transition-all duration-180",
                state.lookback_days === days
                  ? "bg-primary/10 border-primary text-primary"
                  : "bg-muted border-border text-muted-foreground hover:border-primary/50",
              )}
            >
              {days}
            </button>
          ))}
        </div>
      </div>

      {/* Property Type */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Property Type (optional)</Label>
        <div className="flex gap-2">
          {propertyTypes.map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => togglePropertyType(type)}
              className={cn(
                "flex-1 px-4 py-2.5 rounded-lg text-sm font-medium border transition-all duration-180",
                state.property_types.includes(type)
                  ? "bg-accent/10 border-accent text-accent"
                  : "bg-muted border-border text-muted-foreground hover:border-accent/50",
              )}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Price Range */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Price Range (optional)</Label>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="minprice" className="text-xs text-muted-foreground">
              Min
            </Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">$</span>
              <Input
                id="minprice"
                type="number"
                placeholder="0"
                value={state.minprice}
                onChange={(e) => setState({ ...state, minprice: e.target.value })}
                className="pl-7 h-11"
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="maxprice" className="text-xs text-muted-foreground">
              Max
            </Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">$</span>
              <Input
                id="maxprice"
                type="number"
                placeholder="No limit"
                value={state.maxprice}
                onChange={(e) => setState({ ...state, maxprice: e.target.value })}
                className="pl-7 h-11"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Step 4: Review
function Step4Review({ state }: { state: WizardState }) {
  const payload = buildPayload(state)

  const reportTypeLabels: Record<ReportType, string> = {
    market_snapshot: "Market Snapshot",
    new_listings: "New Listings",
    closed: "Closed Sales",
    inventory: "Inventory",
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-display font-semibold">Review & Generate</h3>
        <p className="text-sm text-muted-foreground mt-1">Verify your configuration before generating</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Summary Panel */}
        <div className="space-y-4 p-6 rounded-xl bg-muted/30 border border-border/50">
          <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Summary</h4>

          <div className="space-y-3">
            <div>
              <p className="text-xs text-muted-foreground">Report Type</p>
              <p className="text-sm font-medium font-display">{reportTypeLabels[state.report_type!]}</p>
            </div>

            <div>
              <p className="text-xs text-muted-foreground">Area</p>
              {state.area_mode === "city" ? (
                <p className="text-sm font-medium font-display">{state.city}</p>
              ) : (
                <p className="text-sm font-medium font-display">{state.zips.length} ZIP codes</p>
              )}
            </div>

            <div>
              <p className="text-xs text-muted-foreground">Lookback</p>
              <p className="text-sm font-medium font-display">{state.lookback_days} days</p>
            </div>

            {state.property_types.length > 0 && (
              <div>
                <p className="text-xs text-muted-foreground">Property Types</p>
                <p className="text-sm font-medium font-display">{state.property_types.join(", ")}</p>
              </div>
            )}

            {(state.minprice || state.maxprice) && (
              <div>
                <p className="text-xs text-muted-foreground">Price Range</p>
                <p className="text-sm font-medium font-display">
                  ${state.minprice || "0"} - ${state.maxprice || "∞"}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* API Payload */}
        <div className="space-y-3 p-6 rounded-xl bg-muted/30 border border-border/50">
          <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">API Payload</h4>
          <pre className="text-xs bg-background/80 p-4 rounded-lg border border-border/50 overflow-x-auto font-mono">
            <code className="text-primary">{JSON.stringify(payload, null, 2)}</code>
          </pre>
        </div>
      </div>
    </div>
  )
}
