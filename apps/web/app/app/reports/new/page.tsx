"use client"

import dynamic from "next/dynamic"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { FileText, Loader2, CheckCircle2, XCircle, ArrowRight, Download, Eye } from "lucide-react"
import { Button } from "@repo/ui/components/ui/button"

const NewReportWizard = dynamic(() => import("@repo/ui").then((m) => m.NewReportWizard), { ssr: false })

// Progress stages for the loading animation
const PROGRESS_STAGES = [
  { id: "queued", label: "Queuing report...", duration: 2000 },
  { id: "fetching", label: "Fetching MLS data...", duration: 5000 },
  { id: "processing", label: "Processing listings...", duration: 3000 },
  { id: "generating", label: "Generating PDF...", duration: 4000 },
  { id: "uploading", label: "Uploading to cloud...", duration: 2000 },
]

type GenerationState = "idle" | "generating" | "completed" | "failed"

export default function NewReportPage() {
  const router = useRouter()
  const [generationState, setGenerationState] = useState<GenerationState>("idle")
  const [currentStage, setCurrentStage] = useState(0)
  const [run, setRun] = useState<any>(null)
  const [err, setErr] = useState<string | null>(null)
  const [reportPayload, setReportPayload] = useState<any>(null)

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

  async function onSubmit(payload: any) {
    setGenerationState("generating")
    setCurrentStage(0)
    setErr(null)
    setRun(null)
    setReportPayload(payload)

    try {
      const res = await fetch(`/api/proxy/v1/reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      const j = await res.json()
      if (!res.ok) throw new Error(j?.detail || "Create failed")

      const id = j.report_id

      // Poll for completion
      let tries = 0
      const poll = async () => {
        tries++
        const r = await fetch(`/api/proxy/v1/reports/${id}`)
        const jj = await r.json()
        setRun(jj)

        if (jj.status === "completed") {
          setGenerationState("completed")
          return
        }
        
        if (jj.status === "failed" || tries > 90) {
          setGenerationState("failed")
          setErr(jj.error || "Report generation failed")
          return
        }

        setTimeout(poll, 1000)
      }
      poll()
    } catch (e: any) {
      setErr(e.message || "Unknown error")
      setGenerationState("failed")
    }
  }

  function onCancel() {
    window.history.back()
  }

  function goToReports() {
    router.push("/app/reports")
  }

  function resetAndTryAgain() {
    setGenerationState("idle")
    setCurrentStage(0)
    setErr(null)
    setRun(null)
  }

  // Show loading overlay when generating
  if (generationState === "generating" || generationState === "completed" || generationState === "failed") {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/10 backdrop-blur-md">
        <div className="w-full max-w-lg mx-4">
          <div className="bg-card border border-border rounded-2xl shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="p-6 pb-4 border-b border-border">
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  generationState === "completed" 
                    ? "bg-green-500/10 text-green-500" 
                    : generationState === "failed"
                    ? "bg-red-500/10 text-red-500"
                    : "bg-primary/10 text-primary"
                }`}>
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
                      : `${reportPayload?.city || "Market"} ${reportPayload?.report_type?.replace(/_/g, " ") || "Report"}`}
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
                      {/* Outer ring */}
                      <div className="w-24 h-24 rounded-full border-4 border-primary/20" />
                      {/* Spinning ring */}
                      <div className="absolute inset-0 w-24 h-24 rounded-full border-4 border-transparent border-t-primary animate-spin" />
                      {/* Inner icon */}
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
                      {/* Celebration rings */}
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
                    <p className="text-sm text-red-400">{err || "An unexpected error occurred"}</p>
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
    <div className="space-y-6">
      <NewReportWizard onSubmit={onSubmit} onCancel={onCancel} />
    </div>
  )
}
