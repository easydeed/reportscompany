"use client"

import { useState } from "react"
import dynamic from "next/dynamic"

const ScheduleWizard = dynamic(() => import("@repo/ui").then((m) => m.ScheduleWizard), { ssr: false })

export default function NewSchedulePage() {
  const [err, setErr] = useState<string | null>(null)

  async function onSubmit(payload: any) {
    setErr(null)

    try {
      const res = await fetch(`/api/proxy/v1/schedules`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const text = await res.text().catch(() => "")
        setErr(text || "Create failed")
        return
      }

      window.location.href = "/app/schedules"
    } catch (error: any) {
      setErr(error.message || "Unknown error")
    }
  }

  function onCancel() {
    window.history.back()
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">New Schedule</h1>
      <ScheduleWizard onSubmit={onSubmit} onCancel={onCancel} />
      {err && <p className="text-sm text-red-400">{err}</p>}
    </div>
  )
}

