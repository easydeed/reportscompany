"use client"

import { Button } from "@/components/ui/button"
import { Mail, Users, Clock } from "lucide-react"
import {
  type ScheduleBuilderState,
  type BrandingContext,
  type ProfileContext,
  getEmailSubject,
  getAreaDisplay,
  DAY_NAMES,
} from "@/lib/schedule-types"
import { EmailPreview } from "./email-preview"

interface EmailPreviewPanelProps {
  state: ScheduleBuilderState
  branding: BrandingContext
  profile: ProfileContext
}

export function EmailPreviewPanel({ state, branding, profile }: EmailPreviewPanelProps) {
  const subject = getEmailSubject(state)
  const area = getAreaDisplay(state)

  const getNextRunDate = () => {
    const now = new Date()
    const dayNames = DAY_NAMES

    if (state.cadence === "weekly") {
      const daysUntil = (state.weeklyDow - now.getDay() + 7) % 7 || 7
      const nextDate = new Date(now)
      nextDate.setDate(now.getDate() + daysUntil)
      return `${dayNames[state.weeklyDow]}, ${nextDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })} at ${state.sendHour}:${state.sendMinute.toString().padStart(2, "0")} AM PT`
    } else {
      const nextDate = new Date(now.getFullYear(), now.getMonth(), state.monthlyDom)
      if (nextDate <= now) {
        nextDate.setMonth(nextDate.getMonth() + 1)
      }
      return `${nextDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })} at ${state.sendHour}:${state.sendMinute.toString().padStart(2, "0")} AM PT`
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
      <div className="rounded-xl border bg-card overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h3 className="text-sm font-semibold">EMAIL PREVIEW</h3>
          <span className="text-xs text-muted-foreground">Updates as you build</span>
        </div>

        {/* Subject Line */}
        <div className="border-b px-4 py-3">
          <div className="text-xs text-muted-foreground mb-1">Subject:</div>
          <div className="text-sm font-medium">{subject}</div>
        </div>

        {/* Email Preview */}
        <div className="p-4 bg-stone-100 max-h-[calc(100vh-400px)] overflow-y-auto">
          <EmailPreview state={state} branding={branding} profile={profile} area={area} />
        </div>

        {/* Schedule Info */}
        <div className="border-t px-4 py-3 space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Next send:</span>
            <span className="font-medium">{getNextRunDate()}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">
              {state.recipients.length} recipients ({getTotalRecipients()} emails)
            </span>
          </div>
        </div>

        {/* Send Test Button */}
        <div className="border-t px-4 py-4">
          <Button variant="outline" className="w-full gap-2 bg-transparent">
            <Mail className="h-4 w-4" />
            Send Test Email to Myself
          </Button>
        </div>
      </div>
    </div>
  )
}
