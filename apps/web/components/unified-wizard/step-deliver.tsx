"use client"

import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { FileText, Mail, Calendar, Clock, Check } from "lucide-react"
import { RecipientsSection } from "@/components/schedule-builder/sections/recipients-section"
import type { WizardState, DeliveryMode, Cadence } from "./types"

interface StepDeliverProps {
  state: WizardState
  onChange: (patch: Partial<WizardState>) => void
  defaultMode?: DeliveryMode
}

const DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
const HOURS = Array.from({ length: 24 }, (_, i) => i)

const TIMEZONES = [
  { value: "America/New_York", label: "Eastern" },
  { value: "America/Chicago", label: "Central" },
  { value: "America/Denver", label: "Mountain" },
  { value: "America/Los_Angeles", label: "Pacific" },
  { value: "America/Anchorage", label: "Alaska" },
  { value: "Pacific/Honolulu", label: "Hawaii" },
]

export function StepDeliver({ state, onChange, defaultMode }: StepDeliverProps) {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Almost there!</h2>
        <p className="text-sm text-gray-500 mt-1">
          {defaultMode ? "Review your delivery options." : "Send now or set up a recurring schedule."}
        </p>
      </div>

      {!defaultMode && (
        <div className="grid grid-cols-2 gap-2">
          <ModeCard
            active={state.deliveryMode === "send_now"}
            onClick={() => onChange({ deliveryMode: "send_now" })}
            icon={<Mail className="w-5 h-5" />}
            title="Send Now"
            description="Generate and deliver immediately"
          />
          <ModeCard
            active={state.deliveryMode === "schedule"}
            onClick={() => onChange({ deliveryMode: "schedule" })}
            icon={<Calendar className="w-5 h-5" />}
            title="Schedule"
            description="Set up recurring delivery"
          />
        </div>
      )}

      {state.deliveryMode === "send_now" ? (
        <SendNowOptions state={state} onChange={onChange} />
      ) : (
        <ScheduleOptions state={state} onChange={onChange} />
      )}
    </div>
  )
}

function ModeCard({
  active,
  onClick,
  icon,
  title,
  description,
}: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-xl border-2 p-4 text-left transition-all",
        active ? "border-primary bg-primary/5 shadow-sm" : "border-gray-200 hover:border-gray-300"
      )}
    >
      <div className={cn("mb-2", active ? "text-primary" : "text-gray-400")}>{icon}</div>
      <div className="text-sm font-semibold text-gray-900">{title}</div>
      <div className="text-[11px] text-gray-500 mt-0.5">{description}</div>
    </button>
  )
}

function SendNowOptions({
  state,
  onChange,
}: {
  state: WizardState
  onChange: (patch: Partial<WizardState>) => void
}) {
  return (
    <div className="space-y-4">
      {/* Confidence message */}
      <div className="flex items-start gap-3 rounded-xl border border-gray-200 bg-gray-50/80 p-4">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <FileText className="w-5 h-5" />
        </div>
        <div className="pt-0.5">
          <p className="text-sm font-medium text-gray-900">Your branded report will be ready to download in seconds.</p>
          <p className="text-xs text-gray-500 mt-0.5">A PDF will be generated and opened in a new tab automatically.</p>
        </div>
      </div>

      {/* Send to someone toggle card */}
      <div>
        <Label className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2 block">
          Send to someone?
        </Label>

        <button
          onClick={() => onChange({ sendViaEmail: !state.sendViaEmail, ...(!state.sendViaEmail ? {} : { recipients: [] }) })}
          className={cn(
            "group relative flex items-start gap-4 rounded-xl border-2 p-4 text-left transition-all w-full",
            state.sendViaEmail
              ? "border-primary bg-primary/5 shadow-sm"
              : "border-gray-200 hover:border-primary/40 hover:bg-gray-50/50",
            state.sendViaEmail && "rounded-b-none border-b-0"
          )}
        >
          <div className={cn(
            "flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg transition-colors",
            state.sendViaEmail ? "bg-primary/10 text-primary" : "bg-gray-100 text-gray-400"
          )}>
            <Mail className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-gray-900">Send Report</span>
              {state.sendViaEmail && (
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary">
                  <Check className="h-3 w-3 text-white" />
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-0.5">Email the PDF to a client or colleague</p>
          </div>
        </button>

        {state.sendViaEmail && (
          <div className="rounded-b-xl border-2 border-t-0 border-primary bg-primary/5 px-4 pb-4 pt-3 space-y-3">
            <RecipientsSection
              recipients={state.recipients}
              onChange={(patch) => onChange(patch as Partial<WizardState>)}
              hasRecipients={state.recipients.length > 0}
              stepNumber={undefined}
            />
            <p className="text-xs text-gray-500 text-center">You&apos;ll automatically receive a copy</p>
          </div>
        )}
      </div>
    </div>
  )
}

function ScheduleOptions({
  state,
  onChange,
}: {
  state: WizardState
  onChange: (patch: Partial<WizardState>) => void
}) {
  return (
    <div className="space-y-4">
      {/* Schedule name */}
      <div className="space-y-1.5">
        <Label className="text-xs font-medium">Schedule Name</Label>
        <Input
          value={state.scheduleName}
          onChange={(e) => onChange({ scheduleName: e.target.value })}
          placeholder="e.g., Weekly Luxury Listings – Silver Lake"
          className="h-10"
        />
      </div>

      {/* Frequency */}
      <div className="space-y-1.5">
        <Label className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Frequency</Label>
        <div className="grid grid-cols-2 gap-2">
          {(["weekly", "monthly"] as Cadence[]).map((c) => (
            <button
              key={c}
              onClick={() => onChange({ cadence: c })}
              className={cn(
                "rounded-lg border-2 py-2 text-xs font-medium capitalize transition-all",
                state.cadence === c ? "border-primary bg-primary/5 text-primary" : "border-gray-200 text-gray-500 hover:border-gray-300"
              )}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Day + Time */}
      <div className="grid grid-cols-2 gap-3">
        {state.cadence === "weekly" && (
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Day</Label>
            <Select value={String(state.dayOfWeek)} onValueChange={(v) => onChange({ dayOfWeek: Number(v) })}>
              <SelectTrigger className="h-9 text-xs"><SelectValue /></SelectTrigger>
              <SelectContent>
                {DAYS_OF_WEEK.map((day, i) => (
                  <SelectItem key={i} value={String(i)}>{day}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {state.cadence === "monthly" && (
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Day of Month</Label>
            <Select value={String(state.dayOfMonth)} onValueChange={(v) => onChange({ dayOfMonth: Number(v) })}>
              <SelectTrigger className="h-9 text-xs"><SelectValue /></SelectTrigger>
              <SelectContent>
                {Array.from({ length: 28 }, (_, i) => i + 1).map((d) => (
                  <SelectItem key={d} value={String(d)}>{d}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Time</Label>
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
            <Select value={String(state.sendHour)} onValueChange={(v) => onChange({ sendHour: Number(v) })}>
              <SelectTrigger className="h-9 text-xs flex-1"><SelectValue /></SelectTrigger>
              <SelectContent>
                {HOURS.map((h) => (
                  <SelectItem key={h} value={String(h)}>
                    {h === 0 ? "12 AM" : h < 12 ? `${h} AM` : h === 12 ? "12 PM" : `${h - 12} PM`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Timezone */}
      <div className="space-y-1.5">
        <Label className="text-xs font-medium">Timezone</Label>
        <Select value={state.timezone} onValueChange={(v) => onChange({ timezone: v })}>
          <SelectTrigger className="h-9 text-xs"><SelectValue /></SelectTrigger>
          <SelectContent>
            {TIMEZONES.map((tz) => (
              <SelectItem key={tz.value} value={tz.value}>{tz.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <RecipientsSection
        recipients={state.recipients}
        onChange={(patch) => onChange(patch as Partial<WizardState>)}
        hasRecipients={state.recipients.length > 0}
        stepNumber={undefined}
      />
    </div>
  )
}

