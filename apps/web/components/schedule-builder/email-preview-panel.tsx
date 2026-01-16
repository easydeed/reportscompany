"use client"

import { Button } from "@/components/ui/button"
import { Mail, Users, Clock, Send } from "lucide-react"
import {
  type ScheduleBuilderState,
  type BrandingContext,
  type ProfileContext,
  getEmailSubject,
  getAreaDisplay,
  DAY_NAMES,
} from "./types"
import { EmailPreview } from "./email-preview"

interface EmailPreviewPanelProps {
  state: ScheduleBuilderState
  branding: BrandingContext
  profile: ProfileContext
  onSendTest?: () => void
  sendingTest?: boolean
}

export function EmailPreviewPanel({ 
  state, 
  branding, 
  profile, 
  onSendTest,
  sendingTest 
}: EmailPreviewPanelProps) {
  const subject = getEmailSubject(state)
  const area = getAreaDisplay(state)

  const getNextRunDate = () => {
    const now = new Date()

    if (state.cadence === "weekly") {
      const daysUntil = (state.weeklyDow - now.getDay() + 7) % 7 || 7
      const nextDate = new Date(now)
      nextDate.setDate(now.getDate() + daysUntil)
      const hourDisplay = state.sendHour > 12 ? state.sendHour - 12 : state.sendHour || 12
      const ampm = state.sendHour >= 12 ? "PM" : "AM"
      return `${DAY_NAMES[state.weeklyDow]}, ${nextDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })} at ${hourDisplay}:${state.sendMinute.toString().padStart(2, "0")} ${ampm}`
    } else {
      const nextDate = new Date(now.getFullYear(), now.getMonth(), state.monthlyDom)
      if (nextDate <= now) {
        nextDate.setMonth(nextDate.getMonth() + 1)
      }
      const hourDisplay = state.sendHour > 12 ? state.sendHour - 12 : state.sendHour || 12
      const ampm = state.sendHour >= 12 ? "PM" : "AM"
      return `${nextDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })} at ${hourDisplay}:${state.sendMinute.toString().padStart(2, "0")} ${ampm}`
    }
  }

  const getTotalRecipients = () => {
    let total = 0
    state.recipients.forEach((r) => {
      if (r.type === "group") {
        total += r.memberCount
      } else {
        total += 1
      }
    })
    return total
  }

  return (
    <div className="sticky top-24">
      {/* Hero Preview Container */}
      <div className="rounded-2xl border-2 border-muted bg-gradient-to-br from-slate-50 to-slate-100 p-6 shadow-xl dark:from-slate-900 dark:to-slate-800">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Live Email Preview</h3>
          <span className="flex items-center gap-1.5 rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
            Updates live
          </span>
        </div>

        {/* Subject Line Preview */}
        <div className="mb-4 rounded-lg bg-white/80 p-3 dark:bg-black/20">
          <div className="text-xs font-medium text-muted-foreground mb-1">Subject Line</div>
          <div className="font-medium truncate">{subject}</div>
        </div>

        {/* Email Preview */}
        <div className="overflow-hidden rounded-xl bg-stone-100 shadow-2xl ring-1 ring-black/5 dark:bg-stone-900">
          <div className="max-h-[calc(100vh-480px)] overflow-y-auto">
            <EmailPreview state={state} branding={branding} profile={profile} area={area} />
          </div>
        </div>

        {/* Schedule Info Cards */}
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-white/60 p-3 dark:bg-black/20">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Clock className="h-3.5 w-3.5" />
              <span className="text-xs font-medium">Next Send</span>
            </div>
            <div className="text-sm font-semibold truncate">{getNextRunDate()}</div>
          </div>
          <div className="rounded-lg bg-white/60 p-3 dark:bg-black/20">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Users className="h-3.5 w-3.5" />
              <span className="text-xs font-medium">Recipients</span>
            </div>
            <div className="text-sm font-semibold">
              {state.recipients.length === 0 
                ? "None yet"
                : `${getTotalRecipients()} email${getTotalRecipients() !== 1 ? "s" : ""}`
              }
            </div>
          </div>
        </div>

        {/* Send Test Button */}
        <Button 
          variant="outline" 
          className="mt-4 w-full gap-2 bg-white/80 hover:bg-white dark:bg-black/30 dark:hover:bg-black/50" 
          onClick={onSendTest}
          disabled={sendingTest}
        >
          <Send className="h-4 w-4" />
          {sendingTest ? "Sending..." : "Send Test Email to Myself"}
        </Button>
      </div>
    </div>
  )
}
