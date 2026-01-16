"use client"

import { useState, useMemo } from "react"
import { ChevronLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ConfigurationPanel } from "@/components/schedule-builder/configuration-panel"
import { EmailPreviewPanel } from "@/components/schedule-builder/email-preview-panel"
import type { ScheduleBuilderState } from "@/lib/schedule-types"

const defaultState: ScheduleBuilderState = {
  name: "",
  reportType: "market_snapshot",
  lookbackDays: 30,
  areaType: "city",
  city: null,
  zipCodes: [],
  audienceFilter: null,
  audienceFilterName: null,
  cadence: "weekly",
  weeklyDow: 1,
  monthlyDom: 1,
  sendHour: 9,
  sendMinute: 0,
  timezone: "America/Los_Angeles",
  recipients: [],
  includeAttachment: false,
}

const branding = {
  primaryColor: "#6366f1",
  accentColor: "#8b5cf6",
  emailLogoUrl: null,
}

const profile = {
  name: "Jerry Mendoza",
  jobTitle: "Real Estate Agent",
  avatarUrl: null,
  phone: "(626) 555-1234",
  email: "jerry@example.com",
}

export function ScheduleBuilder() {
  const [state, setState] = useState<ScheduleBuilderState>(defaultState)

  const updateState = <K extends keyof ScheduleBuilderState>(key: K, value: ScheduleBuilderState[K]) => {
    setState((prev) => ({ ...prev, [key]: value }))
  }

  const isValid = useMemo(() => {
    return state.name.trim() !== "" && (state.city !== null || state.zipCodes.length > 0) && state.recipients.length > 0
  }, [state.name, state.city, state.zipCodes, state.recipients])

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-background">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <button className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ChevronLeft className="h-4 w-4" />
            Back to Schedules
          </button>
          <div className="flex items-center gap-3">
            <Button variant="ghost">Cancel</Button>
            <Button disabled={!isValid}>Save Schedule</Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid grid-cols-[1fr,420px] gap-8">
          <ConfigurationPanel state={state} updateState={updateState} />
          <EmailPreviewPanel state={state} branding={branding} profile={profile} />
        </div>
      </main>
    </div>
  )
}
