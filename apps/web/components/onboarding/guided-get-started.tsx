"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useQueryClient } from "@tanstack/react-query"
import {
  ArrowLeft,
  ArrowRight,
  Calendar,
  Check,
  CheckCircle2,
  Loader2,
  MapPin,
  RefreshCw,
  Sparkles,
  Users,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { CityCombobox } from "@/components/shared/city-combobox"
import { RecipientsSection } from "@/components/schedule-builder/sections/recipients-section"
import { SharedPDFPreview } from "@/components/shared/pdf-preview"
import { PREVIEW_DEFAULT_ACCENT, PREVIEW_DEFAULT_PRIMARY } from "@/components/shared/email-preview"
import { queryKeys } from "@/hooks/use-api"
import { cn } from "@/lib/utils"
import type { Recipient } from "@/lib/types/recipients"

type SubmitState = "idle" | "creating" | "polling" | "complete" | "error"

type ContactGroup = {
  id: string
  name: string
  member_count?: number
}

type ApiErrorBody = {
  detail?: unknown
  error?: unknown
  message?: unknown
  product?: unknown
  used?: unknown
  limit?: unknown
}

const STEPS = [
  "Welcome",
  "Your people",
  "Your area",
  "Preview",
  "Autopilot",
] as const

const REPORT_TYPE = "market_snapshot"
const LOOKBACK_DAYS = 30
const DEFAULT_TIMEZONE = "America/Los_Angeles"

const THEME_ID_MAP: Record<number, string> = {
  1: "teal",
  2: "bold",
  3: "classic",
  4: "elegant",
  5: "modern",
}

function mapRecipientsForApi(recipients: Recipient[]) {
  return recipients.map((recipient) => {
    if (recipient.type === "manual_email") return recipient.email
    if (recipient.type === "contact") return { type: "contact", id: recipient.id }
    if (recipient.type === "group") return { type: "group", id: recipient.id }
    return recipient
  })
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null
}

function asReadableString(value: unknown) {
  return typeof value === "string" && value.trim() ? value : null
}

function getApiErrorMessage(body: ApiErrorBody, status: number, fallback: string) {
  const detail = isRecord(body.detail) ? body.detail : null
  const source = (detail || body) as ApiErrorBody
  const product = asReadableString(source.product)
  const used = typeof source.used === "number" ? source.used : null
  const limit = typeof source.limit === "number" ? source.limit : null

  if (status === 429 && product === "schedules") {
    const usage = used !== null && limit !== null
      ? ` You've used ${used} of ${limit} schedules.`
      : ""
    return `Schedule limit reached — You've reached your plan's schedule limit.${usage} Upgrade to set up more recurring reports.`
  }

  return (
    asReadableString(source.message) ||
    asReadableString(body.message) ||
    asReadableString(body.detail) ||
    fallback
  )
}

export function GuidedGetStarted() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [step, setStep] = useState(0)
  const [city, setCity] = useState<string | null>(null)
  const [recipients, setRecipients] = useState<Recipient[]>([])
  const [mySphere, setMySphere] = useState<ContactGroup | null>(null)
  const [submitState, setSubmitState] = useState<SubmitState>("idle")
  const [error, setError] = useState<string | null>(null)
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

  const hasDeliverablePeople = recipients.some((recipient) => recipient.type !== "group" || recipient.memberCount > 0)
  const hasEmptyGroupSelected = recipients.some((recipient) => recipient.type === "group" && recipient.memberCount === 0)
  const canContinue = step === 0 || step === 3 || (step === 1 && hasDeliverablePeople) || (step === 2 && !!city)
  const isSubmitting = submitState === "creating" || submitState === "polling"
  const timezone = useMemo(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || DEFAULT_TIMEZONE
    } catch {
      return DEFAULT_TIMEZONE
    }
  }, [])

  useEffect(() => {
    loadContext()
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [])

  async function loadContext() {
    try {
      const [brandingRes, profileRes, accountRes, groupsRes] = await Promise.all([
        fetch("/api/proxy/v1/account/branding"),
        fetch("/api/proxy/v1/users/me"),
        fetch("/api/proxy/v1/account", { cache: "no-store" }),
        fetch("/api/proxy/v1/contact-groups"),
      ])

      if (brandingRes.ok) {
        const data = await brandingRes.json()
        setBranding({
          primaryColor: data.resolved_primary_color || data.primary_color || PREVIEW_DEFAULT_PRIMARY,
          accentColor: data.resolved_accent_color || data.accent_color || data.secondary_color || PREVIEW_DEFAULT_ACCENT,
          headerLogoUrl: data.resolved_logo_url || data.email_logo_url || data.logo_url || null,
          displayName: data.resolved_display_name || data.display_name || data.brand_display_name || data.name || null,
        })
      }

      if (profileRes.ok) {
        const data = await profileRes.json()
        setProfile({
          name: [data.first_name, data.last_name].filter(Boolean).join(" ") || "Agent Name",
          title: data.job_title || null,
          phone: data.phone || null,
          email: data.email || "agent@example.com",
          photoUrl: data.avatar_url || null,
        })
      }

      if (accountRes.ok) {
        const data = await accountRes.json()
        if (data.default_theme_id && THEME_ID_MAP[data.default_theme_id]) {
          setThemeId(THEME_ID_MAP[data.default_theme_id])
        }
        setBranding((prev) => ({
          ...prev,
          primaryColor: data.resolved_primary_color || prev.primaryColor,
          accentColor: data.resolved_accent_color || data.secondary_color || prev.accentColor,
          headerLogoUrl: data.resolved_logo_url || prev.headerLogoUrl,
          displayName: data.resolved_display_name || prev.displayName,
        }))
      }

      if (groupsRes.ok) {
        const data = await groupsRes.json()
        const sphere = (data.groups || []).find((group: ContactGroup) => group.name === "My Sphere") || null
        setMySphere(sphere)
        if (sphere && (sphere.member_count || 0) > 0) {
          setRecipients((current) =>
            current.length > 0
              ? current
              : [{ type: "group", id: sphere.id, name: sphere.name, memberCount: sphere.member_count || 0 }]
          )
        }
      }
    } catch (loadError) {
      console.error("Failed to load guided onboarding context:", loadError)
    }
  }

  async function skipForNow() {
    sessionStorage.setItem("guided_onboarding_skipped", "true")
    try {
      await fetch("/api/proxy/v1/onboarding/dismiss", { method: "POST" })
      queryClient.invalidateQueries({ queryKey: queryKeys.onboarding })
    } catch (skipError) {
      console.error("Failed to dismiss guided onboarding:", skipError)
    } finally {
      router.push("/app")
    }
  }

  function nextStep() {
    if (step < STEPS.length - 1 && canContinue) {
      setStep((current) => current + 1)
    }
  }

  function previousStep() {
    if (step > 0) {
      setStep((current) => current - 1)
    }
  }

  function startPolling(reportId: string) {
    setSubmitState("polling")
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/api/proxy/v1/reports/${reportId}`)
        if (!res.ok) return
        const data = await res.json()

        if (data.status === "completed" || data.status === "complete") {
          if (pollingRef.current) clearInterval(pollingRef.current)
          pollingRef.current = null
          queryClient.invalidateQueries({ queryKey: queryKeys.reports.all })
          queryClient.invalidateQueries({ queryKey: queryKeys.schedules.all })
          queryClient.invalidateQueries({ queryKey: queryKeys.onboarding })
          setSubmitState("complete")
        } else if (data.status === "failed") {
          if (pollingRef.current) clearInterval(pollingRef.current)
          pollingRef.current = null
          setError("The report could not be generated. Your monthly autopilot may still be saved.")
          setSubmitState("error")
        }
      } catch {
        // Keep polling through transient network errors.
      }
    }, 3000)
  }

  async function turnOnAutopilot() {
    if (!city || !hasDeliverablePeople) return

    setSubmitState("creating")
    setError(null)
    const apiRecipients = mapRecipientsForApi(recipients)

    try {
      const reportRes = await fetch("/api/proxy/v1/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_type: REPORT_TYPE,
          city,
          zips: null,
          lookback_days: LOOKBACK_DAYS,
          filters: null,
          theme_id: themeId,
          accent_color: branding.accentColor,
          send_email: true,
          recipients: apiRecipients,
        }),
      })

      if (!reportRes.ok) {
        const details = await reportRes.json().catch(() => ({}))
        throw new Error(getApiErrorMessage(details, reportRes.status, "We could not send your first report."))
      }

      const reportData = await reportRes.json()
      const reportId = reportData.report_id || reportData.id

      const scheduleRes = await fetch("/api/proxy/v1/schedules", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "Monthly Market Snapshot for My Sphere",
          report_type: REPORT_TYPE,
          city,
          zip_codes: null,
          lookback_days: LOOKBACK_DAYS,
          cadence: "monthly",
          weekly_dow: null,
          monthly_dom: 1,
          send_hour: 9,
          send_minute: 0,
          timezone,
          recipients: apiRecipients,
          include_attachment: true,
          active: true,
          filters: null,
        }),
      })

      if (!scheduleRes.ok) {
        const details = await scheduleRes.json().catch(() => ({}))
        throw new Error(getApiErrorMessage(details, scheduleRes.status, "We could not turn on monthly autopilot."))
      }

      queryClient.invalidateQueries({ queryKey: queryKeys.schedules.all })
      if (reportId) {
        startPolling(reportId)
      } else {
        setSubmitState("complete")
      }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Something went wrong.")
      setSubmitState("error")
    }
  }

  if (submitState === "complete") {
    return (
      <main className="min-h-screen bg-gradient-to-br from-primary/5 via-white to-emerald-50 px-6 py-10">
        <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-3xl items-center justify-center">
          <div className="rounded-3xl border border-emerald-200 bg-white p-8 text-center shadow-sm">
            <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50">
              <CheckCircle2 className="h-9 w-9 text-emerald-500" />
            </div>
            <h1 className="text-2xl font-semibold text-gray-950">Your sphere is on autopilot.</h1>
            <p className="mt-3 text-sm text-gray-600">
              Your people are getting a branded Market Snapshot now, and they&apos;ll get a fresh one every month.
            </p>
            <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
              <Button onClick={() => router.push("/app")}>Go to dashboard</Button>
              <Button variant="outline" asChild>
                <Link href="/app/schedules">View monthly autopilot</Link>
              </Button>
            </div>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white/90 px-6 py-4 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">Get Started</p>
            <h1 className="text-lg font-semibold text-gray-950">Put your sphere on autopilot</h1>
          </div>
          <Button variant="ghost" size="sm" onClick={skipForNow}>
            Skip for now
          </Button>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[minmax(0,1fr)_500px]">
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            {STEPS.map((label, index) => (
              <div key={label} className="flex flex-1 items-center gap-2">
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold",
                    index < step
                      ? "bg-emerald-500 text-white"
                      : index === step
                      ? "bg-primary text-white"
                      : "bg-gray-200 text-gray-500"
                  )}
                >
                  {index < step ? <Check className="h-4 w-4" /> : index + 1}
                </div>
                <span className={cn("hidden text-xs font-medium sm:block", index === step ? "text-gray-900" : "text-gray-400")}>
                  {label}
                </span>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            {step === 0 && (
              <div className="space-y-5">
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                  <Sparkles className="h-6 w-6" />
                </div>
                <div>
                  <h2 className="text-2xl font-semibold text-gray-950">Let&apos;s get your first touchpoint out.</h2>
                  <p className="mt-3 max-w-xl text-sm text-gray-600">
                    In a few minutes, your people can receive a branded Market Snapshot from you. Then we&apos;ll keep you top-of-mind every month.
                  </p>
                </div>
                <div className="grid gap-3 sm:grid-cols-3">
                  <ValueCard icon={<Users className="h-4 w-4" />} title="Your people" text="Start with My Sphere." />
                  <ValueCard icon={<MapPin className="h-4 w-4" />} title="Your area" text="Pick one local market." />
                  <ValueCard icon={<Calendar className="h-4 w-4" />} title="Monthly autopilot" text="We keep the rhythm going." />
                </div>
              </div>
            )}

            {step === 1 && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-xl font-semibold text-gray-950">Add your people.</h2>
                  <p className="mt-2 text-sm text-gray-600">
                    Choose My Sphere, select a few contacts, or add an email. Need to import a list first?
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Button variant="outline" size="sm" asChild>
                      <Link href="/app/people">Import people</Link>
                    </Button>
                    <Button variant="ghost" size="sm" onClick={loadContext} className="gap-1.5">
                      <RefreshCw className="h-3.5 w-3.5" />
                      Refresh My Sphere
                    </Button>
                  </div>
                </div>
                {mySphere && (
                  <div className="rounded-xl border border-primary/15 bg-primary/5 px-4 py-3 text-sm text-gray-700">
                    My Sphere is ready with {mySphere.member_count || 0} people.
                  </div>
                )}
                <RecipientsSection
                  recipients={recipients}
                  onChange={setRecipients}
                  hasRecipients={hasDeliverablePeople}
                  title="Your people"
                  emptyMessage="Add at least one person to send your first report."
                  stepNumber={2}
                />
                {hasEmptyGroupSelected && !hasDeliverablePeople && (
                  <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
                    My Sphere is ready, but it needs people in it before autopilot can send.
                  </p>
                )}
              </div>
            )}

            {step === 2 && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-xl font-semibold text-gray-950">Pick the market they care about.</h2>
                  <p className="mt-2 text-sm text-gray-600">
                    We&apos;ll start with a 30-day Market Snapshot so your sphere gets a simple, useful update.
                  </p>
                </div>
                <CityCombobox value={city} onChange={(selected) => setCity(selected?.city || null)} placeholder="Search for your city" />
              </div>
            )}

            {step === 3 && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-xl font-semibold text-gray-950">Here&apos;s what your people will see.</h2>
                  <p className="mt-2 text-sm text-gray-600">
                    Your branding is already applied. No setup detour, no extra configuration.
                  </p>
                </div>
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                  Market Snapshot for {city || "your area"} · branded from {profile.name}
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-xl font-semibold text-gray-950">Turn on monthly autopilot.</h2>
                  <p className="mt-2 text-sm text-gray-600">
                    We&apos;ll send today&apos;s branded Market Snapshot now, then keep your sphere warm with a fresh one every month.
                  </p>
                </div>
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm">
                  <div className="flex items-center justify-between gap-4">
                    <span className="font-medium text-gray-900">Monthly Market Snapshot</span>
                    <span className="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">Ready</span>
                  </div>
                  <p className="mt-2 text-gray-600">
                    Area: {city}. People: {recipients.length} selected. Cadence: monthly on the 1st at 9:00 AM.
                  </p>
                </div>
                {error && (
                  <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={previousStep} disabled={step === 0 || isSubmitting} className="gap-1.5">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>

            {step < STEPS.length - 1 ? (
              <Button onClick={nextStep} disabled={!canContinue} className="gap-1.5">
                Continue
                <ArrowRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button onClick={turnOnAutopilot} disabled={isSubmitting || !city || !hasDeliverablePeople} className="gap-1.5">
                {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {submitState === "polling" ? "Sending your first report..." : "Send first report + turn on monthly"}
              </Button>
            )}
          </div>
        </section>

        <aside className="rounded-2xl border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-100 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">Live branded preview</p>
          </div>
          <div className="max-h-[calc(100vh-180px)] overflow-y-auto bg-stone-100/60 p-4">
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
              reportType={REPORT_TYPE}
              audienceLabel={null}
              areaName={city || "Your Area"}
              lookbackDays={LOOKBACK_DAYS}
              scale={0.92}
            />
          </div>
        </aside>
      </div>
    </main>
  )
}

function ValueCard({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
      <div className="mb-3 inline-flex h-8 w-8 items-center justify-center rounded-lg bg-white text-primary shadow-sm">
        {icon}
      </div>
      <p className="text-sm font-semibold text-gray-900">{title}</p>
      <p className="mt-1 text-xs text-gray-500">{text}</p>
    </div>
  )
}
