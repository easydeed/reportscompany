"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Stepper } from "@/components/stepper"
import {
  FileText,
  TrendingUp,
  Home,
  DollarSign,
  BarChart3,
  Calendar,
  MapPin,
  Hash,
  X,
  ArrowRight,
  ArrowLeft,
  Clock,
  Mail,
} from "lucide-react"
import { type ScheduleWizardState, type ReportType, type Weekday, weekdayLabels } from "./types"

const steps = [
  { title: "Basics", description: "Name and report type" },
  { title: "Area", description: "Select location" },
  { title: "Cadence", description: "Schedule frequency" },
  { title: "Recipients", description: "Email addresses" },
  { title: "Review", description: "Confirm details" },
]

const reportTypes = [
  { id: "market_snapshot" as ReportType, name: "Market Snapshot", icon: TrendingUp },
  { id: "new_listings" as ReportType, name: "New Listings", icon: Home },
  { id: "inventory" as ReportType, name: "Inventory Report", icon: BarChart3 },
  { id: "closed" as ReportType, name: "Closed Sales", icon: DollarSign },
  { id: "price_bands" as ReportType, name: "Price Bands", icon: BarChart3 },
  { id: "open_houses" as ReportType, name: "Open Houses", icon: Calendar },
]

const lookbackOptions = [7, 14, 30, 60, 90]

const weekdays: Weekday[] = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

const monthlyDays = Array.from({ length: 28 }, (_, i) => i + 1)

export interface ScheduleWizardProps {
  onSubmit: (data: ScheduleWizardState) => void
  onCancel: () => void
}

function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

function validateEmailDomain(email: string): boolean {
  const domain = email.split("@")[1]
  // Basic domain validation - ensure it has at least one dot
  return domain && domain.includes(".")
}

// Step 1: Basics
function StepBasics({ state, setState }: { state: ScheduleWizardState; setState: (s: ScheduleWizardState) => void }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Schedule Basics</h2>
        <p className="text-sm text-muted-foreground">Give your schedule a name and choose the report type</p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-6">
          <div className="space-y-2">
            <Label htmlFor="schedule-name">
              Schedule Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="schedule-name"
              type="text"
              placeholder="e.g., Weekly Market Update"
              value={state.name}
              onChange={(e) => setState({ ...state, name: e.target.value })}
              aria-required="true"
            />
            <p className="text-xs text-muted-foreground">Choose a descriptive name for this schedule</p>
          </div>

          <div className="space-y-3">
            <Label>
              Report Type <span className="text-destructive">*</span>
            </Label>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {reportTypes.map((type) => {
                const Icon = type.icon
                return (
                  <button
                    key={type.id}
                    type="button"
                    onClick={() => setState({ ...state, report_type: type.id })}
                    className={`flex items-center gap-3 p-4 rounded-lg border-2 transition-all text-left ${
                      state.report_type === type.id
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    }`}
                    aria-pressed={state.report_type === type.id}
                  >
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                        state.report_type === type.id
                          ? "bg-primary text-primary-foreground"
                          : "bg-primary/10 text-primary"
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="font-medium text-sm">{type.name}</span>
                  </button>
                )
              })}
            </div>
          </div>

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
            <p className="text-xs text-muted-foreground">How far back to include data in each report</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Step 2: Area
function StepArea({ state, setState }: { state: ScheduleWizardState; setState: (s: ScheduleWizardState) => void }) {
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
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Select Area</h2>
        <p className="text-sm text-muted-foreground">Define the geographic area for your scheduled reports</p>
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
                onChange={(e) => setState({ ...state, city: e.target.value })}
                aria-required="true"
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
                />
                <Button type="button" onClick={addZip} disabled={!zipInput || zipInput.length !== 5}>
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

// Step 3: Cadence
function StepCadence({ state, setState }: { state: ScheduleWizardState; setState: (s: ScheduleWizardState) => void }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Schedule Cadence</h2>
        <p className="text-sm text-muted-foreground">Set how often this report should be generated</p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-6">
          <div className="space-y-3">
            <Label>
              Frequency <span className="text-destructive">*</span>
            </Label>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setState({ ...state, cadence: "weekly" })}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border-2 transition-all ${
                  state.cadence === "weekly"
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-border hover:border-primary/50"
                }`}
                aria-pressed={state.cadence === "weekly"}
              >
                <Calendar className="w-4 h-4" />
                <span className="font-medium">Weekly</span>
              </button>
              <button
                type="button"
                onClick={() => setState({ ...state, cadence: "monthly" })}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border-2 transition-all ${
                  state.cadence === "monthly"
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-border hover:border-primary/50"
                }`}
                aria-pressed={state.cadence === "monthly"}
              >
                <Calendar className="w-4 h-4" />
                <span className="font-medium">Monthly</span>
              </button>
            </div>
          </div>

          {state.cadence === "weekly" && (
            <div className="space-y-3">
              <Label>
                Day of Week <span className="text-destructive">*</span>
              </Label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {weekdays.map((day) => (
                  <button
                    key={day}
                    type="button"
                    onClick={() => setState({ ...state, weekday: day })}
                    className={`px-4 py-2.5 rounded-lg border-2 font-medium transition-all ${
                      state.weekday === day
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-border hover:border-primary/50"
                    }`}
                    aria-pressed={state.weekday === day}
                  >
                    {weekdayLabels[day]}
                  </button>
                ))}
              </div>
            </div>
          )}

          {state.cadence === "monthly" && (
            <div className="space-y-3">
              <Label>
                Day of Month <span className="text-destructive">*</span>
              </Label>
              <div className="grid grid-cols-7 gap-2">
                {monthlyDays.map((day) => (
                  <button
                    key={day}
                    type="button"
                    onClick={() => setState({ ...state, monthly_day: day })}
                    className={`aspect-square rounded-lg border-2 font-medium transition-all ${
                      state.monthly_day === day
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-border hover:border-primary/50"
                    }`}
                    aria-pressed={state.monthly_day === day}
                  >
                    {day}
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">Days 1-28 are available to ensure reliable scheduling</p>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="schedule-time">
              Time <span className="text-destructive">*</span>
            </Label>
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-muted-foreground" />
              <Input
                id="schedule-time"
                type="time"
                value={state.time}
                onChange={(e) => setState({ ...state, time: e.target.value })}
                className="max-w-[200px]"
                aria-required="true"
              />
            </div>
            <p className="text-xs text-muted-foreground">Time zone: UTC (will be converted to your local time)</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Step 4: Recipients
function StepRecipients({
  state,
  setState,
}: {
  state: ScheduleWizardState
  setState: (s: ScheduleWizardState) => void
}) {
  const [emailInput, setEmailInput] = useState("")
  const [emailError, setEmailError] = useState("")

  const addEmail = () => {
    const email = emailInput.trim().toLowerCase()
    setEmailError("")

    if (!email) return

    if (!validateEmail(email)) {
      setEmailError("Please enter a valid email address")
      return
    }

    if (!validateEmailDomain(email)) {
      setEmailError("Invalid email domain")
      return
    }

    if (state.recipients.includes(email)) {
      setEmailError("This email is already added")
      return
    }

    setState({ ...state, recipients: [...state.recipients, email] })
    setEmailInput("")
  }

  const removeEmail = (email: string) => {
    setState({ ...state, recipients: state.recipients.filter((e) => e !== email) })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Email Recipients</h2>
        <p className="text-sm text-muted-foreground">Add email addresses to receive the scheduled reports</p>
      </div>

      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardContent className="pt-6 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email-input">
              Email Address <span className="text-destructive">*</span>
            </Label>
            <div className="flex gap-2">
              <div className="flex-1">
                <Input
                  id="email-input"
                  type="email"
                  placeholder="agent@example.com"
                  value={emailInput}
                  onChange={(e) => {
                    setEmailInput(e.target.value)
                    setEmailError("")
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault()
                      addEmail()
                    }
                  }}
                  className="bg-background/50"
                  aria-invalid={!!emailError}
                  aria-describedby={emailError ? "email-error" : undefined}
                />
                {emailError && (
                  <p id="email-error" className="text-xs text-destructive mt-1 flex items-center gap-1">
                    {emailError}
                  </p>
                )}
              </div>
              <Button type="button" onClick={addEmail} className="bg-primary/90 hover:bg-primary">
                Add
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">Press Enter or click Add to include an email</p>
          </div>

          {state.recipients.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm flex items-center gap-2">
                <Mail className="w-4 h-4 text-cyan-500" />
                Recipients ({state.recipients.length})
              </Label>
              <div className="space-y-2 max-h-[300px] overflow-y-auto p-3 rounded-lg bg-muted/30 border border-border/50">
                {state.recipients.map((email) => (
                  <div
                    key={email}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-background/80 border border-border/50 hover:border-primary/50 transition-colors duration-150"
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
                      <span className="text-sm font-mono">{email}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeEmail(email)}
                      className="p-1 hover:bg-destructive/10 rounded-sm transition-colors text-muted-foreground hover:text-destructive"
                      aria-label={`Remove ${email}`}
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// Step 5: Review
function StepReview({ state }: { state: ScheduleWizardState }) {
  const selectedType = reportTypes.find((t) => t.id === state.report_type)

  const formatArea = () => {
    if (state.area_mode === "city") return state.city
    return `${state.zips.length} ZIP code${state.zips.length !== 1 ? "s" : ""}`
  }

  const formatCadence = () => {
    if (state.cadence === "weekly") {
      return `Weekly on ${weekdayLabels[state.weekday]}`
    }
    return `Monthly on day ${state.monthly_day}`
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Review Schedule</h2>
        <p className="text-sm text-muted-foreground">Verify all details before creating your schedule</p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Schedule Name</p>
              <p className="font-medium">{state.name}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Report Type</p>
              <p className="font-medium">{selectedType?.name}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Area</p>
              <p className="font-medium">{formatArea()}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Lookback Period</p>
              <p className="font-medium">{state.lookback_days} days</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Cadence</p>
              <p className="font-medium">{formatCadence()}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Time</p>
              <p className="font-medium">{state.time}</p>
            </div>
          </div>

          <div>
            <p className="text-xs text-muted-foreground mb-2">Recipients ({state.recipients.length})</p>
            <div className="flex flex-wrap gap-2">
              {state.recipients.map((email) => (
                <Badge key={email} variant="secondary">
                  {email}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export function ScheduleWizard({ onSubmit, onCancel }: ScheduleWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [state, setState] = useState<ScheduleWizardState>({
    name: "",
    report_type: null,
    lookback_days: 30,
    area_mode: "city",
    city: "",
    zips: [],
    cadence: "weekly",
    weekday: "monday",
    monthly_day: 1,
    time: "09:00",
    recipients: [],
  })

  const validateCurrentStep = (): boolean => {
    setError(null)

    switch (currentStep) {
      case 0:
        if (!state.name.trim()) {
          setError("Please enter a schedule name")
          return false
        }
        if (!state.report_type) {
          setError("Please select a report type")
          return false
        }
        return true
      case 1:
        if (state.area_mode === "city" && !state.city.trim()) {
          setError("Please enter a city name")
          return false
        }
        if (state.area_mode === "zips" && state.zips.length === 0) {
          setError("Please add at least one ZIP code")
          return false
        }
        return true
      case 2:
        if (!state.time) {
          setError("Please select a time")
          return false
        }
        return true
      case 3:
        if (state.recipients.length === 0) {
          setError("Please add at least one recipient email")
          return false
        }
        return true
      default:
        return true
    }
  }

  const handleNext = () => {
    if (!validateCurrentStep()) return
    setCurrentStep((prev) => Math.min(prev + 1, steps.length - 1))
  }

  const handleBack = () => {
    setError(null)
    setCurrentStep((prev) => Math.max(prev - 1, 0))
  }

  const handleSubmit = () => {
    if (!validateCurrentStep()) return
    onSubmit(state)
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-3xl mb-2">New Schedule</h1>
          <p className="text-muted-foreground">Automate report generation on a recurring schedule</p>
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
        {currentStep === 0 && <StepBasics state={state} setState={setState} />}
        {currentStep === 1 && <StepArea state={state} setState={setState} />}
        {currentStep === 2 && <StepCadence state={state} setState={setState} />}
        {currentStep === 3 && <StepRecipients state={state} setState={setState} />}
        {currentStep === 4 && <StepReview state={state} />}
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
          <Button onClick={handleSubmit} className="gap-2">
            <FileText className="w-4 h-4" />
            Create Schedule
          </Button>
        )}
      </div>
    </div>
  )
}
