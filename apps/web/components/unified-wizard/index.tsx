"use client"

import { useState, useEffect, useMemo, useCallback } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Loader2, ChevronLeft, ChevronRight, Sparkles, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { SharedEmailPreview } from "@/components/shared/email-preview"
import { StepStory } from "./step-story"
import { StepAudience } from "./step-audience"
import { StepWhereWhen } from "./step-where-when"
import { StepDeliver } from "./step-deliver"
import {
  type WizardState,
  type DeliveryMode,
  INITIAL_STATE,
  STORY_TO_REPORT_TYPE,
  STORY_DEFAULT_LOOKBACK,
  AUDIENCE_FILTER_PRESETS,
  getPreviewReportType,
  getAudienceLabel,
  getAreaDisplay,
  STORIES,
} from "./types"

interface UnifiedWizardProps {
  defaultMode?: DeliveryMode
  scheduleId?: string
}

const STEP_LABELS = ["Story", "Audience", "Where & When", "Deliver"]

export function UnifiedReportWizard({ defaultMode = "send_now", scheduleId }: UnifiedWizardProps) {
  const router = useRouter()
  const [state, setState] = useState<WizardState>({ ...INITIAL_STATE, deliveryMode: defaultMode })
  const [step, setStep] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [branding, setBranding] = useState({
    primaryColor: "#4F46E5",
    accentColor: "#818CF8",
    headerLogoUrl: null as string | null,
    displayName: null as string | null,
  })
  const [profile, setProfile] = useState({
    name: "Agent Name",
    title: null as string | null,
    phone: null as string | null,
    email: "agent@example.com",
    photoUrl: null as string | null,
  })

  // Audience step only shows for "just_listed" story
  const needsAudience = state.story === "just_listed"
  const effectiveSteps = needsAudience ? [0, 1, 2, 3] : [0, 2, 3]
  const currentStepIndex = effectiveSteps.indexOf(step)
  const isLastStep = currentStepIndex === effectiveSteps.length - 1

  useEffect(() => {
    async function loadBranding() {
      try {
        const [bRes, pRes] = await Promise.all([
          fetch("/api/proxy/v1/account/branding"),
          fetch("/api/proxy/v1/users/me"),
        ])
        if (bRes.ok) {
          const d = await bRes.json()
          setBranding({
            primaryColor: d.primary_color || "#4F46E5",
            accentColor: d.accent_color || d.secondary_color || "#818CF8",
            headerLogoUrl: d.email_logo_url || d.logo_url || null,
            displayName: d.display_name || d.name || null,
          })
        }
        if (pRes.ok) {
          const p = await pRes.json()
          setProfile({
            name: [p.first_name, p.last_name].filter(Boolean).join(" ") || "Agent Name",
            title: p.job_title || null,
            phone: p.phone || null,
            email: p.email || "agent@example.com",
            photoUrl: p.avatar_url || null,
          })
        }
      } catch { /* silent */ }
    }
    loadBranding()
  }, [])

  // When story changes, set default lookback
  useEffect(() => {
    if (state.story && !state.lookbackDays) {
      setState((prev) => ({ ...prev, lookbackDays: STORY_DEFAULT_LOOKBACK[state.story!] }))
    }
  }, [state.story, state.lookbackDays])

  const update = useCallback((patch: Partial<WizardState>) => {
    setState((prev) => ({ ...prev, ...patch }))
  }, [])

  const canContinue = useMemo(() => {
    switch (step) {
      case 0: return !!state.story
      case 1: return true // audience always has "all" default
      case 2: return (state.areaType === "city" ? !!state.city : state.zipCodes.length > 0) && !!state.lookbackDays
      case 3: return state.deliveryMode === "send_now"
        ? (state.viewInBrowser || state.downloadPdf || state.sendViaEmail)
        : !!state.scheduleName.trim()
      default: return false
    }
  }, [step, state])

  function goNext() {
    if (!canContinue) return
    const idx = effectiveSteps.indexOf(step)
    if (idx < effectiveSteps.length - 1) {
      setStep(effectiveSteps[idx + 1])
    }
  }

  function goBack() {
    const idx = effectiveSteps.indexOf(step)
    if (idx > 0) setStep(effectiveSteps[idx - 1])
  }

  async function handleSubmit() {
    if (!state.story) return
    setIsSubmitting(true)

    const reportType = STORY_TO_REPORT_TYPE[state.story]
    const filters = state.audience && state.audience !== "all"
      ? AUDIENCE_FILTER_PRESETS[state.audience] || null
      : null

    try {
      if (state.deliveryMode === "send_now") {
        const res = await fetch("/api/proxy/v1/reports", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            report_type: reportType,
            city: state.areaType === "city" ? state.city : null,
            zips: state.areaType === "zip" ? state.zipCodes : null,
            lookback_days: state.lookbackDays,
            filters,
          }),
        })
        if (!res.ok) throw new Error("Failed to create report")
        const data = await res.json()
        router.push(`/app/reports/${data.report_id || data.id}`)
      } else {
        const cadenceMap: Record<string, string> = {
          weekly: "weekly",
          biweekly: "weekly",
          monthly: "monthly",
          quarterly: "monthly",
        }
        const res = await fetch("/api/proxy/v1/schedules", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: state.scheduleName,
            report_type: reportType,
            city: state.areaType === "city" ? state.city : null,
            zip_codes: state.areaType === "zip" ? state.zipCodes : null,
            lookback_days: state.lookbackDays,
            cadence: cadenceMap[state.cadence] || "weekly",
            weekly_dow: (state.cadence === "weekly" || state.cadence === "biweekly") ? state.dayOfWeek : null,
            monthly_dom: (state.cadence === "monthly" || state.cadence === "quarterly") ? state.dayOfMonth : null,
            send_hour: state.sendHour,
            send_minute: state.sendMinute,
            timezone: state.timezone,
            recipients: [],
            include_attachment: true,
            active: true,
            filters,
          }),
        })
        if (!res.ok) throw new Error("Failed to create schedule")
        router.push("/app/schedules")
      }
    } catch (err) {
      console.error("Submit error:", err)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Preview config
  const previewReportType = getPreviewReportType(state.story)
  const audienceLabel = getAudienceLabel(state.audience)
  const areaName = getAreaDisplay(state)
  const storyLabel = state.story ? STORIES.find((s) => s.id === state.story)?.title : null

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/95 backdrop-blur-sm border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between max-w-[1400px] mx-auto">
          <div className="flex items-center gap-3">
            <Link href={defaultMode === "schedule" ? "/app/schedules" : "/app/reports"} className="flex items-center justify-center w-8 h-8 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-sm font-semibold text-gray-900">
                {defaultMode === "schedule" ? "New Schedule" : "New Report"}
              </h1>
              <p className="text-[11px] text-gray-500">
                Step {currentStepIndex + 1} of {effectiveSteps.length}: {STEP_LABELS[step]}
              </p>
            </div>
          </div>

          {/* Step indicators */}
          <div className="hidden md:flex items-center gap-1.5">
            {effectiveSteps.map((s, i) => {
              const done = effectiveSteps.indexOf(step) > i
              const current = s === step
              return (
                <div key={s} className="flex items-center gap-1.5">
                  <div className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold transition-colors",
                    done ? "bg-emerald-500 text-white" : current ? "bg-primary text-white" : "bg-gray-200 text-gray-500"
                  )}>
                    {done ? <Check className="w-3 h-3" /> : i + 1}
                  </div>
                  <span className={cn("text-[11px]", current ? "text-gray-900 font-medium" : "text-gray-400")}>
                    {STEP_LABELS[s]}
                  </span>
                  {i < effectiveSteps.length - 1 && <div className="w-6 h-px bg-gray-300" />}
                </div>
              )
            })}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-[1400px] mx-auto px-6 py-6">
        <div className="grid lg:grid-cols-[1fr_420px] gap-6">
          {/* Left: Step content */}
          <div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 min-h-[480px]">
              {step === 0 && <StepStory selected={state.story} onSelect={(s) => update({ story: s, audience: "all" })} />}
              {step === 1 && <StepAudience selected={state.audience} onSelect={(a) => update({ audience: a })} />}
              {step === 2 && <StepWhereWhen state={state} onChange={update} />}
              {step === 3 && <StepDeliver state={state} onChange={update} />}
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between mt-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={goBack}
                disabled={currentStepIndex === 0}
                className="gap-1.5"
              >
                <ChevronLeft className="w-4 h-4" /> Back
              </Button>

              {isLastStep ? (
                <Button
                  onClick={handleSubmit}
                  disabled={!canContinue || isSubmitting}
                  className="gap-1.5"
                >
                  {isSubmitting ? (
                    <><Loader2 className="w-4 h-4 animate-spin" />Processing...</>
                  ) : state.deliveryMode === "schedule" ? (
                    <><Sparkles className="w-4 h-4" />Create Schedule</>
                  ) : (
                    <><Sparkles className="w-4 h-4" />Generate Report</>
                  )}
                </Button>
              ) : (
                <Button onClick={goNext} disabled={!canContinue} className="gap-1.5">
                  Continue <ChevronRight className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>

          {/* Right: Live preview */}
          <div className="hidden lg:block">
            <div className="sticky top-20 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 bg-gray-50/50">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <h3 className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Email Preview</h3>
                <span className="ml-auto text-[10px] text-gray-400">Updates as you build</span>
              </div>

              {/* Summary pills */}
              <div className="px-4 py-2 border-b border-gray-100 flex flex-wrap gap-1.5">
                {storyLabel && <Pill>{storyLabel}</Pill>}
                {audienceLabel && <Pill>{audienceLabel}</Pill>}
                {state.city && <Pill>{state.city}</Pill>}
                {state.zipCodes.length > 0 && <Pill>{state.zipCodes.length} ZIPs</Pill>}
                {state.lookbackDays && <Pill>{state.lookbackDays}d</Pill>}
                {!storyLabel && <span className="text-[10px] text-gray-400 py-0.5">Select a story to preview</span>}
              </div>

              <div className="p-4 bg-stone-100/50 max-h-[calc(100vh-220px)] overflow-y-auto">
                <SharedEmailPreview
                  primaryColor={branding.primaryColor}
                  accentColor={branding.accentColor}
                  headerLogoUrl={branding.headerLogoUrl}
                  displayName={branding.displayName}
                  agentName={profile.name}
                  agentTitle={profile.title}
                  agentPhone={profile.phone}
                  agentEmail={profile.email}
                  agentPhotoUrl={profile.photoUrl}
                  reportType={previewReportType}
                  audienceLabel={audienceLabel}
                  areaName={areaName}
                  lookbackDays={state.lookbackDays || 30}
                  scale={0.92}
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
      {children}
    </span>
  )
}
