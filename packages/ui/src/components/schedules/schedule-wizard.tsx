"use client"

import { useState, useEffect } from "react"
import { Button } from "../ui/button"
import { Card, CardContent } from "../ui/card"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Badge } from "../ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { Checkbox } from "../ui/checkbox"
import { RadioGroup, RadioGroupItem } from "../ui/radio-group"
import { ScrollArea } from "../ui/scroll-area"
import { HorizontalStepper } from "../horizontal-stepper"
import { TagInput } from "../tag-input"
import { TimePicker } from "../time-picker"
import { CadencePicker } from "../cadence-picker"
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
  Image,
  Star,
  Users,
  Sparkles,
  LayoutGrid,
} from "lucide-react"
import { type ScheduleWizardState, type ReportType, type Weekday, type ReportFilters, weekdayLabels, AUDIENCE_OPTIONS } from "./types"
import { cn } from "../../lib/utils"
import { CityAutocomplete } from "../city-autocomplete"

const steps = [
  { id: "basics", label: "Basics" },
  { id: "area", label: "Area" },
  { id: "cadence", label: "Cadence" },
  { id: "recipients", label: "Recipients" },
  { id: "review", label: "Review" },
]

const lookbackOptions = [7, 14, 30, 60, 90]

const weekdays: Weekday[] = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

const monthlyDays = Array.from({ length: 28 }, (_, i) => i + 1)

// Three main report categories
type ReportTab = "new_listings" | "market_update" | "closed_sales"

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
  return !!(domain && domain.includes("."))
}

// Step 1: Simplified Basics (Three Cards + Pill Audience Selector)
function StepBasics({ state, setState }: { state: ScheduleWizardState; setState: (s: ScheduleWizardState) => void }) {
  const [activeTab, setActiveTab] = useState<ReportTab>("new_listings")
  const [selectedAudience, setSelectedAudience] = useState<string>("all")

  // Handle tab selection
  const handleTabSelect = (tab: ReportTab) => {
    setActiveTab(tab)
    if (tab === "new_listings") {
      const audience = AUDIENCE_OPTIONS.find(a => a.key === selectedAudience) || AUDIENCE_OPTIONS[0]
      const suggestedName = selectedAudience !== "all" 
        ? `${audience.name} - Weekly`
        : state.name || "New Listings - Weekly"
      setState({
        ...state,
        name: state.name || suggestedName,
        report_type: "new_listings_gallery",
        filters: audience.filters,
        preset_key: selectedAudience !== "all" ? selectedAudience : undefined
      })
    } else if (tab === "market_update") {
      setState({
        ...state,
        name: state.name || "Market Update - Weekly",
        report_type: "market_snapshot",
        filters: {},
        preset_key: undefined
      })
    } else if (tab === "closed_sales") {
      setState({
        ...state,
        name: state.name || "Closed Sales - Weekly",
        report_type: "closed",
        filters: {},
        preset_key: undefined
      })
    }
  }

  // Handle audience selection
  const handleAudienceChange = (audienceKey: string) => {
    setSelectedAudience(audienceKey)
    const audience = AUDIENCE_OPTIONS.find(a => a.key === audienceKey) || AUDIENCE_OPTIONS[0]
    const suggestedName = audienceKey !== "all" 
      ? `${audience.name} - Weekly`
      : "New Listings - Weekly"
    setState({
      ...state,
      name: state.name || suggestedName,
      report_type: "new_listings_gallery",
      filters: audience.filters,
      preset_key: audienceKey !== "all" ? audienceKey : undefined
    })
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
        <h2 className="font-display font-semibold text-xl mb-1">Schedule Basics</h2>
        <p className="text-sm text-muted-foreground">Name your schedule and choose a report type</p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-6">
          {/* Schedule Name */}
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
              className="h-11"
            />
          </div>

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
                    <svg className="w-3 h-3 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
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
                    <svg className="w-3 h-3 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
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
                    <svg className="w-3 h-3 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
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
              <CityAutocomplete
                value={state.city}
                onChange={(city) => setState({ ...state, city })}
                placeholder="Start typing a city..."
              />
              <p className="text-xs text-muted-foreground">
                Coverage: Southern California (CRMLS)
              </p>
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
                className="h-11 max-w-[200px]"
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
  const [people, setPeople] = useState<any[]>([])
  const [loadingPeople, setLoadingPeople] = useState(true)
  const [groups, setGroups] = useState<any[]>([])
  const [loadingGroups, setLoadingGroups] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  
  // Fetch contacts and groups on mount
  useEffect(() => {
    async function loadData() {
      try {
        const peopleList: any[] = []

        // Fetch contacts
        const contactsRes = await fetch('/api/proxy/v1/contacts', { cache: 'no-store' })
        if (contactsRes.ok) {
          const contactsData = await contactsRes.json()
          peopleList.push(...(contactsData.contacts || []).map((c: any) => ({
            id: c.id,
            name: c.name,
            email: c.email,
            type: c.type === 'client' ? 'Client' : c.type === 'list' ? 'List' : 'Agent',
          })))
        }

        // Fetch groups
        const groupsRes = await fetch('/api/proxy/v1/contact-groups', { cache: 'no-store' })
        if (groupsRes.ok) {
          const groupsData = await groupsRes.json()
          setGroups(groupsData.groups || [])
        }

        setPeople(peopleList.filter(p => p.email)) // Only show people with emails
      } catch (error) {
        console.error('Failed to load contacts:', error)
      } finally {
        setLoadingPeople(false)
        setLoadingGroups(false)
      }
    }
    loadData()
  }, [])

  // Filter people by search query
  const filteredPeople = people.filter(person => 
    searchQuery === "" ||
    person.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    person.email.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Check if a person is selected
  const isPersonSelected = (personId: string) => {
    return (state.typedRecipients || []).some(r => r.type === "contact" && r.id === personId)
  }

  // Toggle person selection
  const togglePerson = (person: any) => {
    const current = state.typedRecipients || []
    const currentRecipients = state.recipients
    
    if (isPersonSelected(person.id)) {
      // Remove
      setState({
        ...state,
        recipients: currentRecipients.filter(e => e !== person.email),
        typedRecipients: current.filter(r => !(r.type === "contact" && r.id === person.id))
      })
    } else {
      // Add
      setState({
        ...state,
        recipients: [...currentRecipients, person.email],
        typedRecipients: [...current, { type: "contact" as const, id: person.id }]
      })
    }
  }

  // Check if a group is selected
  const isGroupSelected = (groupId: string) => {
    return (state.typedRecipients || []).some(r => r.type === "group" && r.id === groupId)
  }

  // Toggle group selection
  const toggleGroup = (group: any) => {
    const current = state.typedRecipients || []
    
    if (isGroupSelected(group.id)) {
      setState({
        ...state,
        typedRecipients: current.filter(r => !(r.type === "group" && r.id === group.id))
      })
    } else {
      setState({
        ...state,
        typedRecipients: [...current, { type: "group" as const, id: group.id }]
      })
    }
  }

  // Get selected counts
  const selectedContactsCount = (state.typedRecipients || []).filter(r => r.type === "contact").length
  const selectedGroupsCount = (state.typedRecipients || []).filter(r => r.type === "group").length
  const totalSelected = selectedContactsCount + selectedGroupsCount

  // Loading state
  const isLoading = loadingPeople || loadingGroups

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Email Recipients</h2>
        <p className="text-sm text-muted-foreground">
          Select contacts or groups to receive this report.
        </p>
      </div>

      {/* Loading State */}
      {isLoading && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-3">
              <div className="h-5 w-32 bg-muted rounded animate-pulse" />
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-3 p-3 border rounded-lg">
                    <div className="w-5 h-5 bg-muted rounded animate-pulse" />
                    <div className="w-8 h-8 bg-muted rounded-full animate-pulse" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 w-32 bg-muted rounded animate-pulse" />
                      <div className="h-3 w-48 bg-muted rounded animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Selection Summary */}
      {!isLoading && totalSelected > 0 && (
        <div className="flex flex-wrap gap-2 p-3 rounded-lg bg-primary/5 border border-primary/20">
          <span className="text-sm font-medium text-primary">
            {totalSelected} recipient{totalSelected !== 1 ? 's' : ''} selected:
          </span>
          {selectedContactsCount > 0 && (
            <Badge variant="secondary" className="bg-primary/10 text-primary">
              {selectedContactsCount} contact{selectedContactsCount !== 1 ? 's' : ''}
            </Badge>
          )}
          {selectedGroupsCount > 0 && (
            <Badge variant="secondary" className="bg-purple-100 text-purple-700">
              {selectedGroupsCount} group{selectedGroupsCount !== 1 ? 's' : ''}
            </Badge>
          )}
        </div>
      )}

      {/* Contacts Section */}
      {!isLoading && people.length > 0 && (
        <Card>
          <CardContent className="pt-6 space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm flex items-center gap-2">
                <Mail className="w-4 h-4 text-primary" />
                Contacts ({selectedContactsCount}/{people.length})
              </Label>
              {people.length > 5 && (
                <Input
                  type="text"
                  placeholder="Search contacts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-8 w-48 text-sm"
                />
              )}
            </div>
            <div className="max-h-[200px] overflow-y-auto border rounded-lg divide-y">
              {filteredPeople.map((person) => {
                const selected = isPersonSelected(person.id)
                return (
                  <label
                    key={person.id}
                    className={cn(
                      "flex items-center gap-3 p-3 cursor-pointer transition-colors",
                      selected ? "bg-primary/5" : "hover:bg-muted/50"
                    )}
                  >
                    <Checkbox
                      checked={selected}
                      onCheckedChange={() => togglePerson(person)}
                      className="shrink-0"
                    />
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <span className="text-xs font-semibold text-primary">
                        {person.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-sm truncate">{person.name}</p>
                      <p className="text-xs text-muted-foreground truncate">
                        {person.email}
                      </p>
                    </div>
                    <Badge variant="outline" className="shrink-0 text-xs">
                      {person.type}
                    </Badge>
                  </label>
                )
              })}
              {filteredPeople.length === 0 && (
                <p className="p-4 text-sm text-muted-foreground text-center">
                  No contacts match your search
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Groups Section */}
      {!isLoading && groups.length > 0 && (
        <Card>
          <CardContent className="pt-6 space-y-3">
            <Label className="text-sm flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-600" />
              Groups ({selectedGroupsCount}/{groups.length})
            </Label>
            <div className="max-h-[160px] overflow-y-auto border rounded-lg divide-y">
              {groups.map((group: any) => {
                const selected = isGroupSelected(group.id)
                return (
                  <label
                    key={group.id}
                    className={cn(
                      "flex items-center gap-3 p-3 cursor-pointer transition-colors",
                      selected ? "bg-purple-50" : "hover:bg-muted/50"
                    )}
                  >
                    <Checkbox
                      checked={selected}
                      onCheckedChange={() => toggleGroup(group)}
                      className="shrink-0"
                    />
                    <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center shrink-0">
                      <Users className="w-4 h-4 text-purple-600" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-sm truncate">{group.name}</p>
                      <p className="text-xs text-muted-foreground truncate">
                        {group.member_count ?? 0} member{(group.member_count ?? 0) !== 1 ? 's' : ''}
                        {group.description && ` • ${group.description}`}
                      </p>
                    </div>
                  </label>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* No recipients hint */}
      {!isLoading && totalSelected === 0 && (
        <p className="text-sm text-muted-foreground text-center py-2">
          Select at least one contact or group to receive this report
        </p>
      )}

      {/* Empty state - no contacts or groups */}
      {!isLoading && people.length === 0 && groups.length === 0 && (
        <Card>
          <CardContent className="pt-6 text-center">
            <Users className="w-12 h-12 text-muted-foreground/50 mx-auto mb-3" />
            <p className="font-medium text-muted-foreground">No contacts or groups found</p>
            <p className="text-sm text-muted-foreground mt-1">
              Add contacts in the Contacts section to send reports
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Step 5: Review - Simplified version
function StepReview({ state }: { state: ScheduleWizardState }) {
  const isNewListings = state.report_type === "new_listings_gallery" || state.report_type === "featured_listings"
  const isMarketUpdate = state.report_type === "market_snapshot"
  const isClosedSales = state.report_type === "closed"
  
  // Get audience name from filters
  const audienceName = state.filters?.preset_display_name || (isNewListings ? "All Listings" : null)

  const formatCadence = () => {
    if (state.cadence === "weekly") {
      return `Every ${weekdayLabels[state.weekday]}`
    }
    return `Monthly on the ${state.monthly_day}${state.monthly_day === 1 ? 'st' : state.monthly_day === 2 ? 'nd' : state.monthly_day === 3 ? 'rd' : 'th'}`
  }

  const recipientCount = (state.typedRecipients || []).length
  const contactCount = (state.typedRecipients || []).filter(r => r.type === "contact").length
  const groupCount = (state.typedRecipients || []).filter(r => r.type === "group").length
  
  const hasFilters = state.filters && Object.keys(state.filters).filter(k => k !== 'preset_display_name').length > 0

  // Get report display name and icon
  const getReportInfo = () => {
    if (isNewListings) return { name: "New Listings", icon: Image }
    if (isMarketUpdate) return { name: "Market Update", icon: TrendingUp }
    if (isClosedSales) return { name: "Closed Sales", icon: DollarSign }
    return { name: "Report", icon: FileText }
  }
  
  const reportInfo = getReportInfo()
  const ReportIcon = reportInfo.icon

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display font-semibold text-xl mb-1">Ready to schedule!</h2>
        <p className="text-sm text-muted-foreground">Review your automated report settings</p>
      </div>

      {/* Main Summary Card */}
      <div className="relative overflow-hidden rounded-2xl border-2 border-primary/20 bg-gradient-to-br from-primary/5 via-background to-background">
        {/* Header with schedule name and report type */}
        <div className="flex items-center gap-4 p-5 border-b border-primary/10">
          <div className="w-14 h-14 rounded-xl bg-primary flex items-center justify-center">
            <ReportIcon className="w-7 h-7 text-primary-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">Schedule</p>
            <h3 className="font-display font-bold text-xl truncate">{state.name}</h3>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm text-muted-foreground">{reportInfo.name}</span>
              {audienceName && audienceName !== "All Listings" && (
                <Badge variant="secondary" className="text-xs bg-primary/10 text-primary">
                  <Users className="w-3 h-3 mr-1" />
                  {audienceName}
                </Badge>
              )}
            </div>
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
                <BarChart3 className="w-4 h-4 text-green-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Data Range</p>
                <p className="font-semibold text-sm">Last {state.lookback_days} days</p>
              </div>
            </div>

            {/* Cadence */}
            <div className="flex items-start gap-3 p-3 rounded-lg bg-background/80 border border-border/50">
              <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0">
                <Calendar className="w-4 h-4 text-purple-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Frequency</p>
                <p className="font-semibold text-sm">{formatCadence()}</p>
              </div>
            </div>

            {/* Time */}
            <div className="flex items-start gap-3 p-3 rounded-lg bg-background/80 border border-border/50">
              <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                <Clock className="w-4 h-4 text-amber-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Send Time</p>
                <p className="font-semibold text-sm">{state.time}</p>
              </div>
            </div>
          </div>

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

          {/* Recipients Summary */}
          <div className="p-3 rounded-lg bg-background/80 border border-border/50">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-pink-100 flex items-center justify-center flex-shrink-0">
                <Mail className="w-4 h-4 text-pink-600" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-muted-foreground">Recipients</p>
                <p className="font-semibold text-sm">
                  {recipientCount} recipient{recipientCount !== 1 ? 's' : ''}
                  {contactCount > 0 && groupCount > 0 && (
                    <span className="font-normal text-muted-foreground"> ({contactCount} contacts, {groupCount} groups)</span>
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer hint */}
        <div className="px-5 py-3 bg-muted/30 border-t border-border/50">
          <p className="text-xs text-muted-foreground text-center">
            Click <strong>Create Schedule</strong> to start automated delivery
          </p>
        </div>
      </div>
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
    filters: {},  // NEW: empty filters by default
    preset_key: undefined,  // NEW: track preset selection
    area_mode: "city",
    city: "",
    zips: [],
    cadence: "weekly",
    weekday: "friday",  // Default to Friday (common choice)
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
        if (!state.typedRecipients || state.typedRecipients.length === 0) {
          setError("Please add at least one recipient")
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

      <HorizontalStepper steps={steps} currentStep={currentStep} />

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
            Create Schedule
          </Button>
        )}
      </div>
    </div>
  )
}
