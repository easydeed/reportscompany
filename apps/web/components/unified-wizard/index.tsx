"use client"

import { useState, useEffect, useMemo, useCallback, useRef } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Loader2, Check, FileDown, Globe, CheckCircle2, AlertCircle, Plus, ArrowUpCircle, ArrowLeft, ArrowRight } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import { cn } from "@/lib/utils"
import { SharedEmailPreview, PREVIEW_DEFAULT_PRIMARY, PREVIEW_DEFAULT_ACCENT } from "@/components/shared/email-preview"
import { SharedPDFPreview } from "@/components/shared/pdf-preview"
import { VerificationRequired } from "@/components/shared/verification-required"
import { readVerificationRefusal, type VerificationRefusal } from "@/lib/verification"
import { StepStory } from "./step-story"
import { StepAudience } from "./step-audience"
import { StepWhereWhen } from "./step-where-when"
import { StepDeliver } from "./step-deliver"
import { StepHeader } from "./wizard-ui"
import {
  type WizardState,
  type DeliveryMode,
  INITIAL_STATE,
  REPORT_TYPES,
  AUDIENCE_FILTER_PRESETS,
  getAudienceLabel,
  getAreaDisplay,
} from "./types"
import { THEME_ID_TO_NAME, themeName, DEFAULT_THEME_ID } from "@/lib/themes.generated"


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

type GenerationState =
  | "idle" | "creating" | "polling" | "complete" | "error" | "limit_reached"
  // D-019. A distinct state rather than folding into "error": this is a
  // refusal with a specific remedy, and "Try Again" — which is what the
  // error card offers — is the one action that cannot possibly help.
  | "verification_required"

// Cycling waiting-screen stages while we poll the report status. The labels
// mirror what the worker actually does (apps/worker/src/worker/...). Backend
// doesn't expose true progress today, so we time-cycle on advertised
// durations and stick on the final stage until the response arrives.
const POLLING_STAGES: { label: string; durationMs: number }[] = [
  { label: "Pulling MLS data", durationMs: 12000 },
  { label: "Analyzing market activity", durationMs: 13000 },
  { label: "Generating AI market insight", durationMs: 20000 },
  { label: "Rendering your branded PDF", durationMs: 999000 },
]

interface UnifiedWizardProps {
  defaultMode?: DeliveryMode
  scheduleId?: string
}

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
  // A NAME, not an id, because `POST /v1/reports` takes `theme_id` as a
  // string. The literal here was "teal", which the theme cut retired.
  const [themeId, setThemeId] = useState(themeName(DEFAULT_THEME_ID))
  const [generationState, setGenerationState] = useState<GenerationState>("idle")
  const [generatedReportId, setGeneratedReportId] = useState<string | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [generationError, setGenerationError] = useState<string | null>(null)
  const [verificationRefusal, setVerificationRefusal] = useState<VerificationRefusal | null>(null)
  const [limitInfo, setLimitInfo] = useState<{ product: string; used: number; limit: number } | null>(null)
  const [pollingStage, setPollingStage] = useState(0)
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
          // Was a local THEME_ID_MAP wrong on every id (D-163): an
          // account on 4 pre-selected `elegant` and rendered in teal. A
          // retired id falls through to the default set above.
          if (a.default_theme_id && THEME_ID_TO_NAME[a.default_theme_id]) {
            setThemeId(THEME_ID_TO_NAME[a.default_theme_id])
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

  // Cycle through POLLING_STAGES while we wait for the report to finish.
  // Each stage advances on its configured timer; the final stage sticks
  // until generationState transitions out of "polling" (success or error).
  useEffect(() => {
    if (generationState !== "polling") {
      setPollingStage(0)
      return
    }
    let cancelled = false
    const timers: ReturnType<typeof setTimeout>[] = []
    const advance = (idx: number) => {
      if (cancelled || idx >= POLLING_STAGES.length - 1) return
      const t = setTimeout(() => {
        if (cancelled) return
        setPollingStage(idx + 1)
        advance(idx + 1)
      }, POLLING_STAGES[idx].durationMs)
      timers.push(t)
    }
    setPollingStage(0)
    advance(0)
    return () => {
      cancelled = true
      timers.forEach(clearTimeout)
    }
  }, [generationState])

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
          // D-019, checked before the 429 branch because the two are not
          // alternatives: a 403 here never carries limit fields, and reading it
          // as a generic error is what would turn "confirm your email" into
          // "Something went wrong" with a Try Again button.
          const refusal = readVerificationRefusal(await res.clone().json().catch(() => ({})))
          if (refusal) {
            setVerificationRefusal(refusal)
            setGenerationState("verification_required")
            setIsSubmitting(false)
            return
          }
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
          // D-019, checked before the 429 branch because the two are not
          // alternatives: a 403 here never carries limit fields, and reading it
          // as a generic error is what would turn "confirm your email" into
          // "Something went wrong" with a Try Again button.
          const refusal = readVerificationRefusal(await res.clone().json().catch(() => ({})))
          if (refusal) {
            setVerificationRefusal(refusal)
            setGenerationState("verification_required")
            setIsSubmitting(false)
            return
          }
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

  // ── Design's sentence summary ────────────────────────────────────────────
  // "A Closed Sales for Irvine over 30 days, as a PDF." Each slot jumps back to
  // the step that set it, for steps already reached — the same as pressing
  // Back that many times.
  const kindTitle = state.reportType
    ? REPORT_TYPES.find((r) => r.id === state.reportType)?.title ?? null
    : null
  const areaSet = state.areaType === "city" ? !!state.city : state.zipCodes.length > 0
  type Word = { t: string; step?: number }
  const summary: Word[] = kindTitle
    ? [
        { t: "A" },
        { t: kindTitle, step: 0 },
        ...(needsAudience && audienceLabel
          ? [{ t: "for" }, { t: audienceLabel.toLowerCase(), step: 1 }]
          : []),
        { t: "for" },
        { t: areaSet ? areaName : "…", step: 2 },
        ...(state.lookbackDays ? [{ t: "over" }, { t: `${state.lookbackDays} days`, step: 2 }] : []),
        { t: "," },
        state.deliveryMode === "schedule"
          ? { t: `sent ${state.cadence}`, step: 3 }
          : state.sendViaEmail
          ? { t: "emailed with the PDF", step: 3 }
          : { t: "as a PDF", step: 3 },
        { t: "." },
      ]
    : []

  const goTo = (s: number) => {
    if (generationState !== "idle") return
    if (effectiveSteps.indexOf(s) <= currentStepIndex) setStep(s)
  }

  // Design's labels for the rail. The step ids are unchanged.
  const RAIL_LABELS: Record<number, string> = {
    0: "Report",
    1: "Audience",
    2: "Area & window",
    3: defaultMode === "schedule" ? "Schedule" : "Deliver",
  }

  const primaryAction = isSubmitting
    ? "Processing..."
    : state.deliveryMode === "schedule"
    ? "Create Schedule"
    : state.sendViaEmail && state.recipients.length > 0
    ? "Generate & Send"
    : "Generate Report"

  const resetForNew = () => {
    setState({ ...INITIAL_STATE })
    setStep(0)
    setGenerationState("idle")
    setGeneratedReportId(null)
    setPdfUrl(null)
    setGenerationError(null)
  }

  return (
    <div className="flex min-h-screen flex-col bg-white text-[#0F172A]">
      {/* Header — back link, the step rail, exit */}
      <header className="sticky top-0 z-10 flex h-[62px] items-center justify-between gap-6 border-b border-[#ECEAE3] bg-white px-4 md:px-7">
        <h1 className="sr-only">{defaultMode === "schedule" ? "New Schedule" : "New Report"}</h1>
        <Link
          href={defaultMode === "schedule" ? "/app/schedules" : "/app/reports"}
          className="flex items-center gap-2 text-sm font-semibold text-[#334155] hover:text-[#0F172A]"
        >
          <ArrowLeft className="h-4 w-4" />
          {defaultMode === "schedule" ? "Schedules" : "Market reports"}
        </Link>

        <nav aria-label="Steps" className="hidden items-center gap-1.5 md:flex">
          {effectiveSteps.map((s, i) => {
            const done = currentStepIndex > i
            const current = s === step
            const reachable = i <= currentStepIndex && generationState === "idle"
            return (
              <button
                key={s}
                type="button"
                onClick={() => goTo(s)}
                disabled={!reachable}
                aria-current={current ? "step" : undefined}
                className={cn(
                  "flex items-center gap-2 rounded-full px-2.5 py-1.5 text-[13px]",
                  current ? "font-bold text-[#0F172A]" : done ? "font-medium text-[#334155]" : "font-medium text-[#94A3B8]",
                  reachable && !current ? "cursor-pointer hover:text-[#0F172A]" : "cursor-default",
                )}
              >
                <span
                  className={cn(
                    "flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold",
                    current ? "bg-[#0F172A] text-white" : done ? "bg-[#D1FAE5] text-[#047857]" : "bg-[#ECEAE3] text-[#64748B]",
                  )}
                >
                  {done ? <Check className="h-3 w-3" /> : i + 1}
                </span>
                {RAIL_LABELS[s]}
              </button>
            )
          })}
        </nav>
        <span className="text-[13px] font-medium text-[#64748B] md:hidden">
          Step {currentStepIndex + 1} of {effectiveSteps.length}: {RAIL_LABELS[step]}
        </span>

        {generationState === "complete" ? (
          <button
            type="button"
            onClick={resetForNew}
            className="flex items-center gap-1 text-sm font-semibold text-[#64748B] hover:text-[#0F172A]"
          >
            <Plus className="h-4 w-4" />
            {defaultMode === "schedule" ? "New Schedule" : "New Report"}
          </button>
        ) : (
          <button
            type="button"
            onClick={() => router.push(defaultMode === "schedule" ? "/app/schedules" : "/app/reports")}
            className="text-sm font-semibold text-[#64748B] hover:text-[#0F172A]"
          >
            Cancel
          </button>
        )}
      </header>

      <div className="grid flex-1 lg:grid-cols-[minmax(0,480px)_minmax(0,1fr)]">
        {/* Left — the form, or what is happening with it */}
        <section className="flex min-h-[calc(100vh-62px)] flex-col gap-7 border-[#ECEAE3] px-4 py-8 md:px-10 md:pb-8 md:pt-10 lg:border-r">
          {generationState === "idle" && summary.length > 0 && (
            <p className="m-0 flex flex-wrap items-baseline gap-x-1.5 gap-y-1 border-b border-[#ECEAE3] pb-[22px] text-[17px] leading-[1.7] text-[#475569]">
              {summary.map((w, i) =>
                w.step === undefined ? (
                  // Punctuation sits against the word before it, not a gap away.
                  <span key={i} className={w.t === "," || w.t === "." ? "-ml-1.5" : undefined}>
                    {w.t}
                  </span>
                ) : (
                  <button
                    key={i}
                    type="button"
                    onClick={() => goTo(w.step!)}
                    disabled={effectiveSteps.indexOf(w.step) > currentStepIndex}
                    className="border-b-2 pb-px font-bold text-[#0F172A] disabled:cursor-default"
                    style={{ borderColor: w.step === step ? "#4F46E5" : "#D6D3CB" }}
                  >
                    {w.t}
                  </button>
                ),
              )}
            </p>
          )}

          {generationState === "idle" ? (
            <>
              <div className="flex flex-col gap-7">
                {step === 0 && (
                  <StepStory
                    selected={state.reportType}
                    onSelect={(rt) => update({ reportType: rt, audience: "all" })}
                    primaryColor={branding.primaryColor}
                    accentColor={branding.accentColor}
                  />
                )}
                {step === 1 && <StepAudience selected={state.audience} onSelect={(a) => update({ audience: a })} />}
                {step === 2 && <StepWhereWhen state={state} onChange={update} />}
                {step === 3 && <StepDeliver state={state} onChange={update} defaultMode={defaultMode} />}
              </div>

              {/* Footer nav */}
              <div className="mt-auto flex items-center justify-between gap-3 pt-3">
                <button
                  type="button"
                  onClick={goBack}
                  disabled={currentStepIndex === 0}
                  className="text-sm font-semibold text-[#64748B] hover:text-[#0F172A] disabled:invisible"
                >
                  ← Back
                </button>
                {isLastStep ? (
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={!canContinue || isSubmitting}
                    className="inline-flex h-12 items-center gap-2 rounded-[10px] bg-[#0F172A] px-[22px] text-[15px] font-semibold text-white disabled:bg-[#ECEAE3] disabled:text-[#94A3B8]"
                  >
                    {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                    {primaryAction}
                    {!isSubmitting && <ArrowRight className="h-4 w-4" />}
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={goNext}
                    disabled={!canContinue}
                    className="inline-flex h-12 items-center gap-2 rounded-[10px] bg-[#0F172A] px-[22px] text-[15px] font-semibold text-white disabled:bg-[#ECEAE3] disabled:text-[#94A3B8]"
                  >
                    Continue
                    <ArrowRight className="h-4 w-4" />
                  </button>
                )}
              </div>
            </>
          ) : (
            <div className="flex flex-1 flex-col gap-7">
              {(generationState === "creating" || generationState === "polling") && (
                <>
                  <StepHeader
                    title={state.sendViaEmail ? "Building and sending…" : "Building your report…"}
                    sub="This usually takes 30–60 seconds. Please don't close this page."
                  />
                  <ol className="m-0 flex list-none flex-col border-t-[1.5px] border-[#0F172A] p-0">
                    {POLLING_STAGES.map((stage, idx) => {
                      const at = generationState === "creating" ? -1 : pollingStage
                      const isDone = idx < at
                      const isActive = idx === at || (at === -1 && idx === 0)
                      return (
                        <li
                          key={stage.label}
                          className={cn(
                            "flex items-center gap-3.5 border-b border-[#ECEAE3] py-3.5 text-[15px]",
                            isDone || isActive ? "text-[#0F172A]" : "text-[#94A3B8]",
                            isActive ? "font-semibold" : "font-medium",
                          )}
                        >
                          <span
                            className={cn(
                              "flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full",
                              isDone && "bg-[#047857]",
                              isActive && "border-2 border-dashed border-[#0F172A] animate-[spin_1.4s_linear_infinite]",
                              !isDone && !isActive && "border-[1.5px] border-[#CBD5E1]",
                            )}
                          >
                            {isDone && <Check className="h-3 w-3 text-white" />}
                          </span>
                          {stage.label}
                        </li>
                      )
                    })}
                  </ol>
                </>
              )}

              {generationState === "complete" && (
                <>
                  <div className="flex flex-col gap-3">
                    <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[#D1FAE5]">
                      <Check className="h-[22px] w-[22px] text-[#047857]" />
                    </span>
                    <h2 className="m-0 text-[30px] font-extrabold leading-[1.08] tracking-[-0.03em]">
                      Your report is ready.
                    </h2>
                    <p className="m-0 text-base text-[#475569]">
                      {pdfUrl ? "Your themed PDF has been generated." : "Your report has been generated."}
                    </p>
                  </div>
                  <div className="flex flex-col border-t-[1.5px] border-[#0F172A]">
                    {pdfUrl && (
                      <DoneRow icon={<Globe className="h-4 w-4" />} title="View in browser" sub="Opens the PDF in a new tab" onClick={() => window.open(pdfUrl!, "_blank")} />
                    )}
                    {pdfUrl && (
                      <DoneRow icon={<FileDown className="h-4 w-4" />} title="Download PDF" sub="Save it to send or print" onClick={() => triggerDownload(pdfUrl!)} />
                    )}
                    <DoneRow
                      icon={<CheckCircle2 className="h-4 w-4" />}
                      title="View report details"
                      sub="Settings, recipients and history"
                      onClick={() => router.push(`/app/reports/${generatedReportId}`)}
                    />
                  </div>
                  <div className="mt-auto flex gap-2.5">
                    <button
                      type="button"
                      onClick={resetForNew}
                      className="h-[46px] rounded-[9px] border border-[#D6D3CB] px-[18px] text-sm font-semibold"
                    >
                      Make another
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        queryClient.invalidateQueries({ queryKey: ["reports"] })
                        router.push("/app/reports")
                      }}
                      className="inline-flex h-[46px] items-center rounded-[9px] bg-[#0F172A] px-5 text-sm font-semibold text-white"
                    >
                      Back to Reports
                    </button>
                  </div>
                </>
              )}

              {generationState === "limit_reached" && (
                <>
                  <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[#FEF3C7]">
                    <ArrowUpCircle className="h-[22px] w-[22px] text-[#B45309]" />
                  </span>
                  <StepHeader
                    title={generationError?.split(" — ")[0] || "Limit Reached"}
                    sub={generationError?.split(" — ")[1] || generationError || "You've used all your reports for this billing period."}
                  />
                  <p className="m-0 text-[15px] text-[#475569]">
                    Upgrade your plan to continue, or wait until your limit resets next month.
                  </p>
                  <div className="mt-auto flex gap-2.5">
                    <button
                      type="button"
                      onClick={() => {
                        setGenerationState("idle")
                        setGenerationError(null)
                        setIsSubmitting(false)
                      }}
                      className="h-[46px] rounded-[9px] border border-[#D6D3CB] px-[18px] text-sm font-semibold"
                    >
                      Go Back
                    </button>
                    <button
                      type="button"
                      onClick={() => router.push("/app/settings/billing")}
                      className="inline-flex h-[46px] items-center gap-2 rounded-[9px] bg-[#0F172A] px-5 text-sm font-semibold text-white"
                    >
                      <ArrowUpCircle className="h-4 w-4" /> Upgrade Plan
                    </button>
                  </div>
                </>
              )}

              {generationState === "verification_required" && verificationRefusal && (
                <VerificationRequired
                  refusal={verificationRefusal}
                  onBack={() => {
                    setGenerationState("idle")
                    setVerificationRefusal(null)
                    setGenerationError(null)
                    setIsSubmitting(false)
                  }}
                />
              )}

              {generationState === "error" && (
                <>
                  <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[#FEE2E2]">
                    <AlertCircle className="h-[22px] w-[22px] text-[#B91C1C]" />
                  </span>
                  <StepHeader title="Generation failed" sub={generationError || "Something went wrong."} />
                  <div className="mt-auto flex gap-2.5">
                    <button
                      type="button"
                      onClick={() => {
                        setGenerationState("idle")
                        setGenerationError(null)
                        setIsSubmitting(false)
                      }}
                      className="h-[46px] rounded-[9px] border border-[#D6D3CB] px-[18px] text-sm font-semibold"
                    >
                      Go Back
                    </button>
                    <button
                      type="button"
                      onClick={handleSubmit}
                      className="inline-flex h-[46px] items-center rounded-[9px] bg-[#0F172A] px-5 text-sm font-semibold text-white"
                    >
                      Try Again
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </section>

        {/* Right — the live preview */}
        <section
          aria-label={defaultMode === "schedule" ? "Email preview" : "Report preview"}
          className="sticky top-[62px] hidden h-[calc(100vh-62px)] min-w-0 flex-col items-center justify-center gap-4 overflow-hidden bg-[#F4F3EE] px-8 py-10 lg:flex"
        >
          <div
            className={cn(
              "w-full max-w-[480px] shrink-0 overflow-hidden rounded-md",
              defaultMode === "schedule" && "max-h-full overflow-y-auto",
            )}
            style={{ boxShadow: "0 40px 80px -28px rgba(15,23,42,0.4), 0 0 0 1px rgba(15,23,42,0.06)" }}
          >
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
              />
            ) : (
              <SharedPDFPreview
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
              />
            )}
          </div>
          <span className="text-[13px] text-[#64748B]">
            {reportLabel ? "Live preview · sample numbers until generated" : "Pick a report to preview it here"}
          </span>
        </section>
      </div>
    </div>
  )
}

function DoneRow({
  icon,
  title,
  sub,
  onClick,
}: {
  icon: React.ReactNode
  title: string
  sub: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="grid items-center gap-3.5 border-b border-[#ECEAE3] py-3.5 text-left text-[#0F172A] hover:text-[#4F46E5]"
      style={{ gridTemplateColumns: "auto minmax(0,1fr) auto" }}
    >
      <span className="flex h-9 w-9 items-center justify-center rounded-[9px] border border-[#ECEAE3] bg-[#FAFAF7]">
        {icon}
      </span>
      <span className="flex flex-col">
        <span className="text-[15px] font-semibold">{title}</span>
        <span className="text-[13px] text-[#64748B]">{sub}</span>
      </span>
      <ArrowRight className="h-4 w-4 text-[#94A3B8]" />
    </button>
  )
}
