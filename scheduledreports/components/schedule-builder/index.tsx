"use client"

import { useState, useCallback } from "react"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ConfigurationPanel } from "./configuration-panel"
import { PreviewPanel } from "./preview-panel"
import type { ScheduleBuilderState } from "./types"

const initialState: ScheduleBuilderState = {
  name: "",
  reportType: "market_update",
  lookbackDays: 30,
  areaType: "city",
  city: null,
  zipCodes: [],
  audienceFilter: null,
  cadence: "weekly",
  weeklyDow: 1,
  monthlyDom: 1,
  sendHour: 9,
  sendMinute: 0,
  timezone: "America/Los_Angeles",
  recipients: [],
  includeAttachment: false,
}

export function ScheduleBuilder() {
  const [state, setState] = useState<ScheduleBuilderState>(initialState)
  const [expandedSection, setExpandedSection] = useState<string>("name")

  const updateState = useCallback((updates: Partial<ScheduleBuilderState>) => {
    setState((prev) => ({ ...prev, ...updates }))
  }, [])

  const isValid =
    state.name.trim().length > 0 &&
    (state.areaType === "city" ? state.city !== null : state.zipCodes.length > 0) &&
    state.recipients.length > 0

  const handleSave = () => {
    console.log("Saving schedule:", state)
  }

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-background">
        <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between px-6">
          <button className="flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground">
            <ArrowLeft className="h-4 w-4" />
            Back to Schedules
          </button>
          <div className="flex items-center gap-3">
            <Button variant="ghost">Cancel</Button>
            <Button onClick={handleSave} disabled={!isValid} className="bg-violet-600 hover:bg-violet-700 text-white">
              Save Schedule
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-[1400px] px-6 py-8">
        <div className="grid grid-cols-[1fr,400px] gap-8">
          <ConfigurationPanel
            state={state}
            updateState={updateState}
            expandedSection={expandedSection}
            setExpandedSection={setExpandedSection}
          />
          <PreviewPanel state={state} />
        </div>
      </main>
    </div>
  )
}
