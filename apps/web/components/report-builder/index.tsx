"use client"

import { useState, useCallback, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import {
  ArrowLeft,
  Loader2,
  Check,
  AlertCircle,
  MapPin,
  FileText,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Download,
  Eye,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { ReportTypeSection } from "./sections/report-type-section"
import { AreaSection } from "./sections/area-section"
import { AudienceSection } from "./sections/audience-section"
import { DeliverySection } from "./sections/delivery-section"
import { ReportPreview } from "./report-preview"
import type {
  ReportBuilderState,
  ReportApiPayload,
  BrandingContext,
  ProfileContext,
} from "./types"
import {
  REPORT_TYPE_CONFIG,
  AUDIENCE_FILTERS,
  AUDIENCE_FILTER_PRESETS,
  getAreaDisplay,
} from "./types"

const initialState: ReportBuilderState = {
  reportType: "market_snapshot",
  lookbackDays: 30,
  areaType: "city",
  city: null,
  zipCodes: [],
  audienceFilter: null,
  audienceFilterName: null,
  viewInBrowser: true,
  downloadPdf: true,
  downloadSocialImage: false,
  sendViaEmail: false,
  emailRecipients: [],
}

const defaultBranding: BrandingContext = {
  primaryColor: "#6366f1",
  accentColor: "#8b5cf6",
  pdfHeaderLogoUrl: null,
  displayName: null,
}

const defaultProfile: ProfileContext = {
  name: "Your Name",
  jobTitle: "Real Estate Agent",
  avatarUrl: null,
  phone: null,
  email: "you@example.com",
}

// Progress stages for the loading animation
const PROGRESS_STAGES = [
  { id: "queued", label: "Queuing report..." },
  { id: "fetching", label: "Fetching MLS data..." },
  { id: "processing", label: "Processing listings..." },
  { id: "generating", label: "Generating PDF..." },
  { id: "uploading", label: "Uploading to cloud..." },
]

type GenerationState = "idle" | "generating" | "completed" | "failed"

export function ReportBuilder() {
  const router = useRouter()
  const [state, setState] = useState<ReportBuilderState>(initialState)
  const [openSections, setOpenSections] = useState<string[]>(["report-type"])

  // Branding and profile for preview
  const [branding, setBranding] = useState<BrandingContext>(defaultBranding)
  const [profile, setProfile] = useState<ProfileContext>(defaultProfile)

  // Generation state
  const [generationState, setGenerationState] = useState<GenerationState>("idle")
  const [currentStage, setCurrentStage] = useState(0)
  const [run, setRun] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  // Load branding and profile data for preview
  useEffect(() => {
    async function loadContextData() {
      try {
        // Fetch branding
        const brandingRes = await fetch("/api/proxy/v1/account/branding", {
          credentials: "include",
        })
        if (brandingRes.ok) {
          const brandingData = await brandingRes.json()
          setBranding({
            primaryColor: brandingData.primary_color || defaultBranding.primaryColor,
            accentColor: brandingData.secondary_color || defaultBranding.accentColor,
            pdfHeaderLogoUrl: brandingData.logo_url || null,
            displayName: brandingData.name || null,
          })
        }

        // Fetch profile
        const profileRes = await fetch("/api/proxy/v1/users/me", {
          credentials: "include",
        })
        if (profileRes.ok) {
          const profileData = await profileRes.json()
          const fullName =
            [profileData.first_name, profileData.last_name].filter(Boolean).join(" ") ||
            "Your Name"
          setProfile({
            name: fullName,
            jobTitle: profileData.job_title || null,
            avatarUrl: profileData.avatar_url || null,
            phone: profileData.phone || null,
            email: profileData.email || "you@example.com",
          })
        }
      } catch (err) {
        console.error("Failed to load branding/profile:", err)
      }
    }

    loadContextData()
  }, [])

  // Animate through progress stages while generating
  useEffect(() => {
    if (generationState !== "generating") return

    const interval = setInterval(() => {
      setCurrentStage((prev) => {
        if (prev < PROGRESS_STAGES.length - 1) return prev + 1
        return prev
      })
    }, 2500)

    return () => clearInterval(interval)
  }, [generationState])

  const updateState = useCallback((updates: Partial<ReportBuilderState>) => {
    setState((prev) => ({ ...prev, ...updates }))
  }, [])

  // Validation
  const isAreaValid =
    state.areaType === "city" ? !!state.city : state.zipCodes.length > 0
  const hasDeliveryOption =
    state.viewInBrowser ||
    state.downloadPdf ||
    state.downloadSocialImage ||
    state.sendViaEmail
  const isEmailValid = !state.sendViaEmail || state.emailRecipients.length > 0
  const isValid = isAreaValid && hasDeliveryOption && isEmailValid

  // Section statuses
  const getAreaStatus = () => (isAreaValid ? "complete" : "warning")
  const getAudienceStatus = () =>
    state.audienceFilter && state.audienceFilter !== "all" ? "complete" : "optional"
  const getDeliveryStatus = () => {
    if (!hasDeliveryOption) return "warning"
    if (state.sendViaEmail && state.emailRecipients.length === 0) return "warning"
    return "complete"
  }

  const areaDisplay = getAreaDisplay(state)
  const audienceLabel =
    state.audienceFilter && state.audienceFilter !== "all"
      ? AUDIENCE_FILTERS.find((f) => f.value === state.audienceFilter)?.label
      : null

  const handleGenerate = async () => {
    if (!isValid) return

    setGenerationState("generating")
    setCurrentStage(0)
    setError(null)
    setRun(null)

    try {
      // Build filters from audience filter selection
      const filters =
        state.audienceFilter && state.audienceFilter !== "all"
          ? AUDIENCE_FILTER_PRESETS[state.audienceFilter]
          : null

      // Build API payload
      const payload: ReportApiPayload = {
        report_type: state.reportType,
        city: state.areaType === "city" ? state.city : null,
        zip_codes: state.areaType === "zip" ? state.zipCodes : null,
        lookback_days: state.lookbackDays,
        filters: filters,
      }

      const res = await fetch(`/api/proxy/v1/reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      })

      const j = await res.json()
      if (!res.ok) throw new Error(j?.detail || "Create failed")

      const id = j.report_id

      // Poll for completion
      let tries = 0
      const poll = async () => {
        tries++
        const r = await fetch(`/api/proxy/v1/reports/${id}`, { credentials: "include" })
        const jj = await r.json()
        setRun(jj)

        if (jj.status === "completed") {
          setGenerationState("completed")

          // Handle delivery options after completion
          if (state.viewInBrowser && jj.html_url) {
            window.open(jj.html_url, "_blank")
          }
          if (state.downloadPdf && jj.pdf_url) {
            // Trigger PDF download
            const link = document.createElement("a")
            link.href = jj.pdf_url
            link.download = `report-${id}.pdf`
            link.click()
          }
          if (state.sendViaEmail && state.emailRecipients.length > 0) {
            // Send email with report
            try {
              await fetch(`/api/proxy/v1/reports/${id}/email`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({
                  recipients: state.emailRecipients.map((r) => r.email),
                }),
              })
            } catch (emailErr) {
              console.error("Failed to send email:", emailErr)
            }
          }
          return
        }

        if (jj.status === "failed" || tries > 90) {
          setGenerationState("failed")
          setError(jj.error || "Report generation failed")
          return
        }

        setTimeout(poll, 1000)
      }
      poll()
    } catch (e: any) {
      setError(e.message || "Unknown error")
      setGenerationState("failed")
    }
  }

  const goToReports = () => {
    router.push("/app/reports")
  }

  const resetAndTryAgain = () => {
    setGenerationState("idle")
    setCurrentStage(0)
    setError(null)
    setRun(null)
  }

  // Show loading/completion overlay when generating
  if (
    generationState === "generating" ||
    generationState === "completed" ||
    generationState === "failed"
  ) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/10 backdrop-blur-md">
        <div className="w-full max-w-lg mx-4">
          <div className="bg-card border border-border rounded-2xl shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="p-6 pb-4 border-b border-border">
              <div className="flex items-center gap-3">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    generationState === "completed"
                      ? "bg-green-500/10 text-green-500"
                      : generationState === "failed"
                      ? "bg-red-500/10 text-red-500"
                      : "bg-primary/10 text-primary"
                  }`}
                >
                  {generationState === "completed" ? (
                    <CheckCircle2 className="w-6 h-6" />
                  ) : generationState === "failed" ? (
                    <XCircle className="w-6 h-6" />
                  ) : (
                    <FileText className="w-6 h-6" />
                  )}
                </div>
                <div>
                  <h2 className="font-display font-semibold text-xl">
                    {generationState === "completed"
                      ? "Report Ready!"
                      : generationState === "failed"
                      ? "Generation Failed"
                      : "Generating Report"}
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    {generationState === "completed"
                      ? "Your market report has been generated successfully"
                      : generationState === "failed"
                      ? "Something went wrong while creating your report"
                      : `${areaDisplay || "Market"} ${
                          REPORT_TYPE_CONFIG[state.reportType]?.label || "Report"
                        }`}
                  </p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              {generationState === "generating" && (
                <div className="space-y-6">
                  {/* Animated Loader */}
                  <div className="flex justify-center py-8">
                    <div className="relative">
                      <div className="w-24 h-24 rounded-full border-4 border-primary/20" />
                      <div className="absolute inset-0 w-24 h-24 rounded-full border-4 border-transparent border-t-primary animate-spin" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <FileText className="w-8 h-8 text-primary animate-pulse" />
                      </div>
                    </div>
                  </div>

                  {/* Progress Stages */}
                  <div className="space-y-3">
                    {PROGRESS_STAGES.map((stage, index) => (
                      <div
                        key={stage.id}
                        className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-500 ${
                          index < currentStage
                            ? "bg-green-500/10 text-green-500"
                            : index === currentStage
                            ? "bg-primary/10 text-primary"
                            : "bg-muted/50 text-muted-foreground"
                        }`}
                      >
                        <div className="w-6 h-6 flex items-center justify-center">
                          {index < currentStage ? (
                            <CheckCircle2 className="w-5 h-5" />
                          ) : index === currentStage ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                          ) : (
                            <div className="w-2 h-2 rounded-full bg-current opacity-50" />
                          )}
                        </div>
                        <span className="text-sm font-medium">{stage.label}</span>
                      </div>
                    ))}
                  </div>

                  <p className="text-center text-xs text-muted-foreground">
                    This usually takes 15-30 seconds
                  </p>
                </div>
              )}

              {generationState === "completed" && run && (
                <div className="space-y-6">
                  {/* Success Animation */}
                  <div className="flex justify-center py-4">
                    <div className="relative">
                      <div className="w-20 h-20 rounded-full bg-green-500/10 flex items-center justify-center">
                        <CheckCircle2 className="w-10 h-10 text-green-500" />
                      </div>
                      <div className="absolute inset-0 w-20 h-20 rounded-full border-2 border-green-500/30 animate-ping" />
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="grid grid-cols-2 gap-3">
                    {run.pdf_url && (
                      <a
                        href={run.pdf_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-center gap-2 p-4 rounded-xl border-2 border-border hover:border-primary/50 hover:bg-primary/5 transition-all group"
                      >
                        <Download className="w-5 h-5 text-muted-foreground group-hover:text-primary" />
                        <span className="font-medium">Download PDF</span>
                      </a>
                    )}
                    {run.html_url && (
                      <a
                        href={run.html_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-center gap-2 p-4 rounded-xl border-2 border-border hover:border-primary/50 hover:bg-primary/5 transition-all group"
                      >
                        <Eye className="w-5 h-5 text-muted-foreground group-hover:text-primary" />
                        <span className="font-medium">Preview</span>
                      </a>
                    )}
                  </div>

                  {/* Go to Reports Button */}
                  <Button onClick={goToReports} className="w-full h-12 gap-2 text-base">
                    View All Reports
                    <ArrowRight className="w-4 h-4" />
                  </Button>

                  <button
                    onClick={resetAndTryAgain}
                    className="w-full text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Generate Another Report
                  </button>
                </div>
              )}

              {generationState === "failed" && (
                <div className="space-y-6">
                  {/* Error Display */}
                  <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                    <p className="text-sm text-red-400">{error || "An unexpected error occurred"}</p>
                  </div>

                  {/* Retry Actions */}
                  <div className="flex gap-3">
                    <Button variant="outline" onClick={goToReports} className="flex-1 h-11">
                      View Reports
                    </Button>
                    <Button onClick={resetAndTryAgain} className="flex-1 h-11">
                      Try Again
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link
            href="/app/reports"
            className="flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Reports
          </Link>
          <div className="flex items-center gap-3">
            <Button variant="ghost" onClick={() => router.push("/app/reports")}>
              Cancel
            </Button>
            <Button
              onClick={handleGenerate}
              disabled={!isValid}
              className="bg-violet-600 hover:bg-violet-700 text-white"
            >
              Generate Report
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid grid-cols-[1fr,420px] gap-8">
          {/* Left Panel - Configuration */}
          <div className="space-y-4">
            <Accordion
              type="multiple"
              value={openSections}
              onValueChange={setOpenSections}
              className="space-y-4"
            >
              {/* Section 1: Report Type */}
              <AccordionSection
                value="report-type"
                title="Report Type"
                status="complete"
                summary={
                  !openSections.includes("report-type") ? (
                    <span className="flex items-center gap-2 text-sm text-muted-foreground">
                      {(() => {
                        const Icon = REPORT_TYPE_CONFIG[state.reportType].icon
                        return <Icon className="h-4 w-4" />
                      })()}
                      {REPORT_TYPE_CONFIG[state.reportType].label} · Last {state.lookbackDays} days
                    </span>
                  ) : null
                }
              >
                <ReportTypeSection
                  reportType={state.reportType}
                  lookbackDays={state.lookbackDays}
                  onChange={updateState}
                />
              </AccordionSection>

              {/* Section 2: Area */}
              <AccordionSection
                value="area"
                title="Area"
                status={getAreaStatus()}
                summary={
                  !openSections.includes("area") && areaDisplay ? (
                    <span className="flex items-center gap-2 text-sm text-muted-foreground">
                      <MapPin className="h-4 w-4" />
                      {areaDisplay}
                    </span>
                  ) : null
                }
              >
                <AreaSection
                  areaType={state.areaType}
                  city={state.city}
                  zipCodes={state.zipCodes}
                  onChange={updateState}
                />
              </AccordionSection>

              {/* Section 3: Audience Filter (Conditional) */}
              {state.reportType === "new_listings_gallery" && (
                <AccordionSection
                  value="audience"
                  title="Audience Filter"
                  status={getAudienceStatus()}
                  summary={
                    !openSections.includes("audience") && audienceLabel ? (
                      <span className="flex items-center gap-2 text-sm text-muted-foreground">
                        🎯 {audienceLabel}
                      </span>
                    ) : null
                  }
                >
                  <AudienceSection audienceFilter={state.audienceFilter} onChange={updateState} />
                </AccordionSection>
              )}

              {/* Section 4: Delivery Options */}
              <AccordionSection
                value="delivery"
                title="Delivery Options"
                status={getDeliveryStatus()}
                summary={
                  !openSections.includes("delivery") ? (
                    <span className="flex items-center gap-2 text-sm text-muted-foreground">
                      {[
                        state.viewInBrowser && "🌐 Browser",
                        state.downloadPdf && "📄 PDF",
                        state.downloadSocialImage && "📱 Social",
                        state.sendViaEmail && "📧 Email",
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  ) : null
                }
              >
                <DeliverySection
                  viewInBrowser={state.viewInBrowser}
                  downloadPdf={state.downloadPdf}
                  downloadSocialImage={state.downloadSocialImage}
                  sendViaEmail={state.sendViaEmail}
                  emailRecipients={state.emailRecipients}
                  onChange={updateState}
                />
              </AccordionSection>
            </Accordion>
          </div>

          {/* Right Panel - Preview */}
          <div className="sticky top-24 h-fit">
            <ReportPreview state={state} branding={branding} profile={profile} />
          </div>
        </div>
      </main>
    </div>
  )
}

// Accordion Section Component
interface AccordionSectionProps {
  value: string
  title: string
  status: "complete" | "warning" | "optional"
  summary?: React.ReactNode
  children: React.ReactNode
}

function AccordionSection({
  value,
  title,
  status,
  summary,
  children,
}: AccordionSectionProps) {
  return (
    <AccordionItem value={value} className="rounded-xl border bg-card shadow-sm">
      <AccordionTrigger className="px-6 py-4 hover:no-underline [&[data-state=open]>div>svg]:rotate-180">
        <div className="flex flex-1 items-center gap-3">
          <StatusIndicator status={status} />
          <span className="font-medium">{title}</span>
          {summary && <div className="ml-auto mr-4">{summary}</div>}
        </div>
      </AccordionTrigger>
      <AccordionContent className="px-6 pb-6">{children}</AccordionContent>
    </AccordionItem>
  )
}

function StatusIndicator({
  status,
}: {
  status: "complete" | "warning" | "optional"
}) {
  if (status === "complete") {
    return (
      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-white">
        <Check className="h-3 w-3" />
      </div>
    )
  }
  if (status === "warning") {
    return (
      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500 text-white">
        <AlertCircle className="h-3 w-3" />
      </div>
    )
  }
  return <div className="h-5 w-5 rounded-full border-2 border-muted-foreground/30" />
}

// Re-export types for convenience
export type {
  ReportBuilderState,
  ReportApiPayload,
  BrandingContext,
  ProfileContext,
}

