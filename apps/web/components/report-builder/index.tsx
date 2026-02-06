"use client"

import { useState, useEffect } from "react"
import { ArrowLeft, Loader2, Sparkles } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ReportTypeSection } from "./sections/report-type-section"
import { AreaSection } from "./sections/area-section"
import { LookbackSection } from "./sections/lookback-section"
import { DeliverySection } from "./sections/delivery-section"
import { ReportPreview } from "./report-preview"
import type { 
  ReportBuilderState, 
  BrandingContext, 
  ProfileContext,
  AudienceFilter 
} from "./types"
import { AUDIENCE_FILTER_PRESETS } from "./types"

const DEFAULT_STATE: ReportBuilderState = {
  reportType: null,
  lookbackDays: null,
  areaType: "city",
  city: null,
  zipCodes: [],
  audienceFilter: null,
  audienceFilterName: null,
  viewInBrowser: false,
  downloadPdf: false,
  downloadSocialImage: false,
  sendViaEmail: false,
  emailRecipients: [],
}

const DEFAULT_BRANDING: BrandingContext = {
  primaryColor: "#4F46E5",
  accentColor: "#818CF8",
  pdfHeaderLogoUrl: null,
  displayName: "TrendyReports",
}

const DEFAULT_PROFILE: ProfileContext = {
  name: "Agent Name",
  jobTitle: "Real Estate Agent",
  avatarUrl: null,
  phone: "(555) 123-4567",
  email: "agent@example.com",
}

export function ReportBuilder() {
  const [state, setState] = useState<ReportBuilderState>(DEFAULT_STATE)
  const [branding, setBranding] = useState<BrandingContext>(DEFAULT_BRANDING)
  const [profile, setProfile] = useState<ProfileContext>(DEFAULT_PROFILE)
  const [isGenerating, setIsGenerating] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  
  // Track which sections user has interacted with
  const [touched, setTouched] = useState({
    reportType: false,
    area: false,
    lookback: false,
    delivery: false,
  })

  // Scroll shadow detection
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    window.addEventListener("scroll", onScroll)
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  // Fetch branding and profile on mount
  useEffect(() => {
    async function loadContext() {
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
            pdfHeaderLogoUrl: data.pdf_header_logo_url || null,
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
      } catch (error) {
        console.error("Failed to load context:", error)
      }
    }
    loadContext()
  }, [])

  const updateState = (updates: Partial<ReportBuilderState>) => {
    setState((prev) => ({ ...prev, ...updates }))
    
    // Mark sections as touched based on what was updated
    if ('reportType' in updates || 'audienceFilter' in updates) {
      setTouched(prev => ({ ...prev, reportType: true }))
    }
    if ('city' in updates || 'zipCodes' in updates || 'areaType' in updates) {
      setTouched(prev => ({ ...prev, area: true }))
    }
    if ('lookbackDays' in updates) {
      setTouched(prev => ({ ...prev, lookback: true }))
    }
    if ('viewInBrowser' in updates || 'downloadPdf' in updates || 
        'downloadSocialImage' in updates || 'sendViaEmail' in updates ||
        'emailRecipients' in updates) {
      setTouched(prev => ({ ...prev, delivery: true }))
    }
  }

  // Handle audience filter change
  const handleAudienceChange = (filter: AudienceFilter, name: string | null) => {
    updateState({ audienceFilter: filter, audienceFilterName: name })
  }

  // Check section completion - only show complete if touched AND filled
  const isReportTypeComplete = touched.reportType && !!state.reportType
  const isAreaComplete = touched.area && (state.areaType === "city" ? !!state.city : state.zipCodes.length > 0)
  const isLookbackComplete = touched.lookback && !!state.lookbackDays
  const hasDeliveryOption = touched.delivery && (state.viewInBrowser || state.downloadPdf || state.downloadSocialImage || state.sendViaEmail)

  // Can generate only requires actual data, not touched state
  const canGenerate = !!state.reportType && 
    (state.areaType === "city" ? !!state.city : state.zipCodes.length > 0) && 
    !!state.lookbackDays && 
    (state.viewInBrowser || state.downloadPdf || state.downloadSocialImage || state.sendViaEmail)

  // Progress counter for header
  const completedCount = [isReportTypeComplete, isAreaComplete, isLookbackComplete, hasDeliveryOption].filter(Boolean).length
  const totalSections = 4

  // Poll for report completion
  const pollReportStatus = async (reportId: string): Promise<any> => {
    const maxAttempts = 60 // 2 minutes max
    const pollInterval = 2000 // 2 seconds
    
    for (let i = 0; i < maxAttempts; i++) {
      const res = await fetch(`/api/proxy/v1/reports/${reportId}`)
      if (!res.ok) throw new Error("Failed to check report status")
      
      const report = await res.json()
      
      if (report.status === "ready" || report.status === "completed") {
        return report
      }
      
      if (report.status === "failed") {
        throw new Error(report.error_message || "Report generation failed")
      }
      
      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, pollInterval))
    }
    
    throw new Error("Report generation timed out")
  }

  // Handle generate
  const handleGenerate = async () => {
    if (!canGenerate) return
    setIsGenerating(true)

    try {
      // Build API payload
      const filters = state.audienceFilter && state.audienceFilter !== "all" 
        ? AUDIENCE_FILTER_PRESETS[state.audienceFilter] 
        : null

      const payload = {
        report_type: state.reportType,
        city: state.areaType === "city" ? state.city : null,
        zips: state.areaType === "zip" ? state.zipCodes : null,
        lookback_days: state.lookbackDays,
        filters,
      }

      // Step 1: Create report request
      const res = await fetch("/api/proxy/v1/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail?.message || errorData.detail || "Failed to create report")
      }
      
      const { report_id } = await res.json()
      
      // Step 2: Poll for completion
      const completedReport = await pollReportStatus(report_id)
      
      // Step 3: Handle delivery based on options
      if (state.viewInBrowser && completedReport.html_url) {
        window.open(completedReport.html_url, "_blank")
      }
      if (state.downloadPdf && completedReport.pdf_url) {
        window.open(completedReport.pdf_url, "_blank")
      }
      
      // Success - could show a toast or navigate to reports list
      console.log("Report generated successfully:", completedReport)
      
    } catch (error) {
      console.error("Generation error:", error)
      alert(error instanceof Error ? error.message : "Failed to generate report")
    } finally {
      setIsGenerating(false)
    }
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
              href="/app/reports"
              className="flex items-center justify-center w-8 h-8 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-sm font-semibold text-gray-900">New Market Report</h1>
              <p className="text-xs text-gray-500">
                {completedCount} of {totalSections} sections complete
              </p>
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/app/reports">Cancel</Link>
            </Button>
            <Button
              onClick={handleGenerate}
              disabled={!canGenerate || isGenerating}
              size="sm"
              className={cn(
                "transition-all duration-300",
                canGenerate && !isGenerating && [
                  "shadow-md shadow-primary/20",
                  "hover:shadow-lg hover:shadow-primary/30",
                  "hover:-translate-y-0.5",
                ]
              )}
            >
              {isGenerating ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Generating...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5" />
                  Generate Report
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
              {/* Report Type Section */}
              <ReportTypeSection
                reportType={state.reportType}
                audienceFilter={state.audienceFilter}
                audienceFilterName={state.audienceFilterName}
                onChange={updateState}
                onAudienceChange={handleAudienceChange}
                isComplete={isReportTypeComplete}
                stepNumber={1}
              />

              {/* Area Section */}
              <AreaSection
                areaType={state.areaType}
                city={state.city}
                zipCodes={state.zipCodes}
                onChange={updateState}
                isComplete={isAreaComplete}
                stepNumber={2}
              />

              {/* Lookback Section */}
              <LookbackSection
                lookbackDays={state.lookbackDays}
                onChange={updateState}
                isComplete={isLookbackComplete}
                stepNumber={3}
              />

              {/* Delivery Section */}
              <DeliverySection
                viewInBrowser={state.viewInBrowser}
                downloadPdf={state.downloadPdf}
                downloadSocialImage={state.downloadSocialImage}
                sendViaEmail={state.sendViaEmail}
                emailRecipients={state.emailRecipients}
                onChange={updateState}
                hasOption={hasDeliveryOption}
                stepNumber={4}
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
                    Live Preview
                  </h3>
                </div>
                <span className="text-xs text-gray-400">Updates as you build</span>
              </div>

              {/* Preview content */}
              <div className="p-4">
                <ReportPreview 
                  state={state} 
                  branding={branding} 
                  profile={profile} 
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
