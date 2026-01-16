"use client"

import { useState, useCallback, useEffect, useRef } from "react"
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
  ChevronDown,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
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
        <div className="flex h-16 items-center justify-between px-8">
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
      <main className="px-8 py-8">
        <div className="grid grid-cols-[1fr_480px] gap-8">
          {/* Left Panel - Configuration */}
          <div className="space-y-4">
            {/* Section 1: Report Type */}
            <WizardSection
              stepNumber={1}
              title="Report Type"
              subtitle="Choose the type of market report you want to generate"
              status="complete"
              isOpen={openSections.includes("report-type")}
              onToggle={() => {
                setOpenSections(prev => 
                  prev.includes("report-type") 
                    ? prev.filter(s => s !== "report-type")
                    : [...prev, "report-type"]
                )
              }}
              summary={
                <>
                  {(() => {
                    const Icon = REPORT_TYPE_CONFIG[state.reportType].icon
                    return <Icon className="h-4 w-4" />
                  })()}
                  <span>{REPORT_TYPE_CONFIG[state.reportType].label}</span>
                  <span className="text-muted-foreground">·</span>
                  <span className="text-muted-foreground">{state.lookbackDays} days</span>
                </>
              }
            >
              <ReportTypeSection
                reportType={state.reportType}
                lookbackDays={state.lookbackDays}
                onChange={(updates) => {
                  updateState(updates)
                  // Auto-advance to next section after a brief delay
                  setTimeout(() => {
                    if (!openSections.includes("area")) {
                      setOpenSections(prev => [...prev.filter(s => s !== "report-type"), "area"])
                    }
                  }, 300)
                }}
              />
            </WizardSection>

            {/* Section 2: Area */}
            <WizardSection
              stepNumber={2}
              title="Area"
              subtitle="Define the geographic region for your report"
              status={getAreaStatus()}
              isOpen={openSections.includes("area")}
              onToggle={() => {
                setOpenSections(prev => 
                  prev.includes("area") 
                    ? prev.filter(s => s !== "area")
                    : [...prev, "area"]
                )
              }}
              summary={
                areaDisplay ? (
                  <>
                    <MapPin className="h-4 w-4" />
                    <span>{areaDisplay}</span>
                  </>
                ) : null
              }
            >
              <AreaSection
                areaType={state.areaType}
                city={state.city}
                zipCodes={state.zipCodes}
                onChange={(updates) => {
                  updateState(updates)
                  // Auto-advance when city is selected or first ZIP added
                  const willBeValid = updates.city || (updates.zipCodes && updates.zipCodes.length > 0)
                  if (willBeValid) {
                    setTimeout(() => {
                      const nextSection = state.reportType === "new_listings_gallery" ? "audience" : "delivery"
                      if (!openSections.includes(nextSection)) {
                        setOpenSections(prev => [...prev.filter(s => s !== "area"), nextSection])
                      }
                    }, 300)
                  }
                }}
              />
            </WizardSection>

            {/* Section 3: Audience Filter (Conditional) */}
            {state.reportType === "new_listings_gallery" && (
              <WizardSection
                stepNumber={3}
                title="Audience Filter"
                subtitle="Target specific buyer segments for your listings"
                status={getAudienceStatus()}
                isOpen={openSections.includes("audience")}
                onToggle={() => {
                  setOpenSections(prev => 
                    prev.includes("audience") 
                      ? prev.filter(s => s !== "audience")
                      : [...prev, "audience"]
                  )
                }}
                summary={
                  audienceLabel ? (
                    <>
                      <span className="text-lg">🎯</span>
                      <span>{audienceLabel}</span>
                    </>
                  ) : null
                }
              >
                <AudienceSection 
                  audienceFilter={state.audienceFilter} 
                  onChange={(updates) => {
                    updateState(updates)
                    // Auto-advance to delivery
                    if (updates.audienceFilter) {
                      setTimeout(() => {
                        if (!openSections.includes("delivery")) {
                          setOpenSections(prev => [...prev.filter(s => s !== "audience"), "delivery"])
                        }
                      }, 300)
                    }
                  }} 
                />
              </WizardSection>
            )}

            {/* Section 4: Delivery Options */}
            <WizardSection
              stepNumber={state.reportType === "new_listings_gallery" ? 4 : 3}
              title="Delivery Options"
              subtitle="How would you like to receive your report?"
              status={getDeliveryStatus()}
              isOpen={openSections.includes("delivery")}
              onToggle={() => {
                setOpenSections(prev => 
                  prev.includes("delivery") 
                    ? prev.filter(s => s !== "delivery")
                    : [...prev, "delivery"]
                )
              }}
              summary={
                <>
                  {state.viewInBrowser && <span>🌐 Browser</span>}
                  {state.downloadPdf && <span>📄 PDF</span>}
                  {state.downloadSocialImage && <span>📱 Social</span>}
                  {state.sendViaEmail && <span>📧 Email</span>}
                </>
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
            </WizardSection>
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

// Enhanced Wizard Section Component
interface WizardSectionProps {
  stepNumber: number
  title: string
  subtitle: string
  status: "complete" | "warning" | "optional"
  isOpen: boolean
  onToggle: () => void
  summary?: React.ReactNode
  children: React.ReactNode
}

function WizardSection({
  stepNumber,
  title,
  subtitle,
  status,
  isOpen,
  onToggle,
  summary,
  children,
}: WizardSectionProps) {
  const contentRef = useRef<HTMLDivElement>(null)
  const [contentHeight, setContentHeight] = useState(0)

  useEffect(() => {
    if (contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight)
    }
  }, [children, isOpen])

  return (
    <div 
      className={cn(
        "rounded-2xl border-2 bg-card shadow-sm transition-all duration-300",
        isOpen ? "border-violet-200 shadow-md" : "border-border hover:border-violet-100",
        status === "complete" && !isOpen && "border-emerald-100 bg-emerald-50/30"
      )}
    >
      {/* Header */}
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-4 p-5 text-left"
      >
        {/* Step Number / Status */}
        <div className="relative">
          <StepIndicator stepNumber={stepNumber} status={status} isOpen={isOpen} />
        </div>

        {/* Title & Summary */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
            {!isOpen && status === "complete" && summary && (
              <div className="flex items-center gap-2 text-sm text-emerald-700 font-medium animate-in fade-in slide-in-from-left-2 duration-300">
                {summary}
              </div>
            )}
          </div>
          {isOpen && (
            <p className="mt-0.5 text-sm text-muted-foreground animate-in fade-in duration-200">
              {subtitle}
            </p>
          )}
        </div>

        {/* Chevron */}
        <ChevronDown 
          className={cn(
            "h-5 w-5 text-muted-foreground transition-transform duration-300",
            isOpen && "rotate-180"
          )} 
        />
      </button>

      {/* Content */}
      <div 
        className="overflow-hidden transition-all duration-300 ease-out"
        style={{ height: isOpen ? contentHeight : 0 }}
      >
        <div ref={contentRef} className="px-5 pb-6 pt-2">
          <div className="ml-12">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

function StepIndicator({
  stepNumber,
  status,
  isOpen,
}: {
  stepNumber: number
  status: "complete" | "warning" | "optional"
  isOpen: boolean
}) {
  if (status === "complete" && !isOpen) {
    return (
      <div className="relative flex h-8 w-8 items-center justify-center">
        {/* Animated ring */}
        <div className="absolute inset-0 rounded-full bg-emerald-500/20 animate-ping" style={{ animationDuration: '1.5s', animationIterationCount: '1' }} />
        {/* Check circle */}
        <div className="relative flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 animate-in zoom-in duration-300">
          <Check className="h-4 w-4" strokeWidth={3} />
        </div>
      </div>
    )
  }

  if (status === "warning") {
    return (
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-500 text-white shadow-lg shadow-amber-500/30">
        <AlertCircle className="h-4 w-4" />
      </div>
    )
  }

  // Default: Show step number
  return (
    <div 
      className={cn(
        "flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold transition-all duration-300",
        isOpen 
          ? "bg-violet-600 text-white shadow-lg shadow-violet-600/30" 
          : "bg-muted text-muted-foreground"
      )}
    >
      {stepNumber}
    </div>
  )
}

// Re-export types for convenience
export type {
  ReportBuilderState,
  ReportApiPayload,
  BrandingContext,
  ProfileContext,
}

