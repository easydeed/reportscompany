"use client"

import { useState, useCallback } from "react"
import {
  Check,
  Loader2,
  Sparkles,
  ExternalLink,
  Download,
  RotateCcw,
  X,
  AlertCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import type { ReportBuilderState } from "./types"
import { getReportTypeInfo, AUDIENCE_FILTER_PRESETS } from "./types"

interface StepReviewProps {
  state: ReportBuilderState
  onChange: (patch: Partial<ReportBuilderState>) => void
  onReset: () => void
}

type GenPhase = "idle" | "generating" | "done" | "error"

export function StepReview({ state, onChange, onReset }: StepReviewProps) {
  const [phase, setPhase] = useState<GenPhase>("idle")
  const [progress, setProgress] = useState(0)
  const [emailInput, setEmailInput] = useState("")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [completedReport, setCompletedReport] = useState<{
    html_url?: string
    pdf_url?: string
  } | null>(null)

  const reportInfo = state.reportType
    ? getReportTypeInfo(state.reportType)
    : null
  const areaLabel =
    state.areaType === "city"
      ? state.city
      : state.zipCodes.join(", ")

  // Poll for report completion
  const pollReportStatus = async (reportId: string): Promise<Record<string, unknown>> => {
    const maxAttempts = 60
    const pollInterval = 2000

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

      await new Promise(resolve => setTimeout(resolve, pollInterval))
    }

    throw new Error("Report generation timed out")
  }

  const generate = useCallback(async () => {
    setPhase("generating")
    setProgress(0)
    setErrorMessage(null)

    // Start progress simulation
    let p = 0
    const iv = setInterval(() => {
      p += Math.random() * 8 + 2
      if (p >= 90) {
        p = 90 // Cap at 90 until real completion
        clearInterval(iv)
      }
      setProgress(Math.min(p, 90))
    }, 500)

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
      const report = await pollReportStatus(report_id)

      clearInterval(iv)
      setProgress(100)
      setCompletedReport(report as { html_url?: string; pdf_url?: string })

      setTimeout(() => setPhase("done"), 400)
    } catch (error) {
      clearInterval(iv)
      console.error("Generation error:", error)
      setErrorMessage(error instanceof Error ? error.message : "Failed to generate report")
      setPhase("error")
    }
  }, [state])

  function addEmail() {
    const trimmed = emailInput.trim()
    if (
      trimmed &&
      trimmed.includes("@") &&
      !state.recipientEmails.includes(trimmed)
    ) {
      onChange({ recipientEmails: [...state.recipientEmails, trimmed] })
      setEmailInput("")
    }
  }

  function removeEmail(email: string) {
    onChange({
      recipientEmails: state.recipientEmails.filter((e) => e !== email),
    })
  }

  // Error state
  if (phase === "error") {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-12 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-50">
          <AlertCircle className="h-8 w-8 text-red-500" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-foreground">Generation Failed</h2>
          <p className="mt-1 text-muted-foreground">{errorMessage}</p>
        </div>
        <Button
          onClick={() => { setPhase("idle"); setProgress(0) }}
          variant="outline"
        >
          Try Again
        </Button>
      </div>
    )
  }

  // Done state
  if (phase === "done") {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-12 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#EEF2FF]">
          <Check className="h-8 w-8 text-[#6366F1]" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-foreground">Report Ready!</h2>
          <p className="mt-1 text-muted-foreground">
            Your {reportInfo?.name} for {areaLabel} has been generated.
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-3">
          {state.viewInBrowser && completedReport?.html_url && (
            <Button
              className="bg-[#6366F1] text-white hover:bg-[#4338CA]"
              onClick={() => window.open(completedReport.html_url, "_blank")}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Open Report
            </Button>
          )}
          {state.downloadPdf && completedReport?.pdf_url && (
            <Button
              variant="outline"
              onClick={() => window.open(completedReport.pdf_url, "_blank")}
            >
              <Download className="mr-2 h-4 w-4" />
              Download PDF
            </Button>
          )}
        </div>
        <button
          type="button"
          onClick={onReset}
          className="mt-2 flex items-center gap-1.5 text-sm font-medium text-[#6366F1] hover:text-[#4338CA]"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Create Another Report
        </button>
      </div>
    )
  }

  // Generating state
  if (phase === "generating") {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-12 text-center">
        <Loader2 className="h-10 w-10 animate-spin text-[#6366F1]" />
        <div>
          <h2 className="text-xl font-bold text-foreground">Generating Report...</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            This usually takes 10-30 seconds
          </p>
        </div>
        <div className="w-full max-w-xs">
          <Progress value={progress} className="h-2" />
          <p className="mt-2 text-xs text-muted-foreground">
            {progress < 30
              ? "Fetching MLS data..."
              : progress < 70
                ? "Processing..."
                : "Finalizing report..."}
          </p>
        </div>
      </div>
    )
  }

  // Idle / form state
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Review & Generate</h2>
        <p className="mt-1 text-muted-foreground">
          Confirm your selections and choose delivery options.
        </p>
      </div>

      {/* Summary card */}
      <div className="flex items-center gap-4 rounded-xl border border-border bg-muted/50 p-5">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-[#EEF2FF]">
          <Sparkles className="h-5 w-5 text-[#6366F1]" />
        </div>
        <div>
          <p className="font-semibold text-foreground">
            {reportInfo?.name || "Report"}
          </p>
          <p className="text-sm text-muted-foreground">
            {areaLabel} &middot; Last {state.lookbackDays} days
            {state.audienceFilterName && state.audienceFilterName !== "All Listings"
              ? ` \u00b7 ${state.audienceFilterName}`
              : ""}
          </p>
        </div>
      </div>

      {/* Delivery options */}
      <div className="space-y-4">
        <p className="text-sm font-semibold text-foreground">Delivery Options</p>
        <div className="space-y-3">
          {[
            { key: "viewInBrowser" as const, label: "View in Browser" },
            { key: "downloadPdf" as const, label: "Download PDF" },
            { key: "downloadSocialImage" as const, label: "Download Social Image (1080\u00d71920)" },
            { key: "sendViaEmail" as const, label: "Send via Email" },
          ].map((opt) => (
            <label key={opt.key} className="flex items-center gap-3 cursor-pointer">
              <Checkbox
                checked={state[opt.key]}
                onCheckedChange={(v) => onChange({ [opt.key]: !!v })}
              />
              <span className="text-sm text-foreground">{opt.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Recipient emails */}
      {state.sendViaEmail && (
        <div className="space-y-3">
          <p className="text-sm font-semibold text-foreground">Recipients</p>
          <div className="flex items-center gap-2">
            <Input
              placeholder="Search contacts or enter email..."
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault()
                  addEmail()
                }
              }}
            />
          </div>
          {state.recipientEmails.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {state.recipientEmails.map((email) => (
                <span
                  key={email}
                  className="inline-flex items-center gap-1.5 rounded-full bg-[#EEF2FF] px-3 py-1 text-sm font-medium text-[#4338CA]"
                >
                  {email}
                  <button
                    type="button"
                    onClick={() => removeEmail(email)}
                    className="rounded-full p-0.5 hover:bg-[#C7D2FE]"
                    aria-label={`Remove ${email}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Generate button */}
      <Button
        onClick={generate}
        size="lg"
        className="w-full bg-[#6366F1] py-6 text-base font-semibold text-white hover:bg-[#4338CA]"
      >
        <Sparkles className="mr-2 h-5 w-5" />
        Generate Report
      </Button>
    </div>
  )
}
