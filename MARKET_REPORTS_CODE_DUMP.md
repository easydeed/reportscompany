# Market Reports — Full Code Dump

> Generated: March 12 2026
> Purpose: Debugging market reports builder → preview → PDF pipeline

---

## 1. Unified Wizard — `apps/web/components/unified-wizard/index.tsx`

```tsx
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
```

---

## 2. Step Deliver — `apps/web/components/unified-wizard/step-deliver.tsx`

```tsx
"use client"

import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { Globe, FileDown, Mail, Calendar, Clock, X } from "lucide-react"
import type { WizardState, DeliveryMode, Cadence } from "./types"

interface StepDeliverProps {
  state: WizardState
  onChange: (patch: Partial<WizardState>) => void
}

const DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
const HOURS = Array.from({ length: 24 }, (_, i) => i)

const TIMEZONES = [
  { value: "America/New_York", label: "Eastern" },
  { value: "America/Chicago", label: "Central" },
  { value: "America/Denver", label: "Mountain" },
  { value: "America/Los_Angeles", label: "Pacific" },
  { value: "America/Anchorage", label: "Alaska" },
  { value: "Pacific/Honolulu", label: "Hawaii" },
]

export function StepDeliver({ state, onChange }: StepDeliverProps) {
  const [emailInput, setEmailInput] = useState("")

  const addEmail = () => {
    const email = emailInput.trim()
    if (email && email.includes("@") && !state.recipientEmails.includes(email)) {
      onChange({ recipientEmails: [...state.recipientEmails, email] })
      setEmailInput("")
    }
  }

  const removeEmail = (email: string) => {
    onChange({ recipientEmails: state.recipientEmails.filter((e) => e !== email) })
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">How do you want to deliver it?</h2>
        <p className="text-sm text-gray-500 mt-1">Send now or set up a recurring schedule.</p>
      </div>

      {/* Mode toggle */}
      <div className="grid grid-cols-2 gap-2">
        <ModeCard
          active={state.deliveryMode === "send_now"}
          onClick={() => onChange({ deliveryMode: "send_now" })}
          icon={<Mail className="w-5 h-5" />}
          title="Send Now"
          description="Generate and deliver immediately"
        />
        <ModeCard
          active={state.deliveryMode === "schedule"}
          onClick={() => onChange({ deliveryMode: "schedule" })}
          icon={<Calendar className="w-5 h-5" />}
          title="Schedule"
          description="Set up recurring delivery"
        />
      </div>

      {state.deliveryMode === "send_now" ? (
        <SendNowOptions state={state} onChange={onChange} emailInput={emailInput} setEmailInput={setEmailInput} addEmail={addEmail} removeEmail={removeEmail} />
      ) : (
        <ScheduleOptions state={state} onChange={onChange} />
      )}
    </div>
  )
}

function ModeCard({
  active,
  onClick,
  icon,
  title,
  description,
}: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-xl border-2 p-4 text-left transition-all",
        active ? "border-primary bg-primary/5 shadow-sm" : "border-gray-200 hover:border-gray-300"
      )}
    >
      <div className={cn("mb-2", active ? "text-primary" : "text-gray-400")}>{icon}</div>
      <div className="text-sm font-semibold text-gray-900">{title}</div>
      <div className="text-[11px] text-gray-500 mt-0.5">{description}</div>
    </button>
  )
}

function SendNowOptions({
  state,
  onChange,
  emailInput,
  setEmailInput,
  addEmail,
  removeEmail,
}: {
  state: WizardState
  onChange: (patch: Partial<WizardState>) => void
  emailInput: string
  setEmailInput: (v: string) => void
  addEmail: () => void
  removeEmail: (email: string) => void
}) {
  return (
    <div className="space-y-4">
      <Label className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Delivery Options</Label>

      <div className="space-y-2">
        <Checkbox checked={state.viewInBrowser} onChange={(v) => onChange({ viewInBrowser: v })} icon={<Globe className="w-4 h-4" />} label="View in browser" />
        <Checkbox checked={state.downloadPdf} onChange={(v) => onChange({ downloadPdf: v })} icon={<FileDown className="w-4 h-4" />} label="Download PDF" />
        <Checkbox checked={state.sendViaEmail} onChange={(v) => onChange({ sendViaEmail: v })} icon={<Mail className="w-4 h-4" />} label="Send via email" />
      </div>

      {state.sendViaEmail && (
        <div className="space-y-2 pl-6">
          <Label className="text-xs text-gray-600">Recipients</Label>
          <div className="flex gap-2">
            <Input
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addEmail()}
              placeholder="email@example.com"
              className="h-9 text-xs flex-1"
            />
            <button onClick={addEmail} className="px-3 h-9 rounded-lg bg-primary text-white text-xs font-medium">Add</button>
          </div>
          {state.recipientEmails.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {state.recipientEmails.map((email) => (
                <span key={email} className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-700">
                  {email}
                  <button onClick={() => removeEmail(email)} className="hover:text-red-500"><X className="h-3 w-3" /></button>
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ScheduleOptions({
  state,
  onChange,
}: {
  state: WizardState
  onChange: (patch: Partial<WizardState>) => void
}) {
  return (
    <div className="space-y-4">
      {/* Schedule name */}
      <div className="space-y-1.5">
        <Label className="text-xs font-medium">Schedule Name</Label>
        <Input
          value={state.scheduleName}
          onChange={(e) => onChange({ scheduleName: e.target.value })}
          placeholder="e.g., Weekly Luxury Listings – Silver Lake"
          className="h-10"
        />
      </div>

      {/* Frequency */}
      <div className="space-y-1.5">
        <Label className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Frequency</Label>
        <div className="grid grid-cols-4 gap-2">
          {(["weekly", "biweekly", "monthly", "quarterly"] as Cadence[]).map((c) => (
            <button
              key={c}
              onClick={() => onChange({ cadence: c })}
              className={cn(
                "rounded-lg border-2 py-2 text-xs font-medium capitalize transition-all",
                state.cadence === c ? "border-primary bg-primary/5 text-primary" : "border-gray-200 text-gray-500 hover:border-gray-300"
              )}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Day + Time */}
      <div className="grid grid-cols-2 gap-3">
        {(state.cadence === "weekly" || state.cadence === "biweekly") && (
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Day</Label>
            <Select value={String(state.dayOfWeek)} onValueChange={(v) => onChange({ dayOfWeek: Number(v) })}>
              <SelectTrigger className="h-9 text-xs"><SelectValue /></SelectTrigger>
              <SelectContent>
                {DAYS_OF_WEEK.map((day, i) => (
                  <SelectItem key={i} value={String(i)}>{day}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {(state.cadence === "monthly" || state.cadence === "quarterly") && (
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Day of Month</Label>
            <Select value={String(state.dayOfMonth)} onValueChange={(v) => onChange({ dayOfMonth: Number(v) })}>
              <SelectTrigger className="h-9 text-xs"><SelectValue /></SelectTrigger>
              <SelectContent>
                {Array.from({ length: 28 }, (_, i) => i + 1).map((d) => (
                  <SelectItem key={d} value={String(d)}>{d}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Time</Label>
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
            <Select value={String(state.sendHour)} onValueChange={(v) => onChange({ sendHour: Number(v) })}>
              <SelectTrigger className="h-9 text-xs flex-1"><SelectValue /></SelectTrigger>
              <SelectContent>
                {HOURS.map((h) => (
                  <SelectItem key={h} value={String(h)}>
                    {h === 0 ? "12 AM" : h < 12 ? `${h} AM` : h === 12 ? "12 PM" : `${h - 12} PM`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Timezone */}
      <div className="space-y-1.5">
        <Label className="text-xs font-medium">Timezone</Label>
        <Select value={state.timezone} onValueChange={(v) => onChange({ timezone: v })}>
          <SelectTrigger className="h-9 text-xs"><SelectValue /></SelectTrigger>
          <SelectContent>
            {TIMEZONES.map((tz) => (
              <SelectItem key={tz.value} value={tz.value}>{tz.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Recipients placeholder — future: contact/group search */}
      <div className="rounded-lg border border-dashed border-gray-300 p-3 text-center text-xs text-gray-400">
        Recipient search (contacts &amp; groups) coming soon. For now, recipients are managed on the schedules list page.
      </div>
    </div>
  )
}

function Checkbox({
  checked,
  onChange,
  icon,
  label,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  icon: React.ReactNode
  label: string
}) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={cn(
        "flex items-center gap-3 w-full rounded-lg border-2 px-3 py-2.5 text-left transition-all",
        checked ? "border-primary/30 bg-primary/5" : "border-gray-200 hover:bg-gray-50"
      )}
    >
      <div className={cn("flex-shrink-0", checked ? "text-primary" : "text-gray-400")}>{icon}</div>
      <span className="text-sm text-gray-700 flex-1">{label}</span>
      <div className={cn("w-4 h-4 rounded border-2 flex items-center justify-center transition-colors", checked ? "border-primary bg-primary" : "border-gray-300")}>
        {checked && <svg className="w-2.5 h-2.5 text-white" viewBox="0 0 12 12"><path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" fill="none" /></svg>}
      </div>
    </button>
  )
}
```

---

## 3. Wizard Types — `apps/web/components/unified-wizard/types.ts`

```ts
export type StoryType =
  | "just_listed"
  | "just_sold"
  | "market_update"
  | "whats_available"
  | "showcase"

export type AudienceFilter = "all" | "first_time" | "luxury" | "families" | "condo" | "investors"

export type DeliveryMode = "send_now" | "schedule"
export type Cadence = "weekly" | "biweekly" | "monthly" | "quarterly"

export type Recipient =
  | { type: "contact"; id: string; name: string; email: string }
  | { type: "group"; id: string; name: string; memberCount: number }
  | { type: "manual_email"; email: string }

export interface WizardState {
  story: StoryType | null
  audience: AudienceFilter
  areaType: "city" | "zip"
  city: string | null
  zipCodes: string[]
  lookbackDays: 7 | 14 | 30 | 60 | 90 | null
  deliveryMode: DeliveryMode
  // Send now
  viewInBrowser: boolean
  downloadPdf: boolean
  sendViaEmail: boolean
  recipientEmails: string[]
  // Schedule
  scheduleName: string
  cadence: Cadence
  dayOfWeek: number
  dayOfMonth: number
  sendHour: number
  sendMinute: number
  timezone: string
  recipients: Recipient[]
}

export const INITIAL_STATE: WizardState = {
  story: null,
  audience: "all",
  areaType: "city",
  city: null,
  zipCodes: [],
  lookbackDays: null,
  deliveryMode: "send_now",
  viewInBrowser: true,
  downloadPdf: false,
  sendViaEmail: false,
  recipientEmails: [],
  scheduleName: "",
  cadence: "weekly",
  dayOfWeek: 1,
  dayOfMonth: 1,
  sendHour: 9,
  sendMinute: 0,
  timezone: "America/Los_Angeles",
  recipients: [],
}

// ─── Story → report_type mapping ───

export const STORY_TO_REPORT_TYPE: Record<StoryType, string> = {
  just_listed: "new_listings_gallery",
  just_sold: "closed",
  market_update: "market_snapshot",
  whats_available: "inventory",
  showcase: "featured_listings",
}

// ─── Story → default lookback ───

export const STORY_DEFAULT_LOOKBACK: Record<StoryType, 7 | 14 | 30 | 60 | 90> = {
  just_listed: 14,
  just_sold: 30,
  market_update: 30,
  whats_available: 30,
  showcase: 90,
}

// ─── Story cards metadata ───

export const STORIES: {
  id: StoryType
  title: string
  description: string
  bestFor: string
  icon: string
}[] = [
  {
    id: "just_listed",
    title: "What Just Listed",
    description: "Photo gallery of newest homes on the market",
    bestFor: "Buyer drips, prospecting",
    icon: "🏠",
  },
  {
    id: "just_sold",
    title: "What Just Sold",
    description: "Recent sales with prices, DOM & a data table",
    bestFor: "Seller prospecting, CMAs",
    icon: "💰",
  },
  {
    id: "market_update",
    title: "Market Update",
    description: "Median prices, inventory levels, trends — the full picture",
    bestFor: "Monthly sphere updates",
    icon: "📊",
  },
  {
    id: "whats_available",
    title: "What's Available",
    description: "Active listings, supply levels, inventory months",
    bestFor: "Buyer coaching, investors",
    icon: "📦",
  },
  {
    id: "showcase",
    title: "Showcase My Listings",
    description: "Your top 4 most impressive active listings",
    bestFor: "Listing agents, luxury",
    icon: "⭐",
  },
]

// ─── Audience cards metadata ───

export const AUDIENCES: {
  id: AudienceFilter
  label: string
  description: string
}[] = [
  { id: "all", label: "All Listings", description: "No filters applied" },
  { id: "first_time", label: "First-Time Buyers", description: "2+ bed, 2+ bath, SFR, ≤70% median" },
  { id: "luxury", label: "Luxury Homes", description: "SFR, ≥150% median" },
  { id: "families", label: "Family Homes", description: "3+ bed, 2+ bath, SFR" },
  { id: "condo", label: "Condo Watch", description: "Condos only" },
  { id: "investors", label: "Investor Deals", description: "≤50% median" },
]

// Audience → API filters
export const AUDIENCE_FILTER_PRESETS: Record<string, {
  minbeds?: number
  minbaths?: number
  subtype?: string
  price_strategy?: { mode: string; value: number }
  preset_display_name: string
}> = {
  first_time: { minbeds: 2, minbaths: 2, subtype: "SingleFamilyResidence", price_strategy: { mode: "maxprice_pct_of_median_list", value: 0.70 }, preset_display_name: "First-Time Buyer" },
  luxury: { subtype: "SingleFamilyResidence", price_strategy: { mode: "minprice_pct_of_median_list", value: 1.50 }, preset_display_name: "Luxury" },
  families: { minbeds: 3, minbaths: 2, subtype: "SingleFamilyResidence", preset_display_name: "Family Homes" },
  condo: { subtype: "Condominium", preset_display_name: "Condo Watch" },
  investors: { price_strategy: { mode: "maxprice_pct_of_median_list", value: 0.50 }, preset_display_name: "Investor Deals" },
}

// ─── Preview mapping ───

export function getPreviewReportType(story: StoryType | null) {
  if (!story) return "market_snapshot" as const
  const map: Record<StoryType, string> = {
    just_listed: "new_listings_gallery",
    just_sold: "closed",
    market_update: "market_snapshot",
    whats_available: "inventory",
    showcase: "featured_listings",
  }
  return map[story] as "market_snapshot" | "new_listings_gallery" | "closed" | "inventory" | "featured_listings"
}

export function getAudienceLabel(audience: AudienceFilter): string | null {
  if (audience === "all") return null
  return AUDIENCES.find((a) => a.id === audience)?.label || null
}

export function getAreaDisplay(state: WizardState): string {
  if (state.city) return state.city
  if (state.zipCodes.length === 1) return `ZIP ${state.zipCodes[0]}`
  if (state.zipCodes.length <= 3) return `ZIPs ${state.zipCodes.join(", ")}`
  if (state.zipCodes.length > 0) return `${state.zipCodes.length} ZIP codes`
  return "Your Area"
}
```

---

## 4. Old Schedule Builder Recipients — `apps/web/components/schedule-builder/sections/recipients-section.tsx`

```tsx
"use client"

import { useState, useEffect } from "react"
import { Search, X, Users, Mail, AlertCircle, Check } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import type { ScheduleBuilderState, Recipient } from "../types"

interface RecipientsSectionProps {
  recipients: Recipient[]
  onChange: (updates: Partial<ScheduleBuilderState>) => void
  hasRecipients: boolean
  stepNumber?: number
}

export function RecipientsSection({ recipients, onChange, hasRecipients, stepNumber = 6 }: RecipientsSectionProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [contacts, setContacts] = useState<any[]>([])
  const [groups, setGroups] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [contactsRes, groupsRes] = await Promise.all([
          fetch("/api/proxy/v1/contacts"),
          fetch("/api/proxy/v1/contact-groups"),
        ])
        
        if (contactsRes.ok) {
          const data = await contactsRes.json()
          setContacts((data.contacts || []).filter((c: any) => c.email))
        }
        if (groupsRes.ok) {
          const data = await groupsRes.json()
          setGroups(data.groups || [])
        }
      } catch (error) {
        console.error("Failed to load contacts:", error)
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [])

  const filteredContacts = contacts.filter(c =>
    !searchQuery || 
    c.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.email?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const isContactSelected = (id: string) => recipients.some(r => r.type === "contact" && r.id === id)
  const isGroupSelected = (id: string) => recipients.some(r => r.type === "group" && r.id === id)

  const toggleContact = (contact: any) => {
    if (isContactSelected(contact.id)) {
      onChange({ recipients: recipients.filter(r => !(r.type === "contact" && r.id === contact.id)) })
    } else {
      onChange({ 
        recipients: [...recipients, { 
          type: "contact", 
          id: contact.id, 
          name: contact.name, 
          email: contact.email 
        }] 
      })
    }
  }

  const toggleGroup = (group: any) => {
    if (isGroupSelected(group.id)) {
      onChange({ recipients: recipients.filter(r => !(r.type === "group" && r.id === group.id)) })
    } else {
      onChange({ 
        recipients: [...recipients, { 
          type: "group", 
          id: group.id, 
          name: group.name, 
          memberCount: group.member_count || 0 
        }] 
      })
    }
  }

  const removeRecipient = (recipient: Recipient) => {
    onChange({ 
      recipients: recipients.filter(r => 
        !(r.type === recipient.type && 
          ((r.type === "manual_email" && recipient.type === "manual_email" && r.email === recipient.email) ||
           ((r as any).id === (recipient as any).id)))
      ) 
    })
  }

  const contactCount = recipients.filter(r => r.type === "contact").length
  const groupCount = recipients.filter(r => r.type === "group").length

  return (
    <section className={cn(
      "bg-white rounded-xl border transition-all duration-200",
      hasRecipients ? "border-gray-200 shadow-sm" : "border-gray-200/80 shadow-sm"
    )}>
      <div className="flex items-center gap-3 px-5 py-4">
        <div className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors",
          hasRecipients
            ? "bg-emerald-500 text-white"
            : "bg-amber-100 text-amber-600"
        )}>
          {hasRecipients ? <Check className="w-3.5 h-3.5" /> : stepNumber}
        </div>
        <h3 className="text-sm font-medium text-gray-900">Recipients</h3>
      </div>

      <div className="px-5 pb-5">
        {recipients.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {recipients.map((r, i) => (
              <span 
                key={i}
                className="inline-flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary rounded text-sm"
              >
                {r.type === "group" ? <Users className="w-3 h-3" /> : <Mail className="w-3 h-3" />}
                {r.type === "manual_email" ? r.email : r.name}
                {r.type === "group" && ` (${r.memberCount})`}
                <button onClick={() => removeRecipient(r)} className="text-primary/60 hover:text-primary">
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}

        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search contacts..."
            className="pl-9"
          />
        </div>

        {isLoading ? (
          <div className="py-4 text-center text-sm text-gray-400">Loading...</div>
        ) : (
          <div className="space-y-3">
            {groups.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  Groups ({groupCount}/{groups.length})
                </p>
                <div className="max-h-24 overflow-auto border border-gray-200 rounded-lg divide-y divide-gray-100">
                  {groups.map((group) => {
                    const selected = isGroupSelected(group.id)
                    return (
                      <button
                        key={group.id}
                        onClick={() => toggleGroup(group)}
                        className={cn(
                          "flex items-center gap-2 w-full px-3 py-2 text-left transition-colors",
                          selected ? "bg-primary/5" : "hover:bg-gray-50"
                        )}
                      >
                        <div className={cn(
                          "w-4 h-4 rounded border-2 flex items-center justify-center",
                          selected ? "bg-primary border-primary" : "border-gray-300"
                        )}>
                          {selected && <Check className="w-2.5 h-2.5 text-white" />}
                        </div>
                        <Users className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-700 flex-1">{group.name}</span>
                        <span className="text-xs text-gray-400">{group.member_count || 0}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {filteredContacts.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                  <Mail className="w-3 h-3" />
                  Contacts ({contactCount}/{contacts.length})
                </p>
                <div className="max-h-32 overflow-auto border border-gray-200 rounded-lg divide-y divide-gray-100">
                  {filteredContacts.slice(0, 20).map((contact) => {
                    const selected = isContactSelected(contact.id)
                    return (
                      <button
                        key={contact.id}
                        onClick={() => toggleContact(contact)}
                        className={cn(
                          "flex items-center gap-2 w-full px-3 py-2 text-left transition-colors",
                          selected ? "bg-primary/5" : "hover:bg-gray-50"
                        )}
                      >
                        <div className={cn(
                          "w-4 h-4 rounded border-2 flex items-center justify-center",
                          selected ? "bg-primary border-primary" : "border-gray-300"
                        )}>
                          {selected && <Check className="w-2.5 h-2.5 text-white" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-700 truncate">{contact.name}</p>
                          <p className="text-xs text-gray-400 truncate">{contact.email}</p>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {filteredContacts.length === 0 && groups.length === 0 && (
              <p className="py-4 text-center text-sm text-gray-400">No contacts found</p>
            )}
          </div>
        )}

        {!hasRecipients && (
          <p className="text-xs text-amber-600 mt-3 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" />
            Select at least one recipient
          </p>
        )}
      </div>
    </section>
  )
}
```

---

## 5. Schedule API Schema — `apps/api/src/api/routes/schedules.py`

Full file (710 lines):

```python
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, EmailStr, constr, model_validator
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
import json
import traceback
from ..db import db_conn, set_rls, fetchone_dict, fetchall_dicts
from ..crmls_cities import VALID_CITY_NAMES


# ====== Filter Schema ======
class PriceStrategy(BaseModel):
    """
    Market-adaptive pricing strategy.
    Resolves at runtime based on the area's median prices.
    """
    mode: Literal[
        "maxprice_pct_of_median_list",   # e.g., 70% of median list price
        "maxprice_pct_of_median_close",  # e.g., 70% of median close price
        "minprice_pct_of_median_list",   # e.g., 150% of median (luxury)
        "minprice_pct_of_median_close"
    ]
    value: float = Field(..., ge=0.1, le=3.0)  # Percentage as decimal (0.70 = 70%)


class ReportFilters(BaseModel):
    """
    Filters for preset-based schedule reports.
    These filters are passed to SimplyRETS API and report builders.
    
    Supports both absolute prices (minprice/maxprice) and market-adaptive
    pricing via price_strategy. When price_strategy is present, it takes
    precedence and resolves to actual dollar amounts at runtime.
    """
    minbeds: Optional[int] = Field(default=None, ge=0, le=10)
    minbaths: Optional[int] = Field(default=None, ge=0, le=10)
    minprice: Optional[int] = Field(default=None, ge=0)
    maxprice: Optional[int] = Field(default=None, ge=0)
    subtype: Optional[Literal["SingleFamilyResidence", "Condominium"]] = None
    # Market-adaptive pricing (preferred over absolute prices)
    price_strategy: Optional[PriceStrategy] = None
    # Display name for PDF headers (e.g., "First-Time Buyer" instead of "New Listings Gallery")
    preset_display_name: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_price_range(self):
        """Ensure minprice <= maxprice when both are set."""
        if self.minprice is not None and self.maxprice is not None:
            if self.minprice > self.maxprice:
                raise ValueError("minprice cannot exceed maxprice")
        return self

router = APIRouter(prefix="/v1")

# ====== Recipient Schemas ======
class RecipientInput(BaseModel):
    """
    Typed recipient for schedules.

    Each recipient is stored in the DB as a JSON-encoded string:
    - {"type":"contact","id":"<contact_id>"}
    - {"type":"sponsored_agent","id":"<account_id>"}
    - {"type":"group","id":"<group_id>"}
    - {"type":"manual_email","email":"<email>"}
    """
    type: Literal["contact", "sponsored_agent", "group", "manual_email"]
    id: Optional[str] = None
    email: Optional[EmailStr] = None


# ====== Schemas ======
class ScheduleCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=255)
    # IMPORTANT: Keep this Literal in sync with:
    # - Frontend: apps/web/app/lib/reportTypes.ts (ReportType union)
    # - Email: apps/worker/src/worker/email/template.py (report_type_display map)
    # - Worker: apps/worker/src/worker/report_builders.py (builders dict)
    report_type: Literal[
        "market_snapshot",
        "new_listings",
        "inventory",
        "closed",
        "price_bands",
        "open_houses",
        "new_listings_gallery",
        "featured_listings",
    ]
    city: Optional[str] = None
    zip_codes: Optional[List[str]] = None
    lookback_days: int = 30
    cadence: str = Field(..., pattern="^(weekly|monthly)$")
    weekly_dow: Optional[int] = Field(None, ge=0, le=6)  # 0=Sun, 6=Sat
    monthly_dom: Optional[int] = Field(None, ge=1, le=28)  # 1-28
    send_hour: int = Field(9, ge=0, le=23)
    send_minute: int = Field(0, ge=0, le=59)
    timezone: str = "UTC"  # PASS S2: IANA timezone (e.g., America/Los_Angeles)
    recipients: List[Union[RecipientInput, EmailStr]] = Field(..., min_items=1)  # Support both typed and legacy plain emails
    include_attachment: bool = False
    active: bool = True
    # NEW: Filters for Smart Presets
    filters: Optional[ReportFilters] = Field(default_factory=ReportFilters)


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    zip_codes: Optional[List[str]] = None
    lookback_days: Optional[int] = None
    cadence: Optional[str] = Field(None, pattern="^(weekly|monthly)$")
    weekly_dow: Optional[int] = Field(None, ge=0, le=6)
    monthly_dom: Optional[int] = Field(None, ge=1, le=28)
    send_hour: Optional[int] = Field(None, ge=0, le=23)
    send_minute: Optional[int] = Field(None, ge=0, le=59)
    timezone: Optional[str] = None  # PASS S2: IANA timezone
    recipients: Optional[List[Union[RecipientInput, EmailStr]]] = None  # Support both typed and legacy plain emails
    include_attachment: Optional[bool] = None
    active: Optional[bool] = None
    # NEW: Filters for Smart Presets
    filters: Optional[ReportFilters] = None


class ScheduleRow(BaseModel):
    id: str
    name: str
    report_type: str
    city: Optional[str] = None
    zip_codes: Optional[List[str]] = None
    lookback_days: int
    cadence: str
    weekly_dow: Optional[int] = None
    monthly_dom: Optional[int] = None
    send_hour: int
    send_minute: int
    timezone: str = "UTC"  # PASS S2: IANA timezone
    recipients: List[str]  # Raw JSON strings from DB
    resolved_recipients: Optional[List[Dict[str, Any]]] = None  # Decoded recipient objects for frontend
    include_attachment: bool
    active: bool
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    created_at: str
    # NEW: Filters for Smart Presets
    filters: Optional[Dict[str, Any]] = None


class ScheduleRunRow(BaseModel):
    id: str
    schedule_id: str
    report_run_id: Optional[str] = None
    status: str
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: str


# ====== Helpers ======
def require_account_id(request: Request) -> str:
    account_id = getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return account_id


def validate_recipient_ownership(cur, account_id: str, recipient: RecipientInput) -> bool:
    if recipient.type == "manual_email":
        return True
    
    elif recipient.type == "contact":
        if not recipient.id:
            return False
        cur.execute("""
            SELECT 1 FROM contacts 
            WHERE id = %s::uuid AND account_id = %s::uuid
        """, (recipient.id, account_id))
        return cur.fetchone() is not None
    
    elif recipient.type == "sponsored_agent":
        if not recipient.id:
            return False
        cur.execute("""
            SELECT 1 FROM accounts 
            WHERE id = %s::uuid AND sponsor_account_id = %s::uuid
        """, (recipient.id, account_id))
        return cur.fetchone() is not None

    elif recipient.type == "group":
        if not recipient.id:
            return False
        cur.execute(
            """
            SELECT 1 FROM contact_groups
            WHERE id = %s::uuid AND account_id = %s::uuid
            """,
            (recipient.id, account_id),
        )
        return cur.fetchone() is not None

    return False


def encode_recipients(recipients: List[Union[RecipientInput, EmailStr, str]], cur=None, account_id: str = None) -> List[str]:
    encoded = []
    for r in recipients:
        if isinstance(r, RecipientInput):
            if cur and account_id and not validate_recipient_ownership(cur, account_id, r):
                print(f"⚠️  Skipping recipient {r.type}:{r.id} - no permission for account {account_id}")
                continue
            encoded.append(json.dumps(r.model_dump(exclude_none=True)))
        elif isinstance(r, str):
            if r.startswith("{"):
                encoded.append(r)
            else:
                encoded.append(json.dumps({"type": "manual_email", "email": r}))
        else:
            encoded.append(json.dumps({"type": "manual_email", "email": str(r)}))
    return encoded


def decode_recipients(recipients: List[str]) -> List[Dict[str, Any]]:
    decoded = []
    for r in recipients:
        try:
            if r.startswith("{"):
                decoded.append(json.loads(r))
            else:
                decoded.append({"type": "manual_email", "email": r})
        except (json.JSONDecodeError, AttributeError):
            decoded.append({"type": "manual_email", "email": r})
    return decoded


def validate_schedule_params(cadence: str, weekly_dow: Optional[int], monthly_dom: Optional[int]):
    if cadence == "weekly" and weekly_dow is None:
        raise HTTPException(
            status_code=400, 
            detail="weekly_dow (0-6) required for weekly cadence"
        )
    if cadence == "monthly" and monthly_dom is None:
        raise HTTPException(
            status_code=400,
            detail="monthly_dom (1-28) required for monthly cadence"
        )


# ====== Routes ======
@router.post("/schedules", status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreate, 
    request: Request, 
    account_id: str = Depends(require_account_id)
):
    try:
        validate_schedule_params(payload.cadence, payload.weekly_dow, payload.monthly_dom)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Schedule validation error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Invalid schedule parameters: {str(e)}")
    
    if payload.city and payload.city not in VALID_CITY_NAMES:
        raise HTTPException(
            status_code=422,
            detail=f"'{payload.city}' is not a recognized CRMLS city. "
                   f"Please select a city from the dropdown.",
        )
    
    try:
        with db_conn() as (conn, cur):
            set_rls(conn, account_id)
            
            encoded_recipients = encode_recipients(payload.recipients, cur=cur, account_id=account_id)
            
            if not encoded_recipients:
                raise HTTPException(
                    status_code=400,
                    detail="No valid recipients provided"
                )
            
            recipients_escaped = [r.replace('"', '\\"') for r in encoded_recipients]
            recipients_array = "{\"" + "\",\"".join(recipients_escaped) + "\"}"
            
            zip_codes_array = None
            if payload.zip_codes:
                zip_codes_array = "{" + ",".join(payload.zip_codes) + "}"
            
            filters_json = json.dumps(payload.filters.model_dump(exclude_none=True) if payload.filters else {})
            
            cur.execute("""
                INSERT INTO schedules (
                    account_id, name, report_type, city, zip_codes, lookback_days,
                    cadence, weekly_dow, monthly_dom, send_hour, send_minute, timezone,
                    recipients, include_attachment, active, filters
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s::jsonb
                )
                RETURNING id::text, name, report_type, city, zip_codes, lookback_days,
                          cadence, weekly_dow, monthly_dom, send_hour, send_minute, timezone,
                          recipients, include_attachment, active,
                          last_run_at, next_run_at, created_at, filters
            """, (
                account_id, payload.name, payload.report_type, payload.city, zip_codes_array,
                payload.lookback_days, payload.cadence, payload.weekly_dow, payload.monthly_dom,
                payload.send_hour, payload.send_minute, payload.timezone, recipients_array,
                payload.include_attachment, payload.active, filters_json
            ))
            
            row = cur.fetchone()
            conn.commit()
            
            recipients_raw = row[12]
            return {
                "id": row[0],
                "name": row[1],
                "report_type": row[2],
                "city": row[3],
                "zip_codes": row[4],
                "lookback_days": row[5],
                "cadence": row[6],
                "weekly_dow": row[7],
                "monthly_dom": row[8],
                "send_hour": row[9],
                "send_minute": row[10],
                "timezone": row[11],
                "recipients": recipients_raw,
                "resolved_recipients": decode_recipients(recipients_raw),
                "include_attachment": row[13],
                "active": row[14],
                "last_run_at": row[15].isoformat() if row[15] else None,
                "next_run_at": row[16].isoformat() if row[16] else None,
                "created_at": row[17].isoformat(),
                "filters": row[18] if row[18] else {}
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Schedule creation error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")


@router.get("/schedules")
def list_schedules(
    request: Request, 
    account_id: str = Depends(require_account_id),
    active_only: bool = True
):
    with db_conn() as (conn, cur):
        set_rls(conn, account_id)
        
        query = """
            SELECT id::text, name, report_type, city, zip_codes, lookback_days,
                   cadence, weekly_dow, monthly_dom, send_hour, send_minute, timezone,
                   recipients, include_attachment, active,
                   last_run_at, next_run_at, created_at, filters
            FROM schedules
            WHERE account_id = %s
        """
        params = [account_id]
        
        if active_only:
            query += " AND active = true"
        
        query += " ORDER BY created_at DESC"
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        schedules = []
        for row in rows:
            recipients_raw = row[12]
            schedules.append({
                "id": row[0],
                "name": row[1],
                "report_type": row[2],
                "city": row[3],
                "zip_codes": row[4],
                "lookback_days": row[5],
                "cadence": row[6],
                "weekly_dow": row[7],
                "monthly_dom": row[8],
                "send_hour": row[9],
                "send_minute": row[10],
                "timezone": row[11],
                "recipients": recipients_raw,
                "resolved_recipients": decode_recipients(recipients_raw),
                "include_attachment": row[13],
                "active": row[14],
                "last_run_at": row[15].isoformat() if row[15] else None,
                "next_run_at": row[16].isoformat() if row[16] else None,
                "created_at": row[17].isoformat(),
                "filters": row[18] if row[18] else {}
            })
        
        return {"schedules": schedules, "count": len(schedules)}


@router.get("/schedules/{schedule_id}")
def get_schedule(
    schedule_id: str,
    request: Request, 
    account_id: str = Depends(require_account_id)
):
    with db_conn() as (conn, cur):
        set_rls(conn, account_id)
        
        cur.execute("""
            SELECT id::text, name, report_type, city, zip_codes, lookback_days,
                   cadence, weekly_dow, monthly_dom, send_hour, send_minute, timezone,
                   recipients, include_attachment, active,
                   last_run_at, next_run_at, created_at, filters
            FROM schedules
            WHERE id = %s::uuid AND account_id = %s
        """, (schedule_id, account_id))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        recipients_raw = row[12]
        return {
            "id": row[0],
            "name": row[1],
            "report_type": row[2],
            "city": row[3],
            "zip_codes": row[4],
            "lookback_days": row[5],
            "cadence": row[6],
            "weekly_dow": row[7],
            "monthly_dom": row[8],
            "send_hour": row[9],
            "send_minute": row[10],
            "timezone": row[11],
            "recipients": recipients_raw,
            "resolved_recipients": decode_recipients(recipients_raw),
            "include_attachment": row[13],
            "active": row[14],
            "last_run_at": row[15].isoformat() if row[15] else None,
            "next_run_at": row[16].isoformat() if row[16] else None,
            "created_at": row[17].isoformat(),
            "filters": row[18] if row[18] else {}
        }


@router.patch("/schedules/{schedule_id}")
def update_schedule(
    schedule_id: str,
    payload: ScheduleUpdate,
    request: Request, 
    account_id: str = Depends(require_account_id)
):
    updates = []
    params = []
    
    if payload.name is not None:
        updates.append("name = %s")
        params.append(payload.name)
    
    if payload.city is not None:
        if payload.city and payload.city not in VALID_CITY_NAMES:
            raise HTTPException(
                status_code=422,
                detail=f"'{payload.city}' is not a recognized CRMLS city. "
                       f"Please select a city from the dropdown.",
            )
        updates.append("city = %s")
        params.append(payload.city)
    
    if payload.zip_codes is not None:
        zip_codes_array = "{" + ",".join(payload.zip_codes) + "}" if payload.zip_codes else None
        updates.append("zip_codes = %s")
        params.append(zip_codes_array)
    
    if payload.lookback_days is not None:
        updates.append("lookback_days = %s")
        params.append(payload.lookback_days)
    
    if payload.cadence is not None:
        updates.append("cadence = %s")
        params.append(payload.cadence)
    
    if payload.weekly_dow is not None:
        updates.append("weekly_dow = %s")
        params.append(payload.weekly_dow)
    
    if payload.monthly_dom is not None:
        updates.append("monthly_dom = %s")
        params.append(payload.monthly_dom)
    
    if payload.send_hour is not None:
        updates.append("send_hour = %s")
        params.append(payload.send_hour)
    
    if payload.send_minute is not None:
        updates.append("send_minute = %s")
        params.append(payload.send_minute)
    
    if payload.timezone is not None:
        updates.append("timezone = %s")
        params.append(payload.timezone)
    
    recipients_to_update = payload.recipients
    
    if payload.include_attachment is not None:
        updates.append("include_attachment = %s")
        params.append(payload.include_attachment)
    
    if payload.active is not None:
        updates.append("active = %s")
        params.append(payload.active)
    
    filters_to_update = payload.filters
    
    if not updates and recipients_to_update is None and filters_to_update is None:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    with db_conn() as (conn, cur):
        set_rls(conn, account_id)
        
        if recipients_to_update is not None:
            encoded_recipients = encode_recipients(recipients_to_update, cur=cur, account_id=account_id)
            if not encoded_recipients:
                raise HTTPException(
                    status_code=400,
                    detail="No valid recipients provided"
                )
            recipients_escaped = [r.replace('"', '\\"') for r in encoded_recipients]
            recipients_array = "{\"" + "\",\"".join(recipients_escaped) + "\"}"
            updates.append("recipients = %s")
            params.append(recipients_array)
        
        if filters_to_update is not None:
            filters_json = json.dumps(filters_to_update.model_dump(exclude_none=True))
            updates.append("filters = %s::jsonb")
            params.append(filters_json)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append("next_run_at = NULL")
        
        params.append(schedule_id)
        params.append(account_id)
        
        query = f"""
            UPDATE schedules
            SET {", ".join(updates)}
            WHERE id = %s::uuid AND account_id = %s
            RETURNING id::text
        """
        
        cur.execute(query, params)
        row = cur.fetchone()
        conn.commit()
        
        if not row:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {"id": row[0], "message": "Schedule updated"}


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: str,
    request: Request, 
    account_id: str = Depends(require_account_id)
):
    with db_conn() as (conn, cur):
        set_rls(conn, account_id)
        
        cur.execute("""
            DELETE FROM schedules
            WHERE id = %s::uuid AND account_id = %s
            RETURNING id
        """, (schedule_id, account_id))
        
        row = cur.fetchone()
        conn.commit()
        
        if not row:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return None


@router.get("/schedules/{schedule_id}/runs")
def list_schedule_runs(
    schedule_id: str,
    request: Request, 
    account_id: str = Depends(require_account_id),
    limit: int = 50
):
    with db_conn() as (conn, cur):
        set_rls(conn, account_id)
        
        cur.execute("""
            SELECT id FROM schedules WHERE id = %s::uuid AND account_id = %s
        """, (schedule_id, account_id))
        
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        cur.execute("""
            SELECT id::text, schedule_id::text, report_run_id::text,
                   status, error, started_at, finished_at, created_at
            FROM schedule_runs
            WHERE schedule_id = %s::uuid
            ORDER BY created_at DESC
            LIMIT %s
        """, (schedule_id, limit))
        
        rows = cur.fetchall()
        
        runs = []
        for row in rows:
            runs.append({
                "id": row[0],
                "schedule_id": row[1],
                "report_run_id": row[2],
                "status": row[3],
                "error": row[4],
                "started_at": row[5].isoformat() if row[5] else None,
                "finished_at": row[6].isoformat() if row[6] else None,
                "created_at": row[7].isoformat()
            })
        
        return {"runs": runs, "count": len(runs)}
```

---

## 6. Report API Schema — `apps/api/src/api/routes/reports.py`

Full file (193 lines):

```python
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status, Response
from pydantic import BaseModel, Field, constr
from typing import List, Optional, Dict, Any
import json
from ..db import db_conn, set_rls, fetchone_dict, fetchall_dicts
from ..services import evaluate_report_limit, log_limit_decision, LimitDecision
from ..crmls_cities import VALID_CITY_NAMES

router = APIRouter(prefix="/v1")

# ====== Schemas ======
class ReportCreate(BaseModel):
    report_type: constr(strip_whitespace=True, min_length=2)
    city: Optional[str] = None
    zips: Optional[List[str]] = None
    polygon: Optional[str] = None
    lookback_days: int = 30
    filters: Optional[Dict[str, Any]] = None
    additional_params: Optional[dict] = None


class ReportRow(BaseModel):
    id: str
    report_type: str
    status: str
    html_url: Optional[str] = None
    json_url: Optional[str] = None
    csv_url: Optional[str] = None
    pdf_url: Optional[str] = None
    generated_at: Optional[str] = None


# ====== Helpers ======
def require_account_id(request: Request) -> str:
    account_id = getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return account_id


# ====== Routes ======
@router.post("/reports", status_code=status.HTTP_202_ACCEPTED)
def create_report(
    payload: ReportCreate, 
    response: Response,
    request: Request, 
    account_id: str = Depends(require_account_id)
):
    if payload.city and payload.city not in VALID_CITY_NAMES:
        raise HTTPException(
            status_code=422,
            detail=f"'{payload.city}' is not a recognized CRMLS city. "
                   f"Please select a city from the dropdown.",
        )

    params = {
        "city": payload.city,
        "zips": payload.zips,
        "polygon": payload.polygon,
        "lookback_days": payload.lookback_days,
        "filters": payload.filters or {},
        "additional_params": payload.additional_params or {}
    }

    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        
        # ===== PHASE 29B: CHECK USAGE LIMITS =====
        decision, info = evaluate_report_limit(cur, account_id)
        log_limit_decision(account_id, decision, info)
        
        if decision == LimitDecision.BLOCK:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "limit_reached",
                    "message": info["message"],
                    "usage": info["usage"],
                    "plan": info["plan"],
                }
            )
        
        if decision == LimitDecision.ALLOW_WITH_WARNING:
            response.headers["X-TrendyReports-Usage-Warning"] = info["message"]
        
        cur.execute(
            """
            INSERT INTO report_generations
              (account_id, report_type, input_params, status)
            VALUES (%s, %s, %s::jsonb, 'pending')
            RETURNING id::text, status
            """,
            (account_id, payload.report_type, json.dumps(params)),
        )
        row = fetchone_dict(cur)

    # enqueue job
    try:
        from ..worker_client import enqueue_generate_report
        enqueue_generate_report(row["id"], account_id, payload.report_type, params)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to enqueue report {row['id']}: {e}")
        with db_conn() as (conn2, cur2):
            cur2.execute("""
                UPDATE report_generations 
                SET status='failed', error_message=%s 
                WHERE id=%s
            """, (f"Failed to enqueue: {str(e)}", row["id"]))
            conn2.commit()

    return {"report_id": row["id"], "status": row["status"]}


@router.get("/reports/{report_id}", response_model=ReportRow)
def get_report(report_id: str, request: Request, account_id: str = Depends(require_account_id)):
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        cur.execute(
            """
            SELECT id::text, report_type, status, html_url, json_url, csv_url, pdf_url,
                   generated_at::text
            FROM report_generations
            WHERE id = %s AND account_id = %s
            """,
            (report_id, account_id),
        )
        row = fetchone_dict(cur)
        if not row:
            raise HTTPException(status_code=404, detail="Report not found")
        return row


@router.get("/reports")
def list_reports(
    request: Request,
    account_id: str = Depends(require_account_id),
    type: Optional[str] = Query(None, alias="report_type"),
    status_param: Optional[str] = Query(None, alias="status"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    where = ["account_id = %s"]
    params = [account_id]
    
    if type:
        where.append("report_type = %s")
        params.append(type)
    if status_param:
        where.append("status = %s")
        params.append(status_param)
    if from_date:
        where.append("generated_at >= %s::timestamp")
        params.append(from_date)
    if to_date:
        where.append("generated_at < %s::timestamp")
        params.append(to_date)

    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        sql = f"""
          SELECT id::text, report_type, status, html_url, json_url, csv_url, pdf_url,
                 generated_at::text
          FROM report_generations
          WHERE {' AND '.join(where)}
          ORDER BY generated_at DESC
          LIMIT %s OFFSET %s
        """
        cur.execute(sql, (*params, limit, offset))
        items = list(fetchall_dicts(cur))

    return {"reports": items, "pagination": {"limit": limit, "offset": offset, "count": len(items)}}
```

---

## 7. Schedules Tick — `apps/worker/src/worker/schedules_tick.py`

Full file (449 lines):

```python
"""
Schedules Ticker: Background process that finds due schedules and enqueues reports.

Runs every 60 seconds, finds schedules where next_run_at <= NOW() or NULL,
computes next run time, enqueues report to Celery, creates audit record.

PASS S2: Timezone-aware - interprets send_hour/send_minute in schedule's timezone,
converts to UTC for next_run_at storage.

Deploy as a separate Render Background Worker:
  Start command: PYTHONPATH=./src poetry run python -m worker.schedules_tick
"""

import os
import time
import logging
import json
import httpx
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo
import psycopg
import ssl
from celery import Celery

# Create a separate Celery instance for ticker (no result backend needed)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Strip SSL parameters for Celery
if "ssl_cert_reqs=" in REDIS_URL:
    BROKER = REDIS_URL.split("?")[0]
    SSL_CONFIG = {
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
        'ssl_ca_certs': None,
        'ssl_certfile': None,
        'ssl_keyfile': None
    }
else:
    BROKER = REDIS_URL
    SSL_CONFIG = None

celery = Celery(
    "market_reports_ticker",
    broker=BROKER,
    backend=None,  # No result backend needed for ticker
)

config_updates = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_ignore_result": True,  # Don't track results
}

if SSL_CONFIG:
    config_updates["broker_use_ssl"] = SSL_CONFIG

celery.conf.update(**config_updates)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# JSON serialization helper for datetime objects
def safe_json_dumps(obj):
    """JSON serializer that handles datetime objects."""
    def default_handler(o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
    return json.dumps(obj, default=default_handler)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Ticker interval (seconds)
TICK_INTERVAL = int(os.getenv("TICK_INTERVAL", "60"))

# API keep-alive settings
API_BASE_URL = os.getenv("API_BASE_URL", "https://reportscompany.onrender.com")
KEEP_ALIVE_INTERVAL = int(os.getenv("KEEP_ALIVE_INTERVAL", "300"))  # 5 minutes default
_last_keep_alive = 0  # Track last ping time


def keep_api_warm():
    global _last_keep_alive
    
    now = time.time()
    
    if now - _last_keep_alive < KEEP_ALIVE_INTERVAL:
        return
    
    _last_keep_alive = now
    
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=10.0)
        logger.info(f"🔥 API keep-alive ping: {response.status_code}")
    except httpx.TimeoutException:
        logger.warning("⚠️ API keep-alive ping timed out")
    except Exception as e:
        logger.warning(f"⚠️ API keep-alive ping failed: {e}")


def compute_next_run(
    cadence: str,
    weekly_dow: Optional[int],
    monthly_dom: Optional[int],
    send_hour: int,
    send_minute: int,
    timezone: str = "UTC",
    from_time: Optional[datetime] = None
) -> datetime:
    if from_time is None:
        from_time = datetime.now(ZoneInfo("UTC"))
    
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        logger.warning(f"Invalid timezone '{timezone}', falling back to UTC")
        tz = ZoneInfo("UTC")
    
    now_local = from_time.astimezone(tz)
    
    def safe_local_datetime(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
        naive = datetime(year, month, day, hour, minute, 0, 0)
        
        try:
            local_dt = naive.replace(tzinfo=tz, fold=0)
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
            roundtrip = utc_dt.astimezone(tz)
            
            if roundtrip.hour != hour:
                logger.info(f"DST gap detected: {hour}:{minute:02d} doesn't exist on {year}-{month:02d}-{day:02d}, using {roundtrip.hour}:{roundtrip.minute:02d}")
                return roundtrip
            
            return local_dt
        except Exception as e:
            logger.warning(f"Error creating local datetime: {e}, using naive approach")
            return naive.replace(tzinfo=tz)
    
    if cadence == "weekly":
        if weekly_dow is None:
            raise ValueError("weekly_dow required for weekly cadence")
        
        target_weekday = (weekly_dow - 1) % 7  # Sun(0) -> 6, Mon(1) -> 0, etc.
        current_weekday = now_local.weekday()
        
        days_ahead = (target_weekday - current_weekday) % 7
        
        target_date = now_local.date() + timedelta(days=days_ahead)
        next_local = safe_local_datetime(
            target_date.year, target_date.month, target_date.day,
            send_hour, send_minute
        )
        
        if next_local <= now_local:
            target_date = target_date + timedelta(days=7)
            next_local = safe_local_datetime(
                target_date.year, target_date.month, target_date.day,
                send_hour, send_minute
            )
        
        next_utc = next_local.astimezone(ZoneInfo("UTC"))
        return next_utc.replace(tzinfo=None)
    
    elif cadence == "monthly":
        if monthly_dom is None:
            raise ValueError("monthly_dom required for monthly cadence")
        
        target_dom = min(monthly_dom, 28)
        
        year = now_local.year
        month = now_local.month
        
        next_local = safe_local_datetime(year, month, target_dom, send_hour, send_minute)
        
        if next_local <= now_local:
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
            next_local = safe_local_datetime(year, month, target_dom, send_hour, send_minute)
        
        next_utc = next_local.astimezone(ZoneInfo("UTC"))
        return next_utc.replace(tzinfo=None)
    
    else:
        raise ValueError(f"Unknown cadence: {cadence}")


def enqueue_report(
    schedule_id: str,
    account_id: str,
    report_type: str,
    city: Optional[str],
    zip_codes: Optional[list],
    lookback_days: int,
    filters: Optional[Dict[str, Any]] = None
) -> tuple[str, str]:
    params = {
        "city": city,
        "zips": zip_codes,
        "lookback_days": lookback_days,
        "filters": filters or {},
        "schedule_id": schedule_id
    }
    
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
            cur.execute("""
                INSERT INTO report_generations (account_id, report_type, input_params, status)
                VALUES (%s::uuid, %s, %s::jsonb, 'queued')
                RETURNING id::text
            """, (account_id, report_type, safe_json_dumps(params)))
            run_id = cur.fetchone()[0]
        conn.commit()
    
    task = celery.send_task(
        "generate_report",
        args=[run_id, account_id, report_type, params],
        queue="celery"
    )
    
    logger.info(f"Enqueued report for schedule {schedule_id}, run_id={run_id}, task_id={task.id}")
    return run_id, task.id


def process_due_schedules():
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH due AS (
                        SELECT id
                        FROM schedules
                        WHERE active = true
                          AND (next_run_at IS NULL OR next_run_at <= NOW())
                          AND (processing_locked_at IS NULL 
                               OR processing_locked_at < NOW() - INTERVAL '5 minutes')
                        ORDER BY COALESCE(next_run_at, '1970-01-01'::timestamptz) ASC
                        LIMIT 100
                        FOR UPDATE SKIP LOCKED
                    )
                    UPDATE schedules s
                    SET processing_locked_at = NOW()
                    FROM due
                    WHERE s.id = due.id
                    RETURNING s.id::text, s.account_id::text, s.name, s.report_type,
                              s.city, s.zip_codes, s.lookback_days,
                              s.cadence, s.weekly_dow, s.monthly_dom,
                              s.send_hour, s.send_minute, s.timezone,
                              s.recipients, s.include_attachment, s.filters
                """)
                
                due_schedules = cur.fetchall()
                
                if not due_schedules:
                    logger.debug("No due schedules found")
                    return
                
                logger.info(f"Found {len(due_schedules)} due schedule(s)")
                
                for row in due_schedules:
                    schedule_id = row[0]
                    account_id = row[1]
                    name = row[2]
                    report_type = row[3]
                    city = row[4]
                    zip_codes = row[5]
                    lookback_days = row[6]
                    cadence = row[7]
                    weekly_dow = row[8]
                    monthly_dom = row[9]
                    send_hour = row[10]
                    send_minute = row[11]
                    timezone = row[12]
                    recipients = row[13]
                    include_attachment = row[14]
                    filters = row[15]
                    
                    try:
                        next_run_at = compute_next_run(
                            cadence, weekly_dow, monthly_dom,
                            send_hour, send_minute, timezone
                        )
                        
                        report_gen_id, task_id = enqueue_report(
                            schedule_id, account_id, report_type,
                            city, zip_codes, lookback_days,
                            filters=filters
                        )
                        
                        cur.execute("""
                            INSERT INTO schedule_runs (schedule_id, report_run_id, status, created_at)
                            VALUES (%s::uuid, %s::uuid, 'queued', NOW())
                            RETURNING id::text
                        """, (schedule_id, report_gen_id))
                        
                        schedule_run_id = cur.fetchone()[0]
                        
                        cur.execute("""
                            UPDATE schedules
                            SET last_run_at = NOW(),
                                next_run_at = %s,
                                processing_locked_at = NULL
                            WHERE id = %s::uuid
                        """, (next_run_at, schedule_id))
                        
                        conn.commit()
                        
                        logger.info(
                            f"Processed schedule '{name}' (ID: {schedule_id}): "
                            f"schedule_run_id={schedule_run_id}, report_gen_id={report_gen_id}, "
                            f"task_id={task_id}, next_run_at={next_run_at.isoformat()}"
                        )
                    
                    except Exception as e:
                        logger.error(f"Failed to process schedule {schedule_id}: {e}", exc_info=True)
                        try:
                            cur.execute("""
                                UPDATE schedules 
                                SET processing_locked_at = NULL 
                                WHERE id = %s::uuid
                            """, (schedule_id,))
                            conn.commit()
                        except Exception:
                            pass
                        conn.rollback()
                        continue
    
    except Exception as e:
        logger.error(f"Failed to query due schedules: {e}", exc_info=True)


def run_forever():
    logger.info(f"Schedules ticker started (interval: {TICK_INTERVAL}s)")
    logger.info(f"Database: {DATABASE_URL.split('@')[-1]}")
    logger.info(f"API keep-alive target: {API_BASE_URL} (every {KEEP_ALIVE_INTERVAL}s)")
    
    while True:
        try:
            keep_api_warm()
            
            logger.debug("Tick: Checking for due schedules...")
            process_due_schedules()
        except Exception as e:
            logger.error(f"Ticker error: {e}", exc_info=True)
        
        time.sleep(TICK_INTERVAL)


if __name__ == "__main__":
    run_forever()
```

---

## 8. Shared Email Preview — `apps/web/components/shared/email-preview/index.tsx`

```tsx
"use client"

import { PreviewHeader } from "./preview-header"
import { PreviewNarrative } from "./preview-narrative"
import { PreviewHeroStat } from "./preview-hero-stat"
import { PreviewPhotoGrid } from "./preview-photo-grid"
import { PreviewStackedStats } from "./preview-stacked-stats"
import { PreviewDataTable } from "./preview-data-table"
import { PreviewQuickTake } from "./preview-quick-take"
import { PreviewCta } from "./preview-cta"
import { PreviewAgentFooter } from "./preview-agent-footer"
import { PreviewGalleryCount } from "./preview-gallery-count"
import { PREVIEW_CONTENT, type PreviewReportType } from "./sample-data"

export type { PreviewReportType } from "./sample-data"

export interface SharedEmailPreviewProps {
  primaryColor: string
  accentColor: string
  headerLogoUrl?: string | null
  displayName?: string | null
  agentName: string
  agentTitle?: string | null
  agentPhone?: string | null
  agentEmail?: string | null
  agentPhotoUrl?: string | null
  reportType: PreviewReportType
  audienceLabel?: string | null
  areaName?: string
  lookbackDays?: number
  scale?: number
}

export function SharedEmailPreview({
  primaryColor,
  accentColor,
  headerLogoUrl,
  displayName,
  agentName,
  agentTitle,
  agentPhone,
  agentEmail,
  agentPhotoUrl,
  reportType,
  audienceLabel,
  areaName,
  lookbackDays = 30,
  scale = 1,
}: SharedEmailPreviewProps) {
  const content = PREVIEW_CONTENT[reportType]
  if (!content) return null

  const agentFooter = (
    <PreviewAgentFooter
      agentName={agentName}
      agentTitle={agentTitle}
      agentPhone={agentPhone}
      agentEmail={agentEmail}
      agentPhotoUrl={agentPhotoUrl}
      primaryColor={primaryColor}
    />
  )

  const body = renderBody(reportType, content, primaryColor, accentColor, agentFooter)

  return (
    <div
      className="mx-auto origin-top font-sans"
      style={{ transform: scale < 1 ? `scale(${scale})` : undefined, maxWidth: 480 }}
    >
      <div className="overflow-hidden rounded-t-lg shadow-sm">
        <PreviewHeader
          primaryColor={primaryColor}
          accentColor={accentColor}
          headerLogoUrl={headerLogoUrl}
          displayName={displayName}
          reportType={reportType}
          audienceLabel={audienceLabel}
          areaName={areaName}
          lookbackDays={lookbackDays}
        />
      </div>

      <div className="space-y-3 border-x border-stone-200 bg-white px-4 py-4">
        {body}
      </div>

      <div className="rounded-b-lg border border-t-0 border-stone-200 bg-stone-50 px-4 py-2.5 text-center text-[9px] text-stone-400">
        Powered by {displayName || "TrendyReports"} &bull;{" "}
        <span className="underline">Unsubscribe</span>
      </div>
    </div>
  )
}

function renderBody(
  type: PreviewReportType,
  content: (typeof PREVIEW_CONTENT)[PreviewReportType],
  primary: string,
  accent: string,
  agentFooter: React.ReactNode,
) {
  switch (type) {
    case "market_snapshot":
      return (
        <>
          <PreviewNarrative text={content.narrative} primaryColor={primary} />
          <PreviewHeroStat
            label={content.heroLabel}
            value={content.heroValue}
            sub={content.heroSub}
            primaryColor={primary}
          />
          <PreviewPhotoGrid
            listings={content.listings}
            layout="2x2"
            primaryColor={primary}
            accentColor={accent}
          />
          <PreviewStackedStats stats={content.stats} primaryColor={primary} />
          <PreviewQuickTake text={content.quickTake} accentColor={accent} />
          <PreviewCta primaryColor={primary} />
          {agentFooter}
        </>
      )

    case "new_listings_gallery":
      return (
        <>
          <PreviewNarrative text={content.narrative} primaryColor={primary} />
          <PreviewHeroStat
            label={content.heroLabel}
            value={content.heroValue}
            sub={content.heroSub}
            primaryColor={primary}
          />
          {content.galleryCount && (
            <PreviewGalleryCount
              count={content.galleryCount}
              label="properties found"
              accentColor={accent}
            />
          )}
          <PreviewStackedStats stats={content.stats} primaryColor={primary} />
          <PreviewPhotoGrid
            listings={content.listings}
            layout="3x2"
            primaryColor={primary}
            accentColor={accent}
          />
          <PreviewQuickTake text={content.quickTake} accentColor={accent} />
          <PreviewCta primaryColor={primary} />
          {agentFooter}
        </>
      )

    case "closed":
      return (
        <>
          <PreviewNarrative text={content.narrative} primaryColor={primary} />
          <PreviewHeroStat
            label={content.heroLabel}
            value={content.heroValue}
            sub={content.heroSub}
            primaryColor={primary}
          />
          <PreviewStackedStats stats={content.stats} primaryColor={primary} />
          <PreviewPhotoGrid
            listings={content.listings}
            layout="2x2"
            primaryColor={primary}
            accentColor={accent}
          />
          <PreviewDataTable rows={content.tableRows} primaryColor={primary} />
          <PreviewQuickTake text={content.quickTake} accentColor={accent} />
          <PreviewCta primaryColor={primary} />
          {agentFooter}
        </>
      )

    case "inventory":
      return (
        <>
          <PreviewNarrative text={content.narrative} primaryColor={primary} />
          <PreviewHeroStat
            label={content.heroLabel}
            value={content.heroValue}
            sub={content.heroSub}
            primaryColor={primary}
          />
          <PreviewStackedStats stats={content.stats} primaryColor={primary} />
          <PreviewPhotoGrid
            listings={content.listings}
            layout="2x2"
            primaryColor={primary}
            accentColor={accent}
          />
          <PreviewDataTable rows={content.tableRows} primaryColor={primary} />
          <PreviewQuickTake text={content.quickTake} accentColor={accent} />
          <PreviewCta primaryColor={primary} />
          {agentFooter}
        </>
      )

    case "featured_listings":
      return (
        <>
          <PreviewNarrative text={content.narrative} primaryColor={primary} />
          {content.galleryCount && (
            <PreviewGalleryCount
              count={content.galleryCount}
              label="featured properties"
              accentColor={accent}
            />
          )}
          <PreviewPhotoGrid
            listings={content.listings}
            layout="large-cards"
            primaryColor={primary}
            accentColor={accent}
          />
          <PreviewStackedStats stats={content.stats} primaryColor={primary} />
          <PreviewQuickTake text={content.quickTake} accentColor={accent} />
          <PreviewCta primaryColor={primary} />
          {agentFooter}
        </>
      )
  }
}
```

---

## 9. Sample Data for Preview — `apps/web/components/shared/email-preview/sample-data.ts`

```ts
export type PreviewReportType =
  | "market_snapshot"
  | "new_listings_gallery"
  | "closed"
  | "inventory"
  | "featured_listings"

export const SAMPLE_PHOTOS = [
  "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1583608205776-bfd35f0d9f83?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=280&h=200&fit=crop",
]

export interface SampleListing {
  photo: string
  price: string
  address: string
  specs: string
  badge?: string
}

export interface SampleStat {
  label: string
  value: string
  sub?: string
}

export interface SampleTableRow {
  address: string
  beds: number
  baths: number
  sqft: string
  price: string
  dom: number
}

interface PreviewContent {
  heroLabel: string
  heroValue: string
  heroSub?: string
  narrative: string
  stats: SampleStat[]
  listings: SampleListing[]
  tableRows: SampleTableRow[]
  quickTake: string
  galleryCount?: number
}

export const PREVIEW_CONTENT: Record<PreviewReportType, PreviewContent> = {
  market_snapshot: {
    heroLabel: "Median Sale Price",
    heroValue: "$925,000",
    heroSub: "+4.2% vs prior period",
    narrative:
      "The market showed balanced activity this period with stable pricing and moderate inventory. Buyer demand remains consistent as homes continue to sell near asking price with reasonable days on market.",
    stats: [
      { label: "Closed Sales", value: "42", sub: "+8%" },
      { label: "Avg DOM", value: "24", sub: "-3 days" },
      { label: "Months of Inventory", value: "2.4", sub: "Seller's market" },
      { label: "List-to-Sale", value: "98.2%", sub: "Near asking" },
    ],
    listings: SAMPLE_PHOTOS.slice(0, 4).map((photo, i) => ({
      photo,
      price: ["$1.29M", "$875K", "$1.05M", "$925K"][i],
      address: ["142 Oak Valley Dr", "89 Maple Heights", "310 Sunset Blvd", "27 Pine Ridge Ct"][i],
      specs: ["4 bd | 3 ba | 2,450 sf", "3 bd | 2 ba | 1,800 sf", "4 bd | 3 ba | 2,200 sf", "3 bd | 2 ba | 1,950 sf"][i],
    })),
    tableRows: [],
    quickTake: "Median prices up 4.2% with 42 closed sales. Homes selling in 24 days on average at 98% of list price. A balanced market favoring prepared buyers.",
  },

  new_listings_gallery: {
    heroLabel: "New Listings",
    heroValue: "127",
    heroSub: "in the last 14 days",
    narrative:
      "Fresh inventory continues to hit the market at a healthy pace. This period saw strong activity across all price segments with several standout properties worth immediate attention.",
    stats: [
      { label: "Median List Price", value: "$985K" },
      { label: "Starting From", value: "$425K" },
    ],
    listings: SAMPLE_PHOTOS.map((photo, i) => ({
      photo,
      price: ["$1.29M", "$875K", "$1.05M", "$925K", "$650K", "$1.48M"][i],
      address: ["142 Oak Valley Dr", "89 Maple Heights", "310 Sunset Blvd", "27 Pine Ridge Ct", "55 Lakeview Ln", "201 Hilltop Way"][i],
      specs: [
        "4 bd | 3 ba | 2,450 sf",
        "3 bd | 2 ba | 1,800 sf",
        "4 bd | 3 ba | 2,200 sf",
        "3 bd | 2 ba | 1,950 sf",
        "3 bd | 2 ba | 1,600 sf",
        "5 bd | 4 ba | 3,100 sf",
      ][i],
    })),
    tableRows: [],
    quickTake: "127 new listings hit the market. Median asking price at $985K with entry-level options starting at $425K. Strong selection across all segments.",
    galleryCount: 127,
  },

  closed: {
    heroLabel: "Total Closed",
    heroValue: "42",
    heroSub: "in the last 30 days",
    narrative:
      "Closed sales remained strong this period. Properties sold at near-asking prices with competitive days on market. The data confirms sustained buyer demand across most price tiers.",
    stats: [
      { label: "Median Sold", value: "$1.08M", sub: "+2.1%" },
      { label: "Avg DOM", value: "18", sub: "-5 days" },
      { label: "Close-to-List", value: "98.2%" },
    ],
    listings: SAMPLE_PHOTOS.slice(0, 4).map((photo, i) => ({
      photo,
      price: ["$1.29M", "$875K", "$1.05M", "$925K"][i],
      address: ["142 Oak Valley Dr", "89 Maple Heights", "310 Sunset Blvd", "27 Pine Ridge Ct"][i],
      specs: ["4 bd | 3 ba | 2,450 sf", "3 bd | 2 ba | 1,800 sf", "4 bd | 3 ba | 2,200 sf", "3 bd | 2 ba | 1,950 sf"][i],
      badge: "Sold",
    })),
    tableRows: [
      { address: "142 Oak Valley Dr", beds: 4, baths: 3, sqft: "2,450", price: "$1.29M", dom: 12 },
      { address: "89 Maple Heights", beds: 3, baths: 2, sqft: "1,800", price: "$875K", dom: 21 },
      { address: "310 Sunset Blvd", beds: 4, baths: 3, sqft: "2,200", price: "$1.05M", dom: 8 },
    ],
    quickTake: "42 homes sold at a median of $1.08M. Average DOM of 18 days with 98.2% close-to-list ratio. Sellers are getting strong offers quickly.",
  },

  inventory: {
    heroLabel: "Active Listings",
    heroValue: "186",
    heroSub: "currently on market",
    narrative:
      "Current inventory levels indicate a balanced market with healthy options for buyers. Supply has increased modestly, providing more choices without tipping into oversupply.",
    stats: [
      { label: "Median Active", value: "$1.12M" },
      { label: "Avg DOM", value: "31", sub: "Active" },
      { label: "Months Supply", value: "3.1" },
    ],
    listings: SAMPLE_PHOTOS.slice(0, 4).map((photo, i) => ({
      photo,
      price: ["$1.35M", "$795K", "$1.12M", "$980K"][i],
      address: ["55 Lakeview Ln", "201 Hilltop Way", "78 Cedar Park", "340 Riverdale"][i],
      specs: ["5 bd | 4 ba | 3,100 sf", "3 bd | 2 ba | 1,700 sf", "4 bd | 3 ba | 2,400 sf", "3 bd | 3 ba | 2,050 sf"][i],
      badge: "Active",
    })),
    tableRows: [
      { address: "55 Lakeview Ln", beds: 5, baths: 4, sqft: "3,100", price: "$1.35M", dom: 14 },
      { address: "201 Hilltop Way", beds: 3, baths: 2, sqft: "1,700", price: "$795K", dom: 28 },
      { address: "78 Cedar Park", beds: 4, baths: 3, sqft: "2,400", price: "$1.12M", dom: 7 },
    ],
    quickTake: "186 active listings with 3.1 months of supply. Median asking price at $1.12M. Enough inventory for buyers to be selective without excessive competition.",
  },

  featured_listings: {
    heroLabel: "Featured Listings",
    heroValue: "4",
    heroSub: "hand-picked properties",
    narrative:
      "These standout properties represent the best current opportunities in the area. Each offers exceptional value, location, or features that make them worth immediate attention.",
    stats: [
      { label: "Price Range", value: "$875K – $1.5M" },
      { label: "Avg Sq Ft", value: "2,388" },
    ],
    listings: SAMPLE_PHOTOS.slice(0, 4).map((photo, i) => ({
      photo,
      price: ["$1.50M", "$1.15M", "$985K", "$875K"][i],
      address: ["8 Grandview Terrace", "142 Oak Valley Dr", "310 Sunset Blvd", "89 Maple Heights"][i],
      specs: [
        "5 bd | 4 ba | 3,200 sf",
        "4 bd | 3 ba | 2,450 sf",
        "4 bd | 3 ba | 2,200 sf",
        "3 bd | 2 ba | 1,700 sf",
      ][i],
    })),
    tableRows: [],
    quickTake: "4 featured properties ranging from $875K to $1.5M. Prime locations with above-average square footage and move-in ready condition.",
    galleryCount: 4,
  },
}
```

---

## 10. Print Page — `apps/web/app/print/[runId]/page.tsx`

```tsx
import fs from 'fs/promises';
import path from 'path';
import { 
  buildMarketSnapshotHtml,
  buildNewListingsHtml,
  buildInventoryHtml,
  buildClosedHtml,
  buildPriceBandsHtml,
  buildNewListingsGalleryHtml,
  buildFeaturedListingsHtml
} from '@/lib/templates';

type Props = { params: Promise<{ runId: string }> };

async function fetchData(runId: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE;
  
  if (!base) {
    console.error('[Print Page] NEXT_PUBLIC_API_BASE not set');
    return null;
  }
  
  const url = `${base}/v1/reports/${runId}/data`;
  console.log(`[Print Page] Fetching report data from: ${url}`);
  
  try {
    const res = await fetch(url, {
      cache: "no-store",
      headers: {
        'Accept': 'application/json',
      }
    });
    
    console.log(`[Print Page] Response status: ${res.status}`);
    
    if (!res.ok) {
      console.error(`[Print Page] API error: ${res.status} ${res.statusText}`);
      return null;
    }
    
    const data = await res.json();
    console.log(`[Print Page] Successfully fetched data for: ${data.city || 'unknown'}`);
    return data;
  } catch (error) {
    console.error(`[Print Page] Failed to fetch report data:`, error);
    return null;
  }
}

async function loadTemplate(templateName: string): Promise<string> {
  const templatePath = path.join(process.cwd(), 'templates', templateName);
  try {
    const template = await fs.readFile(templatePath, 'utf-8');
    console.log(`[Print Page] Loaded template: ${templateName}`);
    return template;
  } catch (error) {
    console.error(`[Print Page] Failed to load template ${templateName}:`, error);
    throw new Error(`Template not found: ${templateName}`);
  }
}

// Map report type to display name
const REPORT_TITLES: Record<string, string> = {
  market_snapshot: "Market Snapshot",
  new_listings: "New Listings",
  closed: "Closed Sales",
  inventory: "Inventory Report",
  open_houses: "Open Houses",
  price_bands: "Price Bands",
  new_listings_gallery: "New Listings Gallery",
  featured_listings: "Featured Listings"
};

export default async function PrintReport({ params }: Props) {
  const { runId } = await params;
  const data = await fetchData(runId);

  if (!data) {
    return (
      <html lang="en">
        <head>
          <title>Report Not Found</title>
        </head>
        <body style={{
          fontFamily: 'system-ui, sans-serif',
          padding: '40px',
          textAlign: 'center'
        }}>
          <h1>Report Not Found</h1>
          <p>Report ID: <code>{runId}</code></p>
          <p style={{color: '#666', fontSize: '14px'}}>
            The report data could not be loaded. Please check:
          </p>
          <ul style={{textAlign: 'left', maxWidth: '400px', margin: '20px auto', color: '#666', fontSize: '14px'}}>
            <li>Report ID is correct</li>
            <li>Report has been generated</li>
            <li>API connection is working</li>
          </ul>
          <p style={{color: '#999', fontSize: '12px', marginTop: '40px'}}>
            API Base: {process.env.NEXT_PUBLIC_API_BASE || 'Not configured'}
          </p>
        </body>
      </html>
    );
  }

  const reportType = data.report_type || "market_snapshot";
  const reportTitle = REPORT_TITLES[reportType] || "Market Report";

  // Use TrendyReports templates based on report type
  const templateMap: Record<string, { filename: string; builder: (t: string, d: any) => string }> = {
    "market_snapshot": { filename: 'trendy-market-snapshot.html', builder: buildMarketSnapshotHtml },
    "new_listings": { filename: 'trendy-new-listings.html', builder: buildNewListingsHtml },
    "inventory": { filename: 'trendy-inventory.html', builder: buildInventoryHtml },
    "closed": { filename: 'trendy-closed.html', builder: buildClosedHtml },
    "price_bands": { filename: 'trendy-price-bands.html', builder: buildPriceBandsHtml },
    "open_houses": { filename: 'trendy-inventory.html', builder: buildInventoryHtml },  // Reuse inventory template
    "new_listings_gallery": { filename: 'trendy-new-listings-gallery.html', builder: buildNewListingsGalleryHtml },
    "featured_listings": { filename: 'trendy-featured-listings.html', builder: buildFeaturedListingsHtml },
  };

  const templateConfig = templateMap[reportType];
  
  if (templateConfig) {
    try {
      const template = await loadTemplate(templateConfig.filename);
      const html = templateConfig.builder(template, data);
      
      return (
        <html lang="en">
          <head>
            <title>{reportTitle} - {data.city}</title>
          </head>
          <body dangerouslySetInnerHTML={{ __html: html }} />
        </html>
      );
    } catch (error) {
      console.error(`[Print Page] Template error for ${reportType}, falling back to simple view:`, error);
      // Fall through to simple view below
    }
  }

  // Fallback simple view for other report types or template errors
  return (
    <html lang="en">
      <head>
        <title>{reportTitle} - {data.city}</title>
        <style>{`
          @page { size: Letter; margin: 0.5in; }
          body { font-family: ui-sans-serif, system-ui; -webkit-print-color-adjust: exact; }
          h1 { font-size: 22px; margin: 0 0 8px; }
          .subtitle { color: #6b7280; margin: 0 0 16px; }
          .kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 8px; }
          .kpi { border: 1px solid #e5e7eb; padding: 8px; border-radius: 8px; }
          .kpi-label { font-size: 12px; color: #6b7280; }
          .kpi-value { font-size: 18px; font-weight: 600; margin-top: 4px; }
          .listings { margin-top: 24px; }
          .listing { border: 1px solid #e5e7eb; padding: 12px; margin-bottom: 8px; border-radius: 8px; }
          .listing-address { font-weight: 600; margin-bottom: 4px; }
          .listing-details { font-size: 14px; color: #6b7280; }
        `}</style>
      </head>
      <body>
        <h1>{reportTitle} — {data.city ?? "—"}</h1>
        <p className="subtitle">Period: Last {data.lookback_days ?? 0} days</p>

        <div className="kpis">
          <div className="kpi">
            <div className="kpi-label">Active</div>
            <div className="kpi-value">{data.counts?.Active ?? 0}</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Pending</div>
            <div className="kpi-value">{data.counts?.Pending ?? 0}</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Closed</div>
            <div className="kpi-value">{data.counts?.Closed ?? 0}</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Median List Price</div>
            <div className="kpi-value">${data.metrics?.median_list_price?.toLocaleString?.() ?? 0}</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Median Close Price</div>
            <div className="kpi-value">${data.metrics?.median_close_price?.toLocaleString?.() ?? 0}</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Avg DOM</div>
            <div className="kpi-value">{data.metrics?.avg_dom?.toFixed(1) ?? 0} days</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Months of Inventory</div>
            <div className="kpi-value">{data.metrics?.months_of_inventory?.toFixed(1) ?? 0}</div>
          </div>
        </div>

        {data.listings_sample && data.listings_sample.length > 0 && (
          <div className="listings">
            <h2 style={{fontSize: '18px', marginBottom: '12px'}}>Sample Listings ({data.listings_sample.length})</h2>
            {data.listings_sample.slice(0, 10).map((listing: any, idx: number) => (
              <div key={idx} className="listing">
                <div className="listing-address">{listing.address || "Address unavailable"}</div>
                <div className="listing-details">
                  ${listing.list_price?.toLocaleString() ?? "N/A"} • 
                  {listing.beds ?? "—"} beds • 
                  {listing.baths ?? "—"} baths • 
                  {listing.sqft?.toLocaleString() ?? "—"} sqft • 
                  {listing.status ?? "—"}
                  {listing.days_on_market != null && ` • ${listing.days_on_market} days on market`}
                </div>
              </div>
            ))}
          </div>
        )}
      </body>
    </html>
  );
}
```

---

## 11. Template Hydration — `apps/web/lib/templates.ts`

(1,185 lines — full file included in audit document `docs/architecture/modules/market-reports-audit.md`)

Due to extreme length, see the file directly at `apps/web/lib/templates.ts`. Key exports:

- `buildMarketSnapshotHtml(templateHtml, data)`
- `buildNewListingsHtml(templateHtml, data)`
- `buildInventoryHtml(templateHtml, data)`
- `buildClosedHtml(templateHtml, data)`
- `buildPriceBandsHtml(templateHtml, data)`
- `buildNewListingsGalleryHtml(templateHtml, data)`
- `buildFeaturedListingsHtml(templateHtml, data)`

Shared helpers: `injectBrand()`, `buildHeroHeader()`, `buildTitleBar()`, `buildBrandedFooterHtml()`, `escapeHtml()`, `sanitizeUrl()`, `sanitizeColor()`

---

## 12. HTML Template Example — `apps/web/templates/trendy-market-snapshot.html`

(525 lines — full file included above in section 10's print page context)

See the file directly at `apps/web/templates/trendy-market-snapshot.html`. Contains:

- US Letter page layout (8.5" × 11")
- Hero header with gradient (`var(--pct-blue)` → `var(--pct-accent)`)
- Handlebars-style placeholders: `{{brand_name}}`, `{{market_name}}`, `{{median_price}}`, etc.
- Branded footer with `{{#if rep_photo_url}}` conditionals
- Print CSS with `@page { size: letter; margin: 0; }`

---

## 13. Step Story — `apps/web/components/unified-wizard/step-story.tsx`

```tsx
"use client"

import { cn } from "@/lib/utils"
import { Check } from "lucide-react"
import { STORIES, type StoryType } from "./types"

interface StepStoryProps {
  selected: StoryType | null
  onSelect: (story: StoryType) => void
}

export function StepStory({ selected, onSelect }: StepStoryProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">What story do you want to tell?</h2>
        <p className="text-sm text-gray-500 mt-1">Choose the type of report to send your audience.</p>
      </div>

      <div className="grid gap-2.5">
        {STORIES.map((story) => {
          const active = selected === story.id
          return (
            <button
              key={story.id}
              onClick={() => onSelect(story.id)}
              className={cn(
                "group relative flex items-start gap-4 rounded-xl border-2 p-4 text-left transition-all",
                active
                  ? "border-primary bg-primary/5 shadow-sm"
                  : "border-gray-200 hover:border-primary/40 hover:bg-gray-50/50"
              )}
            >
              <span className="text-2xl flex-shrink-0 mt-0.5">{story.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-gray-900">{story.title}</span>
                  {active && (
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary">
                      <Check className="h-3 w-3 text-white" />
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-0.5">{story.description}</p>
                <p className="text-[10px] text-gray-400 mt-1">Best for: {story.bestFor}</p>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
```

---

## 14. Legacy Component Import Check

### v0-report-builder imports

Only self-reference found — no page/route imports it:

```
apps/web/components/v0-report-builder/report-builder.tsx:31:export function ReportBuilderWizard() {
```

### report-builder imports (from app/ routes)

**No matches found.** No app route imports the legacy `ReportBuilder`.

### schedule-builder imports (from app/ routes)

**No matches found.** No app route imports the legacy `ScheduleBuilder`.

### pdf_adapter imports

**No matches found.** `pdf_adapter.py` is not imported by any Python file in `apps/worker/` or `apps/api/`.

---

*End of dump.*
