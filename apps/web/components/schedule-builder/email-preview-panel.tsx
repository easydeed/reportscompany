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
      <div className="rounded-xl border bg-card overflow-hidden shadow-sm">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-3 bg-muted/30">
          <h3 className="text-sm font-semibold">EMAIL PREVIEW</h3>
          <span className="text-xs text-muted-foreground">Updates as you build</span>
        </div>

        {/* Subject Line */}
        <div className="border-b px-4 py-3">
          <div className="text-xs text-muted-foreground mb-1">Subject:</div>
          <div className="text-sm font-medium truncate">{subject}</div>
        </div>

        {/* Email Preview */}
        <div className="p-4 bg-stone-100 dark:bg-stone-900 max-h-[calc(100vh-420px)] overflow-y-auto">
          <EmailPreview state={state} branding={branding} profile={profile} area={area} />
        </div>

        {/* Schedule Info */}
        <div className="border-t px-4 py-3 space-y-2 bg-muted/20">
          <div className="flex items-center gap-2 text-sm">
            <Clock className="h-4 w-4 text-muted-foreground shrink-0" />
            <span className="text-muted-foreground">Next send:</span>
            <span className="font-medium truncate">{getNextRunDate()}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Users className="h-4 w-4 text-muted-foreground shrink-0" />
            <span className="text-muted-foreground">
              {state.recipients.length === 0 
                ? "No recipients added yet"
                : `${state.recipients.length} recipient${state.recipients.length !== 1 ? "s" : ""} (${getTotalRecipients()} email${getTotalRecipients() !== 1 ? "s" : ""})`
              }
            </span>
          </div>
        </div>

        {/* Send Test Button */}
        <div className="border-t px-4 py-4">
          <Button 
            variant="outline" 
            className="w-full gap-2 bg-transparent" 
            onClick={onSendTest}
            disabled={sendingTest}
          >
            <Mail className="h-4 w-4" />
            {sendingTest ? "Sending..." : "Send Test Email to Myself"}
          </Button>
        </div>
      </div>
    </div>
  )
}

