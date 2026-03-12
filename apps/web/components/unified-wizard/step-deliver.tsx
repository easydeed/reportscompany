"use client"

import { useState } from "react"
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
import { Globe, FileDown, Mail, Calendar, Clock, X } from "lucide-react"
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
  const [emailInput, setEmailInput] = useState("")

  const addEmail = () => {
    const email = emailInput.trim()
    if (email && email.includes("@") && !state.recipientEmails.includes(email)) {
      onChange({ recipientEmails: [...state.recipientEmails, email] })
      setEmailInput("")
    }
  }

  const removeEmail = (email: string) => {
    onChange({ recipientEmails: state.recipientEmails.filter((e) => e !== email) })
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">How do you want to deliver it?</h2>
        <p className="text-sm text-gray-500 mt-1">
          {defaultMode ? "Choose your delivery options." : "Send now or set up a recurring schedule."}
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
        <SendNowOptions state={state} onChange={onChange} emailInput={emailInput} setEmailInput={setEmailInput} addEmail={addEmail} removeEmail={removeEmail} />
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
  emailInput,
  setEmailInput,
  addEmail,
  removeEmail,
}: {
  state: WizardState
  onChange: (patch: Partial<WizardState>) => void
  emailInput: string
  setEmailInput: (v: string) => void
  addEmail: () => void
  removeEmail: (email: string) => void
}) {
  return (
    <div className="space-y-4">
      <Label className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Delivery Options</Label>

      <div className="space-y-2">
        <Checkbox checked={state.viewInBrowser} onChange={(v) => onChange({ viewInBrowser: v })} icon={<Globe className="w-4 h-4" />} label="View in browser" />
        <Checkbox checked={state.downloadPdf} onChange={(v) => onChange({ downloadPdf: v })} icon={<FileDown className="w-4 h-4" />} label="Download PDF" />
        <Checkbox checked={state.sendViaEmail} onChange={(v) => onChange({ sendViaEmail: v })} icon={<Mail className="w-4 h-4" />} label="Send via email" />
      </div>

      {state.sendViaEmail && (
        <div className="space-y-2 pl-6">
          <Label className="text-xs text-gray-600">Recipients</Label>
          <div className="flex gap-2">
            <Input
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addEmail()}
              placeholder="email@example.com"
              className="h-9 text-xs flex-1"
            />
            <button onClick={addEmail} className="px-3 h-9 rounded-lg bg-primary text-white text-xs font-medium">Add</button>
          </div>
          {state.recipientEmails.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {state.recipientEmails.map((email) => (
                <span key={email} className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-700">
                  {email}
                  <button onClick={() => removeEmail(email)} className="hover:text-red-500"><X className="h-3 w-3" /></button>
                </span>
              ))}
            </div>
          )}
        </div>
      )}
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

function Checkbox({
  checked,
  onChange,
  icon,
  label,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  icon: React.ReactNode
  label: string
}) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={cn(
        "flex items-center gap-3 w-full rounded-lg border-2 px-3 py-2.5 text-left transition-all",
        checked ? "border-primary/30 bg-primary/5" : "border-gray-200 hover:bg-gray-50"
      )}
    >
      <div className={cn("flex-shrink-0", checked ? "text-primary" : "text-gray-400")}>{icon}</div>
      <span className="text-sm text-gray-700 flex-1">{label}</span>
      <div className={cn("w-4 h-4 rounded border-2 flex items-center justify-center transition-colors", checked ? "border-primary bg-primary" : "border-gray-300")}>
        {checked && <svg className="w-2.5 h-2.5 text-white" viewBox="0 0 12 12"><path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" fill="none" /></svg>}
      </div>
    </button>
  )
}
