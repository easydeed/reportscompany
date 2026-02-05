"use client"

import { useState, useEffect } from "react"
import { ArrowLeft, Loader2, Sparkles, Check } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ReportTypeSection } from "./sections/report-type-section"
import { AreaSection } from "./sections/area-section"
import { LookbackSection } from "./sections/lookback-section"
import { CadenceSection } from "./sections/cadence-section"
import { RecipientsSection } from "./sections/recipients-section"
import { EmailPreview } from "./email-preview"
import type { 
  ScheduleBuilderState, 
  BrandingContext, 
  ProfileContext,
  AudienceFilter,
  Recipient 
} from "./types"
import { AUDIENCE_FILTER_PRESETS, getAreaDisplay, getEmailSubject } from "./types"

const DEFAULT_STATE: ScheduleBuilderState = {
  name: "",
  reportType: null,
  lookbackDays: null,
  areaType: "city",
  city: null,
  zipCodes: [],
  audienceFilter: null,
  audienceFilterName: null,
  cadence: "weekly",
  weeklyDow: 1, // Monday
  monthlyDom: 1,
  sendHour: 9,
  sendMinute: 0,
  timezone: "America/Los_Angeles",
  recipients: [],
  includeAttachment: true,
}

const DEFAULT_BRANDING: BrandingContext = {
  primaryColor: "#7C3AED",
  accentColor: "#8B5CF6",
  emailLogoUrl: null,
  displayName: "TrendyReports",
}

const DEFAULT_PROFILE: ProfileContext = {
  name: "Agent Name",
  jobTitle: "Real Estate Agent",
  avatarUrl: null,
  phone: "(555) 123-4567",
  email: "agent@example.com",
}

interface ScheduleBuilderProps {
  scheduleId?: string
}

export function ScheduleBuilder({ scheduleId }: ScheduleBuilderProps) {
  const router = useRouter()
  const [state, setState] = useState<ScheduleBuilderState>(DEFAULT_STATE)
  const [branding, setBranding] = useState<BrandingContext>(DEFAULT_BRANDING)
  const [profile, setProfile] = useState<ProfileContext>(DEFAULT_PROFILE)
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(!!scheduleId)
  const [scrolled, setScrolled] = useState(false)
  
  // Track which sections user has interacted with
  const [touched, setTouched] = useState({
    name: false,
    reportType: false,
    area: false,
    lookback: false,
    cadence: false,
    recipients: false,
  })

  const isEditMode = !!scheduleId

  // Scroll shadow detection
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    window.addEventListener("scroll", onScroll)
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  // Fetch branding, profile, and existing schedule (if editing)
  useEffect(() => {
    async function loadData() {
      try {
        const [brandingRes, profileRes] = await Promise.all([
          fetch("/api/proxy/v1/account/branding"),
          fetch("/api/proxy/v1/users/me"),
        ])

        if (brandingRes.ok) {
          const data = await brandingRes.json()
          setBranding({
            primaryColor: data.primary_color || DEFAULT_BRANDING.primaryColor,
            accentColor: data.accent_color || DEFAULT_BRANDING.accentColor,
            emailLogoUrl: data.email_logo_url || null,
            displayName: data.display_name || null,
          })
        }

        if (profileRes.ok) {
          const data = await profileRes.json()
          setProfile({
            name: [data.first_name, data.last_name].filter(Boolean).join(" ") || DEFAULT_PROFILE.name,
            jobTitle: data.job_title || null,
            avatarUrl: data.avatar_url || null,
            phone: data.phone || null,
            email: data.email || DEFAULT_PROFILE.email,
          })
        }

        // Load existing schedule if editing
        if (scheduleId) {
          const scheduleRes = await fetch(`/api/proxy/v1/schedules/${scheduleId}`)
          if (scheduleRes.ok) {
            const schedule = await scheduleRes.json()
            setState(mapApiToState(schedule))
            // Mark all sections as touched when editing existing schedule
            setTouched({
              name: true,
              reportType: true,
              area: true,
              lookback: true,
              cadence: true,
              recipients: true,
            })
          }
        }
      } catch (error) {
        console.error("Failed to load data:", error)
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [scheduleId])

  const updateState = (updates: Partial<ScheduleBuilderState>) => {
    setState((prev) => ({ ...prev, ...updates }))
    
    // Mark sections as touched based on what was updated
    if ('name' in updates) {
      setTouched(prev => ({ ...prev, name: true }))
    }
    if ('reportType' in updates || 'audienceFilter' in updates) {
      setTouched(prev => ({ ...prev, reportType: true }))
    }
    if ('city' in updates || 'zipCodes' in updates || 'areaType' in updates) {
      setTouched(prev => ({ ...prev, area: true }))
    }
    if ('lookbackDays' in updates) {
      setTouched(prev => ({ ...prev, lookback: true }))
    }
    if ('cadence' in updates || 'weeklyDow' in updates || 'monthlyDom' in updates ||
        'sendHour' in updates || 'sendMinute' in updates || 'timezone' in updates) {
      setTouched(prev => ({ ...prev, cadence: true }))
    }
    if ('recipients' in updates) {
      setTouched(prev => ({ ...prev, recipients: true }))
    }
  }

  // Handle audience filter change
  const handleAudienceChange = (filter: AudienceFilter, name: string | null) => {
    updateState({ audienceFilter: filter, audienceFilterName: name })
  }

  // Check section completion - only show complete if touched AND filled
  const isNameComplete = touched.name && !!state.name.trim()
  const isReportTypeComplete = touched.reportType && !!state.reportType
  const isAreaComplete = touched.area && (state.areaType === "city" ? !!state.city : state.zipCodes.length > 0)
  const isLookbackComplete = touched.lookback && !!state.lookbackDays
  const isCadenceComplete = touched.cadence && !!state.cadence && !!state.timezone
  const hasRecipients = touched.recipients && state.recipients.length > 0

  // Can save only requires actual data, not touched state
  const canSave = !!state.name.trim() && 
    !!state.reportType && 
    (state.areaType === "city" ? !!state.city : state.zipCodes.length > 0) && 
    !!state.cadence && !!state.timezone && 
    state.recipients.length > 0

  // Progress counter for header
  const completedCount = [isNameComplete, isReportTypeComplete, isAreaComplete, isLookbackComplete, isCadenceComplete, hasRecipients].filter(Boolean).length
  const totalSections = 6

  // Handle save
  const handleSave = async () => {
    if (!canSave) return
    setIsSaving(true)

    try {
      const filters = state.audienceFilter && state.audienceFilter !== "all" 
        ? AUDIENCE_FILTER_PRESETS[state.audienceFilter] 
        : null

      const payload = {
        name: state.name,
        report_type: state.reportType,
        city: state.areaType === "city" ? state.city : null,
        zip_codes: state.areaType === "zip" ? state.zipCodes : null,
        lookback_days: state.lookbackDays,
        cadence: state.cadence,
        weekly_dow: state.cadence === "weekly" ? state.weeklyDow : null,
        monthly_dom: state.cadence === "monthly" ? state.monthlyDom : null,
        send_hour: state.sendHour,
        send_minute: state.sendMinute,
        timezone: state.timezone,
        recipients: state.recipients.map(r => ({
          type: r.type,
          id: r.type === "contact" || r.type === "group" ? r.id : undefined,
          email: r.type === "manual_email" ? r.email : undefined,
        })),
        include_attachment: state.includeAttachment,
        active: true,
        filters,
      }

      const url = isEditMode 
        ? `/api/proxy/v1/schedules/${scheduleId}`
        : "/api/proxy/v1/schedules"
      
      const res = await fetch(url, {
        method: isEditMode ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (!res.ok) throw new Error("Failed to save schedule")
      
      router.push("/app/schedules")
    } catch (error) {
      console.error("Save error:", error)
    } finally {
      setIsSaving(false)
    }
  }

  const areaDisplay = getAreaDisplay(state)
  const emailSubject = getEmailSubject(state)

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header - with scroll shadow and backdrop blur */}
      <header className={cn(
        "sticky top-0 z-10 bg-white/95 backdrop-blur-sm border-b px-8 py-3 transition-shadow duration-200",
        scrolled ? "shadow-sm border-gray-200" : "border-transparent"
      )}>
        <div className="flex items-center justify-between">
          {/* Left: Back + Title */}
          <div className="flex items-center gap-4">
            <Link
              href="/app/schedules"
              className="flex items-center justify-center w-8 h-8 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-sm font-semibold text-gray-900">
                {isEditMode ? "Edit Schedule" : "New Schedule"}
              </h1>
              <p className="text-xs text-gray-500">
                {completedCount} of {totalSections} sections complete
              </p>
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/app/schedules">Cancel</Link>
            </Button>
            <Button
              onClick={handleSave}
              disabled={!canSave || isSaving}
              size="sm"
              className={cn(
                "transition-all duration-300",
                canSave && !isSaving && [
                  "shadow-md shadow-primary/20",
                  "hover:shadow-lg hover:shadow-primary/30",
                  "hover:-translate-y-0.5",
                ]
              )}
            >
              {isSaving ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Saving...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5" />
                  {isEditMode ? "Update Schedule" : "Create Schedule"}
                </span>
              )}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content - 400px config / flexible preview */}
      <main className="px-8 py-6">
        <div className="grid grid-cols-[400px_1fr] gap-8">
          {/* Left: Config Panel (fixed 400px) */}
          <div className="relative">
            {/* Vertical progress line */}
            <div className="absolute left-[19px] top-8 bottom-8 w-px bg-gray-200" />
            <div
              className="absolute left-[19px] top-8 w-px bg-primary transition-all duration-500"
              style={{ height: `${(completedCount / totalSections) * 100}%` }}
            />

            <div className="space-y-3 relative">
              {/* Schedule Name Section */}
              <section className={cn(
                "bg-white rounded-xl border transition-all duration-200",
                isNameComplete ? "border-gray-200 shadow-sm" : "border-gray-200/80 shadow-sm"
              )}>
                <div className="flex items-center gap-3 px-5 py-4">
                  <div className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors",
                    isNameComplete
                      ? "bg-emerald-500 text-white"
                      : "bg-gray-100 text-gray-500"
                  )}>
                    {isNameComplete ? <Check className="w-3.5 h-3.5" /> : 1}
                  </div>
                  <h3 className="text-sm font-medium text-gray-900">Schedule Name</h3>
                </div>
                <div className="px-5 pb-5">
                  <input
                    type="text"
                    value={state.name}
                    onChange={(e) => updateState({ name: e.target.value })}
                    placeholder="e.g., Weekly Market Update"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                </div>
              </section>

              {/* Report Type Section */}
              <ReportTypeSection
                reportType={state.reportType}
                audienceFilter={state.audienceFilter}
                audienceFilterName={state.audienceFilterName}
                onChange={updateState}
                onAudienceChange={handleAudienceChange}
                isComplete={isReportTypeComplete}
                stepNumber={2}
              />

              {/* Area Section */}
              <AreaSection
                areaType={state.areaType}
                city={state.city}
                zipCodes={state.zipCodes}
                onChange={updateState}
                isComplete={isAreaComplete}
                stepNumber={3}
              />

              {/* Lookback Section */}
              <LookbackSection
                lookbackDays={state.lookbackDays}
                onChange={updateState}
                isComplete={isLookbackComplete}
                stepNumber={4}
              />

              {/* Cadence Section */}
              <CadenceSection
                cadence={state.cadence}
                weeklyDow={state.weeklyDow}
                monthlyDom={state.monthlyDom}
                sendHour={state.sendHour}
                sendMinute={state.sendMinute}
                timezone={state.timezone}
                onChange={updateState}
                isComplete={isCadenceComplete}
                stepNumber={5}
              />

              {/* Recipients Section */}
              <RecipientsSection
                recipients={state.recipients}
                onChange={updateState}
                hasRecipients={hasRecipients}
                stepNumber={6}
              />
            </div>
          </div>

          {/* Right: Preview Panel (flexible, takes remaining space) */}
          <div className="sticky top-20">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              {/* Preview header — distinct treatment */}
              <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100 bg-gray-50/50">
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Email Preview
                  </h3>
                </div>
                <span className="text-xs text-gray-400">Updates as you build</span>
              </div>

              {/* Preview content */}
              <div className="p-4">
                <p className="text-xs text-gray-500 mb-4">
                  Subject: {emailSubject}
                </p>
                <EmailPreview 
                  state={state} 
                  branding={branding} 
                  profile={profile}
                  area={areaDisplay}
                />
                <div className="mt-4 text-center text-xs text-gray-500">
                  {state.cadence === "weekly" 
                    ? `Every ${["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][state.weeklyDow]} at ${state.sendHour}:${state.sendMinute.toString().padStart(2, "0")}`
                    : `Monthly on day ${state.monthlyDom} at ${state.sendHour}:${state.sendMinute.toString().padStart(2, "0")}`
                  }
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

// Helper to map API response to state
function mapApiToState(schedule: any): ScheduleBuilderState {
  return {
    name: schedule.name || "",
    reportType: schedule.report_type || "market_snapshot",
    lookbackDays: schedule.lookback_days || 30,
    areaType: schedule.city ? "city" : "zip",
    city: schedule.city || null,
    zipCodes: schedule.zip_codes || [],
    audienceFilter: mapFiltersToAudience(schedule.filters),
    audienceFilterName: schedule.filters?.preset_display_name || null,
    cadence: schedule.cadence || "weekly",
    weeklyDow: schedule.weekly_dow ?? 1,
    monthlyDom: schedule.monthly_dom ?? 1,
    sendHour: schedule.send_hour ?? 9,
    sendMinute: schedule.send_minute ?? 0,
    timezone: schedule.timezone || "America/Los_Angeles",
    recipients: (schedule.recipients || []).map((r: any) => ({
      type: r.type,
      id: r.id,
      name: r.name || r.email,
      email: r.email,
      memberCount: r.member_count,
    })),
    includeAttachment: schedule.include_attachment ?? true,
  }
}

function mapFiltersToAudience(filters: any): AudienceFilter {
  if (!filters) return null
  if (filters.preset_display_name === "First-Time Buyer") return "first_time"
  if (filters.preset_display_name === "Luxury") return "luxury"
  if (filters.preset_display_name === "Family Homes") return "families"
  if (filters.preset_display_name === "Condo Watch") return "condo"
  if (filters.preset_display_name === "Investor Deals") return "investors"
  return "all"
}
