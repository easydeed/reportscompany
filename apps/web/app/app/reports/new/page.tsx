"use client"

import dynamic from "next/dynamic"
import { useState } from "react"

const NewReportWizard = dynamic(() => import("@repo/ui").then((m) => m.NewReportWizard), { ssr: false })

export default function NewReportPage() {
  const [submitting, setSubmitting] = useState(false)
  const [run, setRun] = useState<any>(null)
  const [err, setErr] = useState<string | null>(null)

  async function onSubmit(payload: any) {
    setSubmitting(true)
    setErr(null)
    setRun(null)

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

        if (jj.status === "completed" || jj.status === "failed" || tries > 60) return

        setTimeout(poll, 800)
      }
      poll()
    } catch (e: any) {
      setErr(e.message || "Unknown error")
    } finally {
      setSubmitting(false)
    }
  }

  function onCancel() {
    window.history.back()
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">New Report</h1>
      
      <NewReportWizard onSubmit={onSubmit} onCancel={onCancel} />

      {submitting && <p className="text-sm text-amber-500">Creating report…</p>}
      
      {err && <p className="text-sm text-red-500">Error: {err}</p>}
      
      {run && (
        <div className="rounded border border-slate-700 bg-[#0F172A] p-4">
          <div className="text-sm">
            Status:{" "}
            <span className={run.status === "completed" ? "text-green-400" : "text-amber-400"}>
              {run.status}
            </span>
          </div>
          <div className="mt-2 flex gap-4">
            {run.html_url && (
              <a className="text-[#22D3EE] underline" target="_blank" rel="noopener noreferrer" href={run.html_url}>
                Open HTML
              </a>
            )}
            {run.pdf_url && (
              <a className="text-[#22D3EE] underline" target="_blank" rel="noopener noreferrer" href={run.pdf_url}>
                Open PDF
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
