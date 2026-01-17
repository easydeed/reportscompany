"use client"

import { useState, useEffect } from "react"
import { ArrowLeft, Loader2 } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
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
  reportType: "market_snapshot",
  lookbackDays: 30,
  areaType: "city",
  city: null,
  zipCodes: [],
  audienceFilter: null,
  audienceFilterName: null,
  viewInBrowser: true,
  downloadPdf: false,
  downloadSocialImage: false,
  sendViaEmail: false,
  emailRecipients: [],
}

const DEFAULT_BRANDING: BrandingContext = {
  primaryColor: "#7C3AED",
  accentColor: "#8B5CF6",
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
  }

  // Handle audience filter change
  const handleAudienceChange = (filter: AudienceFilter, name: string | null) => {
    updateState({ audienceFilter: filter, audienceFilterName: name })
  }

  // Check section completion
  const isReportTypeComplete = !!state.reportType
  const isAreaComplete = state.areaType === "city" ? !!state.city : state.zipCodes.length > 0
  const isLookbackComplete = !!state.lookbackDays
  const hasDeliveryOption = state.viewInBrowser || state.downloadPdf || state.downloadSocialImage || state.sendViaEmail

  const canGenerate = isReportTypeComplete && isAreaComplete && isLookbackComplete && hasDeliveryOption

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
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white border-b border-gray-200 px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link 
              href="/app/reports" 
              className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Reports
            </Link>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/app/reports">
              <Button variant="outline" className="bg-white border-gray-200 text-gray-700 hover:bg-gray-50">
                Cancel
              </Button>
            </Link>
            <Button 
              onClick={handleGenerate}
              disabled={!canGenerate || isGenerating}
              className="bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-50"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                "Generate Report"
              )}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content - 400px config / flexible preview */}
      <main className="px-8 py-6">
        <div className="grid grid-cols-[400px_1fr] gap-8">
          {/* Left: Config Panel (fixed 400px) */}
          <div className="space-y-4">
            {/* Report Type Section */}
            <ReportTypeSection
              reportType={state.reportType}
              audienceFilter={state.audienceFilter}
              audienceFilterName={state.audienceFilterName}
              onChange={updateState}
              onAudienceChange={handleAudienceChange}
              isComplete={isReportTypeComplete}
            />

            {/* Area Section */}
            <AreaSection
              areaType={state.areaType}
              city={state.city}
              zipCodes={state.zipCodes}
              onChange={updateState}
              isComplete={isAreaComplete}
            />

            {/* Lookback Section */}
            <LookbackSection
              lookbackDays={state.lookbackDays}
              onChange={updateState}
              isComplete={isLookbackComplete}
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
            />
          </div>

          {/* Right: Preview Panel (flexible, takes remaining space) */}
          <div className="sticky top-24">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-900">Preview</h3>
                <span className="text-xs text-gray-400">Updates as you build</span>
              </div>
              <ReportPreview 
                state={state} 
                branding={branding} 
                profile={profile} 
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
