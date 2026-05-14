"use client"

import { useState, useEffect, useMemo, useCallback, useRef } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Loader2, ChevronLeft, ChevronRight, Sparkles, Check, FileDown, Globe, CheckCircle2, AlertCircle, Plus, ArrowUpCircle, ArrowLeft } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { SharedEmailPreview, PREVIEW_DEFAULT_PRIMARY, PREVIEW_DEFAULT_ACCENT } from "@/components/shared/email-preview"
import { StepStory } from "./step-story"
import { StepAudience } from "./step-audience"
import { StepWhereWhen } from "./step-where-when"
import { StepDeliver } from "./step-deliver"
import {
  type WizardState,
  type DeliveryMode,
  INITIAL_STATE,
  REPORT_TYPES,
  AUDIENCE_FILTER_PRESETS,
  getAudienceLabel,
  getAreaDisplay,
} from "./types"

const THEME_ID_MAP: Record<number, string> = {
  1: "teal", 2: "bold", 3: "classic", 4: "elegant", 5: "modern",
}

const REPORT_TYPE_LABELS: Record<string, string> = {
  new_listings_gallery: "New Listings Gallery",
  closed: "Closed Sales",
  market_snapshot: "Market Snapshot",
  inventory: "Active Inventory",
  featured_listings: "Featured Listings",
  open_houses: "Open Houses",
  price_bands: "Price Bands",
  new_listings: "New Listings Analytics",
}

type GenerationState = "idle" | "creating" | "polling" | "complete" | "error" | "limit_reached"

interface UnifiedWizardProps {
  defaultMode?: DeliveryMode
  scheduleId?: string
}

const STEP_LABELS = ["Story", "Audience", "Where & When", "Deliver"]

export function UnifiedReportWizard({ defaultMode = "send_now", scheduleId }: UnifiedWizardProps) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [state, setState] = useState<WizardState>({ ...INITIAL_STATE, deliveryMode: defaultMode })
  const [step, setStep] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [branding, setBranding] = useState({
    primaryColor: PREVIEW_DEFAULT_PRIMARY,
    accentColor: PREVIEW_DEFAULT_ACCENT,
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
  const [themeId, setThemeId] = useState("teal")
  const [generationState, setGenerationState] = useState<GenerationState>("idle")
  const [generatedReportId, setGeneratedReportId] = useState<string | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [generationError, setGenerationError] = useState<string | null>(null)
  const [limitInfo, setLimitInfo] = useState<{ product: string; used: number; limit: number } | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const selectedReport = REPORT_TYPES.find(r => r.id === state.reportType)
  const needsAudience = selectedReport?.hasAudienceStep ?? false
  const effectiveSteps = needsAudience ? [0, 1, 2, 3] : [0, 2, 3]
  const currentStepIndex = effectiveSteps.indexOf(step)
  const isLastStep = currentStepIndex === effectiveSteps.length - 1

  useEffect(() => {
    async function loadBranding() {
      try {
        const [bRes, pRes, aRes] = await Promise.all([
          fetch("/api/proxy/v1/account/branding"),
          fetch("/api/proxy/v1/users/me"),
          fetch("/api/proxy/v1/account", { cache: "no-store" }),
        ])
        if (bRes.ok) {
          const d = await bRes.json()
          setBranding({
            primaryColor: d.resolved_primary_color || d.primary_color || PREVIEW_DEFAULT_PRIMARY,
            accentColor: d.resolved_accent_color || d.accent_color || d.secondary_color || PREVIEW_DEFAULT_ACCENT,
            headerLogoUrl: d.resolved_logo_url || d.email_logo_url || d.logo_url || null,
            displayName: d.resolved_display_name || d.display_name || d.brand_display_name || d.name || null,
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
        if (aRes.ok) {
          const a = await aRes.json()
          if (a.default_theme_id && THEME_ID_MAP[a.default_theme_id]) {
            setThemeId(THEME_ID_MAP[a.default_theme_id])
          }
          // Prefer resolved accent (parent inheritance) over the raw secondary_color.
          const resolvedAccent = a.resolved_accent_color || a.secondary_color
          if (resolvedAccent) {
            setBranding((prev) => ({ ...prev, accentColor: resolvedAccent }))
          }
          // Apply resolved logo/primary/displayName too, so wizard preview matches PDF.
          if (a.resolved_logo_url || a.resolved_primary_color || a.resolved_display_name) {
            setBranding((prev) => ({
              ...prev,
              primaryColor: a.resolved_primary_color || prev.primaryColor,
              headerLogoUrl: a.resolved_logo_url || prev.headerLogoUrl,
              displayName: a.resolved_display_name || prev.displayName,
            }))
          }
        }
      } catch { /* silent */ }
    }
    loadBranding()
  }, [])

  useEffect(() => {
    if (state.reportType && !state.lookbackDays) {
      const rt = REPORT_TYPES.find(r => r.id === state.reportType)
      if (rt) setState((prev) => ({ ...prev, lookbackDays: rt.defaultLookback }))
    }
  }, [state.reportType, state.lookbackDays])

  const update = useCallback((patch: Partial<WizardState>) => {
    setState((prev) => ({ ...prev, ...patch }))
  }, [])

  const canContinue = useMemo(() => {
    switch (step) {
      case 0: return !!state.reportType
      case 1: return true // audience always has "all" default
      case 2: return (state.areaType === "city" ? !!state.city : state.zipCodes.length > 0) && !!state.lookbackDays
      case 3: return state.deliveryMode === "send_now"
        ? (!state.sendViaEmail || state.recipients.length > 0)
        : !!state.scheduleName.trim() && state.recipients.length > 0
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

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [])

  function startPolling(reportId: string) {
    setGenerationState("polling")
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/api/proxy/v1/reports/${reportId}`)
        if (!res.ok) return
        const data = await res.json()
        if (data.status === "completed" || data.status === "complete") {
          if (pollingRef.current) clearInterval(pollingRef.current)
          pollingRef.current = null
          setPdfUrl(data.pdf_url || null)
          setGenerationState("complete")
          // Refresh the reports list cache so /app/reports shows the new
          // row immediately instead of waiting out the staleTime window.
          queryClient.invalidateQueries({ queryKey: ["reports"] })
          if (data.pdf_url) {
            window.open(data.pdf_url, "_blank")
            if (state.downloadPdf) triggerDownload(data.pdf_url)
          }
        } else if (data.status === "failed") {
          if (pollingRef.current) clearInterval(pollingRef.current)
          pollingRef.current = null
          setGenerationError("Report generation failed. Please try again.")
          setGenerationState("error")
        }
      } catch { /* ignore polling errors */ }
    }, 3000)
  }

  function triggerDownload(url: string) {
    const a = document.createElement("a")
    a.href = url
    a.download = ""
    a.target = "_blank"
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  async function handleSubmit() {
    if (!state.reportType) return
    setIsSubmitting(true)

    const reportType = state.reportType
    const filters = state.audience && state.audience !== "all"
      ? AUDIENCE_FILTER_PRESETS[state.audience] || null
      : null

    try {
      if (state.deliveryMode === "send_now") {
        setGenerationState("creating")
        const res = await fetch("/api/proxy/v1/reports", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            report_type: reportType,
            city: state.areaType === "city" ? state.city : null,
            zips: state.areaType === "zip" ? state.zipCodes : null,
            lookback_days: state.lookbackDays,
            filters,
            theme_id: themeId,
            accent_color: branding.accentColor,
            ...(state.sendViaEmail && state.recipients.length > 0 && {
              send_email: true,
              recipients: state.recipients.map(r => {
                if (r.type === "manual_email") return r.email;
                if (r.type === "contact") return { type: "contact", id: r.id };
                if (r.type === "group") return { type: "group", id: r.id };
                return r;
              }),
            }),
          }),
        })
        if (!res.ok) {
          if (res.status === 429) {
            const errData = await res.json().catch(() => ({}))
            const productLabels: Record<string, string> = {
              market_reports: "Market Report",
              schedules: "Schedule",
              property_reports: "Property Report",
            }
            const productLabel = errData.product ? (productLabels[errData.product] || "Report") : "Market Report"
            const used = errData.used ?? null
            const limit = errData.limit ?? null
            const detail = used !== null && limit !== null
              ? `You've used ${used} of ${limit} ${productLabel.toLowerCase()}s this month.`
              : errData.detail || errData.message || `You've reached your ${productLabel.toLowerCase()} limit.`
            setGenerationError(`${productLabel} limit reached — ${detail}`)
            setGenerationState("limit_reached")
            setIsSubmitting(false)
            return
          }
          const errData = await res.json().catch(() => ({}))
          throw new Error(errData.detail || errData.message || "Failed to create report")
        }
        const data = await res.json()
        const reportId = data.report_id || data.id
        setGeneratedReportId(reportId)
        startPolling(reportId)
      } else {
        const res = await fetch("/api/proxy/v1/schedules", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: state.scheduleName,
            report_type: reportType,
            city: state.areaType === "city" ? state.city : null,
            zip_codes: state.areaType === "zip" ? state.zipCodes : null,
            lookback_days: state.lookbackDays,
            cadence: state.cadence,
            weekly_dow: state.cadence === "weekly" ? state.dayOfWeek : null,
            monthly_dom: state.cadence === "monthly" ? state.dayOfMonth : null,
            send_hour: state.sendHour,
            send_minute: state.sendMinute,
            timezone: state.timezone,
            recipients: state.recipients.map(r => {
              if (r.type === "manual_email") return r.email;
              if (r.type === "contact") return { type: "contact", id: r.id };
              if (r.type === "group") return { type: "group", id: r.id };
              return r;
            }),
            include_attachment: true,
            active: true,
            filters,
          }),
        })
        if (!res.ok) {
          if (res.status === 429) {
            const errData = await res.json().catch(() => ({}))
            const productLabels: Record<string, string> = {
              market_reports: "Market Report",
              schedules: "Schedule",
              property_reports: "Property Report",
            }
            const productLabel = errData.product ? (productLabels[errData.product] || "Report") : "Schedule"
            const used = errData.used ?? null
            const limit = errData.limit ?? null
            const detail = used !== null && limit !== null
              ? `You've used ${used} of ${limit} ${productLabel.toLowerCase()}s.`
              : errData.detail || errData.message || `You've reached your ${productLabel.toLowerCase()} limit.`
            setGenerationError(`${productLabel} limit reached — ${detail}`)
            setGenerationState("limit_reached")
            setIsSubmitting(false)
            return
          }
          const errData = await res.json().catch(() => ({}))
          throw new Error(errData.detail || errData.message || "Failed to create schedule")
        }
        router.push("/app/schedules")
      }
    } catch (err) {
      if (state.deliveryMode === "send_now") {
        setGenerationError(err instanceof Error ? err.message : "Something went wrong")
        setGenerationState("error")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const previewReportType = (state.reportType || "market_snapshot") as import("@/components/shared/email-preview").PreviewReportType
  const audienceLabel = getAudienceLabel(state.audience)
  const areaName = getAreaDisplay(state)
  const reportLabel = state.reportType ? (REPORT_TYPE_LABELS[state.reportType] || null) : null

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/95 backdrop-blur-sm border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between max-w-[1400px] mx-auto">
          <div className="flex items-center gap-3">
            <Link href={defaultMode === "schedule" ? "/app/schedules" : "/app/reports"} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
              <ChevronLeft className="w-4 h-4" />
              <span>{defaultMode === "schedule" ? "Schedules" : "Reports"}</span>
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

          <div className="flex items-center gap-4">
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

            {generationState === "complete" ? (
              <Button
                size="sm"
                onClick={() => {
                  setState({ ...INITIAL_STATE })
                  setStep(0)
                  setGenerationState("idle")
                  setGeneratedReportId(null)
                  setPdfUrl(null)
                  setGenerationError(null)
                }}
              >
                <Plus className="w-4 h-4 mr-1" />
                {defaultMode === "schedule" ? "New Schedule" : "New Report"}
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push(defaultMode === "schedule" ? "/app/schedules" : "/app/reports")}
              >
                Cancel
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-[1400px] mx-auto px-6 py-6">
        <div className="grid lg:grid-cols-[1fr_460px] gap-6">
          {/* Left: Step content or generation state */}
          <div>
            {generationState !== "idle" ? (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 min-h-[480px] flex items-center justify-center">
                <div className="text-center max-w-sm mx-auto space-y-4">
                  {(generationState === "creating" || generationState === "polling") && (
                    <>
                      <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                        <Loader2 className="w-8 h-8 text-primary animate-spin" />
                      </div>
                      <div>
                        <h2 className="text-lg font-semibold text-gray-900">
                          {generationState === "creating" ? "Creating your report..." : "Generating your report..."}
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">
                          {generationState === "polling"
                            ? "This usually takes 30–60 seconds. Please don\u2019t close this page."
                            : "Setting things up..."}
                        </p>
                      </div>
                      {generationState === "polling" && (
                        <div className="flex justify-center gap-1 pt-2">
                          {[0, 1, 2].map((i) => (
                            <div
                              key={i}
                              className="w-2 h-2 rounded-full bg-primary/40 animate-bounce"
                              style={{ animationDelay: `${i * 150}ms` }}
                            />
                          ))}
                        </div>
                      )}
                    </>
                  )}

                  {generationState === "complete" && (
                    <>
                      <div className="w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center mx-auto">
                        <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                      </div>
                      <div>
                        <h2 className="text-lg font-semibold text-gray-900">Your report is ready!</h2>
                        <p className="text-sm text-gray-500 mt-1">
                          {pdfUrl ? "Your themed PDF has been generated." : "Your report has been generated."}
                        </p>
                      </div>
                      <div className="flex flex-col gap-2 pt-2">
                        {pdfUrl && (
                          <>
                            <Button onClick={() => window.open(pdfUrl!, "_blank")} className="gap-2">
                              <Globe className="w-4 h-4" /> View in Browser
                            </Button>
                            <Button variant="outline" onClick={() => triggerDownload(pdfUrl!)} className="gap-2">
                              <FileDown className="w-4 h-4" /> Download PDF
                            </Button>
                          </>
                        )}
                        <Button
                          variant="ghost"
                          onClick={() => router.push(`/app/reports/${generatedReportId}`)}
                          className="gap-2"
                        >
                          View Report Details
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            queryClient.invalidateQueries({ queryKey: ["reports"] })
                            router.push("/app/reports")
                          }}
                          className="gap-2"
                        >
                          <ArrowLeft className="w-4 h-4" /> Back to Reports
                        </Button>
                      </div>
                    </>
                  )}

                  {generationState === "limit_reached" && (
                    <>
                      <div className="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center mx-auto">
                        <ArrowUpCircle className="w-8 h-8 text-amber-500" />
                      </div>
                      <div>
                        <h2 className="text-lg font-semibold text-gray-900">
                          {generationError?.split(" — ")[0] || "Limit Reached"}
                        </h2>
                        <p className="text-sm text-gray-600 mt-1">
                          {generationError?.split(" — ")[1] || generationError || "You've used all your reports for this billing period."}
                        </p>
                        <p className="text-sm text-gray-500 mt-2">
                          Upgrade your plan to continue, or wait until your limit resets next month.
                        </p>
                      </div>
                      <div className="flex flex-col gap-2 pt-2">
                        <Button onClick={() => router.push("/app/settings/billing")} className="gap-2">
                          <ArrowUpCircle className="w-4 h-4" /> Upgrade Plan
                        </Button>
                        <Button variant="outline" onClick={() => {
                          setGenerationState("idle")
                          setGenerationError(null)
                          setIsSubmitting(false)
                        }}>
                          Go Back
                        </Button>
                      </div>
                    </>
                  )}

                  {generationState === "error" && (
                    <>
                      <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto">
                        <AlertCircle className="w-8 h-8 text-red-500" />
                      </div>
                      <div>
                        <h2 className="text-lg font-semibold text-gray-900">Generation failed</h2>
                        <p className="text-sm text-red-600 mt-1">{generationError || "Something went wrong."}</p>
                      </div>
                      <div className="flex gap-2 justify-center pt-2">
                        <Button variant="outline" onClick={() => {
                          setGenerationState("idle")
                          setGenerationError(null)
                          setIsSubmitting(false)
                        }}>
                          Go Back
                        </Button>
                        <Button onClick={handleSubmit}>Try Again</Button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            ) : (
              <>
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                  {step === 0 && <StepStory selected={state.reportType} onSelect={(rt) => update({ reportType: rt, audience: "all" })} />}
                  {step === 1 && <StepAudience selected={state.audience} onSelect={(a) => update({ audience: a })} />}
                  {step === 2 && <StepWhereWhen state={state} onChange={update} />}
                  {step === 3 && <StepDeliver state={state} onChange={update} defaultMode={defaultMode} />}
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
                      ) : state.sendViaEmail && state.recipients.length > 0 ? (
                        <><Sparkles className="w-4 h-4" />Generate &amp; Send</>
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
              </>
            )}
          </div>

          {/* Right: Live preview */}
          <div className="hidden lg:block">
            <div className="sticky top-20 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 bg-gray-50/50">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <h3 className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                  Email Preview
                </h3>
                <span className="ml-auto text-[10px] text-gray-400">Updates as you build</span>
              </div>

              {/* Summary pills */}
              <div className="px-4 py-2 border-b border-gray-100 flex flex-wrap gap-1.5">
                {reportLabel && <Pill>{reportLabel}</Pill>}
                {audienceLabel && <Pill>{audienceLabel}</Pill>}
                {state.city && <Pill>{state.city}</Pill>}
                {state.zipCodes.length > 0 && <Pill>{state.zipCodes.length} ZIPs</Pill>}
                {state.lookbackDays && <Pill>{state.lookbackDays}d</Pill>}
                {!reportLabel && <span className="text-[10px] text-gray-400 py-0.5">Select a report type to preview</span>}
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
