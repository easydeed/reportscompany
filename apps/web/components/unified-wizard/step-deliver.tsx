"use client"

/**
 * Step 4 — what happens with it. Design's `Wizards v3`: radio rows with what
 * each choice costs, then recipients; or, for a schedule, cadence pills, the
 * day, the hour and a name.
 *
 * Every field writes the same state it did before. Three things from the deck
 * are not carried over: "Weekly · Growth" (nothing gates weekly delivery by
 * plan), its fixed list of seven days of the month (the product offers 1–28),
 * and "You'll see who opens" (not something this flow shows).
 */
import { RecipientsSection } from "@/components/schedule-builder/sections/recipients-section"
import { REPORT_TYPES, getAreaDisplay, type WizardState, type DeliveryMode, type Cadence } from "./types"
import { FieldLabel, Pill, RadioList, RadioRow, StepHeader, selectClass } from "./wizard-ui"

interface StepDeliverProps {
  state: WizardState
  onChange: (patch: Partial<WizardState>) => void
  defaultMode?: DeliveryMode
}

const DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
const HOURS = Array.from({ length: 24 }, (_, i) => i)
const hourLabel = (h: number) => (h === 0 ? "12 AM" : h < 12 ? `${h} AM` : h === 12 ? "12 PM" : `${h - 12} PM`)

const TIMEZONES = [
  { value: "America/New_York", label: "Eastern" },
  { value: "America/Chicago", label: "Central" },
  { value: "America/Denver", label: "Mountain" },
  { value: "America/Los_Angeles", label: "Pacific" },
  { value: "America/Anchorage", label: "Alaska" },
  { value: "Pacific/Honolulu", label: "Hawaii" },
]

export function StepDeliver({ state, onChange, defaultMode }: StepDeliverProps) {
  const isSchedule = state.deliveryMode === "schedule"
  return (
    <div className="flex flex-col gap-6">
      <StepHeader
        title={isSchedule ? "When should it go out?" : "What happens with it?"}
        sub={
          isSchedule
            ? "Every run uses one report from your allowance and pulls fresh data when it runs."
            : "Download it now, or send it from you with the PDF attached."
        }
      />

      {!defaultMode && (
        <RadioList>
          <RadioRow
            on={state.deliveryMode === "send_now"}
            onClick={() => onChange({ deliveryMode: "send_now" })}
            label="Send now"
            desc="Generate and deliver immediately"
          />
          <RadioRow
            on={state.deliveryMode === "schedule"}
            onClick={() => onChange({ deliveryMode: "schedule" })}
            label="Put it on a schedule"
            desc="Fresh data every send"
          />
        </RadioList>
      )}

      {isSchedule ? (
        <ScheduleOptions state={state} onChange={onChange} />
      ) : (
        <SendNowOptions state={state} onChange={onChange} />
      )}
    </div>
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
    <div className="flex flex-col gap-6">
      <div role="radiogroup" aria-label="Delivery">
        <RadioList>
          <RadioRow
            on={!state.sendViaEmail}
            onClick={() => onChange({ sendViaEmail: false, recipients: [] })}
            label="Download the PDF"
            desc="Opens in a new tab when it's ready. Print it, attach it, post it."
            aside="1 report"
          />
          <RadioRow
            on={state.sendViaEmail}
            onClick={() => onChange({ sendViaEmail: true })}
            label="Send it to contacts now"
            desc="From you, with the PDF attached."
            aside="1 report"
          />
        </RadioList>
      </div>

      {state.sendViaEmail && (
        <div className="flex flex-col gap-2.5">
          <FieldLabel>To</FieldLabel>
          <RecipientsSection
            recipients={state.recipients}
            onChange={(recipients) => onChange({ recipients })}
            hasRecipients={state.recipients.length > 0}
            stepNumber={undefined}
          />
          <span className="text-[13px] text-[#64748B]">You&apos;ll automatically receive a copy.</span>
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
  const tz = TIMEZONES.find((t) => t.value === state.timezone)?.label ?? state.timezone
  const ord = (n: number) => n + (n % 10 === 1 && n !== 11 ? "st" : n % 10 === 2 && n !== 12 ? "nd" : n % 10 === 3 && n !== 13 ? "rd" : "th")
  const when =
    state.cadence === "weekly"
      ? `weekly on ${DAYS_OF_WEEK[state.dayOfWeek]}`
      : `monthly on the ${ord(state.dayOfMonth)}`
  const kind = REPORT_TYPES.find((r) => r.id === state.reportType)?.title ?? "Report"
  const area = state.city || state.zipCodes.length ? getAreaDisplay(state) : "your area"
  const namePlaceholder = `${state.cadence === "monthly" ? "Monthly" : "Weekly"} ${area} ${kind}`

  return (
    <div className="flex flex-col gap-[18px]">
      <div className="flex flex-col gap-2.5">
        <FieldLabel>Cadence</FieldLabel>
        <div className="flex gap-1.5">
          {(["weekly", "monthly"] as Cadence[]).map((c) => (
            <Pill key={c} on={state.cadence === c} onClick={() => onChange({ cadence: c })}>
              {c === "weekly" ? "Weekly" : "Monthly"}
            </Pill>
          ))}
        </div>

        {state.cadence === "weekly" ? (
          <div className="flex flex-wrap gap-1.5">
            {DAYS_OF_WEEK.map((d, i) => (
              <Pill
                key={d}
                on={state.dayOfWeek === i}
                onClick={() => onChange({ dayOfWeek: i })}
                className="min-w-[44px] rounded-lg px-2.5 text-center"
              >
                {d.slice(0, 3)}
              </Pill>
            ))}
          </div>
        ) : (
          <label className="flex items-center gap-2 text-[13px] text-[#64748B]">
            Day of month
            <select
              value={state.dayOfMonth}
              onChange={(e) => onChange({ dayOfMonth: Number(e.target.value) })}
              className={selectClass}
            >
              {Array.from({ length: 28 }, (_, i) => i + 1).map((d) => (
                <option key={d} value={d}>{ord(d)}</option>
              ))}
            </select>
          </label>
        )}

        <div className="flex flex-wrap items-center gap-2 text-[13px] text-[#64748B]">
          <label className="flex items-center gap-2">
            At
            <select
              value={state.sendHour}
              onChange={(e) => onChange({ sendHour: Number(e.target.value) })}
              className={selectClass}
            >
              {HOURS.map((h) => (
                <option key={h} value={h}>{hourLabel(h)}</option>
              ))}
            </select>
          </label>
          <select
            aria-label="Timezone"
            value={state.timezone}
            onChange={(e) => onChange({ timezone: e.target.value })}
            className={selectClass}
          >
            {TIMEZONES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>
        <span className="text-[13px] text-[#64748B]">
          Sends {when} at {hourLabel(state.sendHour).replace(" ", ":00 ")} {tz}.
        </span>
      </div>

      <label className="flex flex-col gap-1.5">
        <FieldLabel>Name</FieldLabel>
        <input
          value={state.scheduleName}
          onChange={(e) => onChange({ scheduleName: e.target.value })}
          placeholder={namePlaceholder}
          className="h-11 rounded-lg border border-[#D6D3CB] px-3 text-[15px] font-medium text-[#0F172A] outline-none focus:border-[#0F172A]"
        />
      </label>

      <div className="flex flex-col gap-2.5">
        <FieldLabel>To</FieldLabel>
        <RecipientsSection
          recipients={state.recipients}
          onChange={(recipients) => onChange({ recipients })}
          hasRecipients={state.recipients.length > 0}
          stepNumber={undefined}
        />
      </div>
    </div>
  )
}
