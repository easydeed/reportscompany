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
  AudienceFilter
} from "./types"
import { getAreaDisplay, getEmailSubject } from "./types"
import { editState, schedulePatch, schedulePayload, type StoredSchedule } from "./edit-state"
import { useInvalidate } from "@/hooks/use-api"
import { VerificationRequiredBanner } from "@/components/shared/verification-required"
import { readVerificationRefusal, type VerificationRefusal } from "@/lib/verification"

const DEFAULT_STATE: ScheduleBuilderState = {
  name: "",
  active: true,
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
  primaryColor: "#4F46E5",
  accentColor: "#818CF8",
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
  schedule?: StoredSchedule
}

export function ScheduleBuilder({ schedule }: ScheduleBuilderProps) {
  const router = useRouter()
  const invalidate = useInvalidate()
  const [initial] = useState(() => schedule ? editState(schedule) : DEFAULT_STATE)
  const [state, setState] = useState(initial)
  const [branding, setBranding] = useState<BrandingContext>(DEFAULT_BRANDING)
  const [profile, setProfile] = useState<ProfileContext>(DEFAULT_PROFILE)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [verificationRefusal, setVerificationRefusal] = useState<VerificationRefusal | null>(null)
  const [scrolled, setScrolled] = useState(false)
  
  // Track which sections user has interacted with
  const [touched, setTouched] = useState({
    name: !!schedule,
    reportType: !!schedule,
    area: !!schedule,
    lookback: !!schedule,
    cadence: !!schedule,
    recipients: !!schedule,
  })

  const isEditMode = !!schedule

  // Scroll shadow detection
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    window.addEventListener("scroll", onScroll)
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  // Load the optional email preview independently of the schedule being edited.
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
            accentColor: data.accent_color || data.secondary_color || DEFAULT_BRANDING.accentColor,
            emailLogoUrl: data.email_logo_url || data.logo_url || null,
            displayName: data.display_name || data.name || null,
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

      } catch (error) {
        console.error("Failed to load data:", error)
      }
    }
    loadData()
  }, [])

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
  const patch = schedule ? schedulePatch(initial, state) : null
  const canSave = (!patch || Object.keys(patch).length > 0) && !!state.name.trim() &&
    !!state.reportType && 
    (state.areaType === "city" ? !!state.city : state.zipCodes.length > 0) && 
    !!state.cadence && !!state.timezone && 
    (state.recipients.length > 0 || (isEditMode && !state.active && !initial.recipients.length))

  // Progress counter for header
  const completedCount = [isNameComplete, isReportTypeComplete, isAreaComplete, isLookbackComplete, isCadenceComplete, hasRecipients].filter(Boolean).length
  const totalSections = 6

  // Handle save
  const handleSave = async () => {
    if (!canSave || isSaving) return
    setIsSaving(true)
    setSaveError(null)
    setVerificationRefusal(null)

    try {
      const url = schedule
        ? `/api/proxy/v1/schedules/${encodeURIComponent(schedule.id)}`
        : "/api/proxy/v1/schedules"
      
      const res = await fetch(url, {
        method: isEditMode ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch ?? schedulePayload(state)),
      })

      if (!res.ok) {
        // D-019. The refusal has to reach the person who triggered it.
        const body = await res.json().catch(() => ({}))
        const refusal = readVerificationRefusal(body)
        if (refusal) {
          setVerificationRefusal(refusal)
          return
        }
        // AND EVERY OTHER FAILURE TOO. This branch used to `throw` into a catch
        // whose entire body was `console.error`, so a rejected save left the
        // button springing back to "Create Schedule" and NOTHING else — the
        // user's only evidence that it had not worked was the page not
        // navigating. A 403 handled correctly on top of that would still have
        // been invisible for any other status. See D-082 for the same shape
        // elsewhere in this app.
        throw new Error(
          (typeof body?.detail === "string" && body.detail) ||
          body?.message ||
          "Failed to save schedule"
        )
      }

      await invalidate.schedules()
      router.push("/app/schedules")
      router.refresh()
    } catch (error) {
      console.error("Save error:", error)
      setSaveError(error instanceof Error ? error.message : "Failed to save schedule")
    } finally {
      setIsSaving(false)
    }
  }

  const areaDisplay = getAreaDisplay(state)
  const emailSubject = getEmailSubject(state)

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
        {verificationRefusal && (
          <div className="mb-6">
            <VerificationRequiredBanner refusal={verificationRefusal} />
          </div>
        )}
        {saveError && !verificationRefusal && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {saveError}
          </div>
        )}
        <div className="grid gap-8 lg:grid-cols-[400px_1fr]">
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
                  <label htmlFor="schedule-name" className="text-sm font-medium text-gray-900">Schedule Name</label>
                </div>
                <div className="px-5 pb-5">
                  <input
                    id="schedule-name"
                    maxLength={255}
                    type="text"
                    value={state.name}
                    onChange={(e) => updateState({ name: e.target.value })}
                    placeholder="e.g., Weekly Market Update"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                  {schedule && (
                    <label className="mt-3 flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={state.active}
                        onChange={(e) => updateState({ active: e.target.checked })} />
                      Active schedule
                    </label>
                  )}
                </div>
              </section>

              {/* Report Type Section */}
              <ReportTypeSection
                locked={isEditMode}
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
                onChange={(recipients) => updateState({ recipients })}
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
