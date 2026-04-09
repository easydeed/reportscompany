"use client"

import { useState, useEffect, useMemo, useCallback, useRef } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Loader2, ChevronLeft, ChevronRight, Sparkles, Check, FileDown, Globe, CheckCircle2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { SharedEmailPreview } from "@/components/shared/email-preview"
import { SAMPLE_PHOTOS } from "@/components/shared/email-preview/sample-data"
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

const THEME_ID_MAP: Record<number, string> = {
  1: "teal", 2: "bold", 3: "classic", 4: "elegant", 5: "modern",
}

const THEME_HEADER_BG: Record<string, string> = {
  teal: "#18235c", bold: "#1B365D", classic: "#1e3a5f",
  elegant: "#1a1a1a", modern: "#0f172a",
}

const REPORT_TYPE_LABELS: Record<string, string> = {
  new_listings_gallery: "New Listings Gallery",
  closed: "Recently Sold",
  market_snapshot: "Market Snapshot",
  inventory: "Active Inventory",
  featured_listings: "Featured Listings",
}

type GenerationState = "idle" | "creating" | "polling" | "complete" | "error"

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
  const [themeId, setThemeId] = useState("teal")
  const [generationState, setGenerationState] = useState<GenerationState>("idle")
  const [generatedReportId, setGeneratedReportId] = useState<string | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [generationError, setGenerationError] = useState<string | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Audience step only shows for "just_listed" story
  const needsAudience = state.story === "just_listed"
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
        if (aRes.ok) {
          const a = await aRes.json()
          if (a.default_theme_id && THEME_ID_MAP[a.default_theme_id]) {
            setThemeId(THEME_ID_MAP[a.default_theme_id])
          }
          if (a.secondary_color) {
            setBranding((prev) => ({ ...prev, accentColor: a.secondary_color }))
          }
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
    if (!state.story) return
    setIsSubmitting(true)

    const reportType = STORY_TO_REPORT_TYPE[state.story]
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
        if (!res.ok) throw new Error("Failed to create report")
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
        if (!res.ok) throw new Error("Failed to create schedule")
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

            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push(defaultMode === "schedule" ? "/app/schedules" : "/app/reports")}
            >
              Cancel
            </Button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-[1400px] mx-auto px-6 py-6">
        <div className="grid lg:grid-cols-[1fr_420px] gap-6">
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
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 min-h-[480px]">
                  {step === 0 && <StepStory selected={state.story} onSelect={(s) => update({ story: s, audience: "all" })} />}
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
                  {defaultMode === "schedule" ? "Email Preview" : "Report Preview"}
                </h3>
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
                {defaultMode === "schedule" ? (
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
                ) : (
                  <ReportPreview
                    themeId={themeId}
                    primaryColor={branding.primaryColor}
                    accentColor={branding.accentColor}
                    displayName={branding.displayName}
                    agentName={profile.name}
                    agentTitle={profile.title}
                    agentPhone={profile.phone}
                    agentEmail={profile.email}
                    agentPhotoUrl={profile.photoUrl}
                    reportType={previewReportType}
                    areaName={areaName}
                    lookbackDays={state.lookbackDays || 30}
                    logoUrl={branding.headerLogoUrl}
                  />
                )}
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

function ReportPreview({
  themeId,
  primaryColor,
  accentColor,
  displayName,
  agentName,
  agentTitle,
  agentPhone,
  agentEmail,
  agentPhotoUrl,
  reportType,
  areaName,
  lookbackDays,
  logoUrl,
}: {
  themeId: string
  primaryColor: string
  accentColor: string
  displayName: string | null
  agentName: string
  agentTitle?: string | null
  agentPhone?: string | null
  agentEmail?: string | null
  agentPhotoUrl?: string | null
  reportType: string
  areaName: string
  lookbackDays: number
  logoUrl: string | null
}) {
  const darkBg = THEME_HEADER_BG[themeId] || THEME_HEADER_BG.teal
  const label = REPORT_TYPE_LABELS[reportType] || "Market Report"
  const isGallery = reportType === "new_listings_gallery" || reportType === "featured_listings"
  const isSnapshot = reportType === "market_snapshot"
  const contactParts = [agentPhone, agentEmail].filter(Boolean)

  return (
    <div
      className="aspect-[8.5/11] rounded-lg overflow-hidden shadow-md border border-gray-200 bg-white flex flex-col"
      style={{ fontSize: "10px" }}
    >
      {/* Header bar — mirrors PDF template header-bar */}
      <div
        className="px-3 py-2.5 text-white flex items-center justify-between"
        style={{ background: `linear-gradient(135deg, ${darkBg} 0%, ${darkBg}dd 60%, ${accentColor} 100%)` }}
      >
        <div className="flex items-center gap-1.5">
          <div className="w-5 h-5 rounded bg-white/90 flex items-center justify-center overflow-hidden flex-shrink-0">
            {logoUrl ? (
              <img src={logoUrl} alt="" className="w-full h-full object-contain" />
            ) : (
              <span className="text-[6px] font-bold" style={{ color: darkBg }}>
                {(displayName || "MR").slice(0, 2).toUpperCase()}
              </span>
            )}
          </div>
          <div>
            <div className="text-[7px] font-semibold text-white/90 truncate max-w-[100px]">
              {displayName || "Your Brokerage"}
            </div>
            <div className="text-[5px] text-white/60">{label}</div>
          </div>
        </div>
        {agentTitle && (
          <div className="text-[5px] bg-white/15 px-1.5 py-0.5 rounded-full text-white/80 truncate max-w-[80px]">
            {agentTitle}
          </div>
        )}
      </div>

      {/* Title section */}
      <div className="px-3 pt-2 pb-1.5">
        <div className="text-[11px] font-bold" style={{ color: primaryColor }}>{label} — {areaName}</div>
        <div className="text-[6px] text-gray-400 mt-0.5">Last {lookbackDays} days &bull; Live MLS Data</div>
        <div className="h-[2px] rounded mt-1.5 w-12" style={{ backgroundColor: accentColor }} />
      </div>

      {/* Content area */}
      <div className="px-3 py-1.5 space-y-2 flex-1 min-h-0">
        {/* Hero stat */}
        {!isGallery && (
          <div className="text-center py-1">
            <div className="text-[6px] text-gray-400 uppercase tracking-wider mb-0.5">
              {isSnapshot ? "Median Sale Price" : "Avg. Sale Price"}
            </div>
            <div className="text-[18px] font-bold font-serif" style={{ color: primaryColor }}>$825,000</div>
          </div>
        )}

        {isGallery && (
          <div className="flex items-center justify-center gap-1 py-0.5">
            <div
              className="w-4 h-4 rounded-full flex items-center justify-center text-[6px] font-bold text-white"
              style={{ backgroundColor: accentColor }}
            >
              12
            </div>
            <span className="text-[7px] text-gray-500 uppercase tracking-wider">Listings</span>
          </div>
        )}

        {/* Photo grid */}
        <div className={cn("grid gap-1", isGallery ? "grid-cols-3" : "grid-cols-2")}>
          {SAMPLE_PHOTOS.slice(0, isGallery ? 6 : 4).map((url, i) => (
            <div key={i} className="aspect-[4/3] rounded overflow-hidden bg-gray-100">
              <img src={url} alt="" className="w-full h-full object-cover" />
            </div>
          ))}
        </div>

        {/* Stats bar */}
        <div className="flex justify-between bg-gray-50 rounded px-2 py-1.5">
          {[
            { label: "Active", val: "67" },
            { label: "Pending", val: "12" },
            { label: "Sold", val: "38" },
            { label: "Avg DOM", val: "12" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-[8px] font-bold" style={{ color: primaryColor }}>{s.val}</div>
              <div className="text-[5px] text-gray-400">{s.label}</div>
            </div>
          ))}
        </div>

        {/* AI insight */}
        {isSnapshot && (
          <div className="rounded px-2 py-1.5" style={{ backgroundColor: `${accentColor}08`, borderLeft: `3px solid ${accentColor}` }}>
            <div className="h-1.5 bg-gray-100 rounded w-full mb-0.5" />
            <div className="h-1.5 bg-gray-100 rounded w-3/4" />
          </div>
        )}
      </div>

      {/* Agent footer — mirrors PDF agent-footer */}
      <div className="px-3 py-2 bg-gray-50 border-t border-gray-100 mt-auto">
        <div className="flex items-center gap-1.5">
          <div
            className="w-5 h-5 rounded-full flex-shrink-0 overflow-hidden flex items-center justify-center bg-gray-200"
            style={{ border: `1.5px solid ${primaryColor}33` }}
          >
            {agentPhotoUrl ? (
              <img src={agentPhotoUrl} alt="" className="w-full h-full object-cover" />
            ) : (
              <span className="text-[5px] font-semibold text-gray-400">{agentName?.charAt(0) || "?"}</span>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[7px] font-semibold text-gray-800 truncate">{agentName}</div>
            {agentTitle && <div className="text-[5px] text-gray-400">{agentTitle}</div>}
            {contactParts.length > 0 && (
              <div className="text-[5px] truncate" style={{ color: accentColor }}>
                {contactParts.join(" \u2022 ")}
              </div>
            )}
          </div>
          {logoUrl && (
            <img src={logoUrl} alt="" className="h-3 w-auto object-contain opacity-50 flex-shrink-0" />
          )}
        </div>
      </div>
    </div>
  )
}
