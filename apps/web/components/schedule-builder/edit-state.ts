import type { Schedule } from "@/components/schedules/types"
import { AUDIENCE_FILTER_PRESETS, type AudienceFilter, type Recipient, type ScheduleBuilderState } from "./types"

type StoredRecipient =
  | { type: "manual_email"; email: string }
  | { type: "contact" | "sponsored_agent" | "group"; id: string }

export type StoredSchedule = Omit<Schedule, "account_id"> & {
  weekly_dow?: ScheduleBuilderState["weeklyDow"] | null
  lookback_days: NonNullable<ScheduleBuilderState["lookbackDays"]>
  timezone: string
  resolved_recipients: StoredRecipient[]
  filters: Record<string, unknown> | null
}

function displayRecipient(recipient: StoredRecipient): Recipient {
  switch (recipient.type) {
    case "manual_email": return recipient
    case "contact": return { ...recipient, type: "contact", name: recipient.id, email: "" }
    case "group": return { ...recipient, type: "group", name: recipient.id, memberCount: 0 }
    case "sponsored_agent": return { ...recipient, type: "sponsored_agent", name: `Sponsored agent · ${recipient.id}` }
  }
}

export function editState(schedule: StoredSchedule): ScheduleBuilderState {
  const filters = schedule.filters ?? {}
  const preset = Object.entries(AUDIENCE_FILTER_PRESETS).find(([, value]) =>
    Object.keys(value).length === Object.keys(filters).length &&
    Object.entries(value).every(([key, field]) => JSON.stringify(filters[key]) === JSON.stringify(field))
  )
  const hasFilters = Object.keys(filters).length > 0
  return {
    name: schedule.name,
    active: schedule.active,
    reportType: schedule.report_type,
    lookbackDays: schedule.lookback_days,
    areaType: schedule.zip_codes?.length ? "zip" : "city",
    city: schedule.zip_codes?.length ? null : schedule.city ?? null,
    zipCodes: schedule.zip_codes ?? [],
    audienceFilter: (preset?.[0] as AudienceFilter) ?? (hasFilters ? null : "all"),
    audienceFilterName: typeof filters.preset_display_name === "string" ? filters.preset_display_name : null,
    cadence: schedule.cadence,
    weeklyDow: schedule.weekly_dow ?? 1,
    monthlyDom: schedule.monthly_dom ?? 1,
    sendHour: schedule.send_hour,
    sendMinute: schedule.send_minute,
    timezone: schedule.timezone,
    recipients: schedule.resolved_recipients.map(displayRecipient),
    includeAttachment: schedule.include_attachment,
  }
}

export function schedulePayload(state: ScheduleBuilderState) {
  return {
    name: state.name.trim(),
    active: state.active,
    report_type: state.reportType,
    city: state.areaType === "city" ? state.city : null,
    zip_codes: state.areaType === "zip" ? state.zipCodes : null,
    lookback_days: state.lookbackDays,
    cadence: state.cadence,
    weekly_dow: state.cadence === "weekly" ? state.weeklyDow : null,
    monthly_dom: state.cadence === "monthly" ? state.monthlyDom : null,
    send_hour: state.sendHour,
    send_minute: state.sendMinute,
    timezone: state.timezone,
    recipients: state.recipients.map(r => r.type === "manual_email" ? r : { type: r.type, id: r.id }),
    include_attachment: state.includeAttachment,
    filters: state.audienceFilter ? AUDIENCE_FILTER_PRESETS[state.audienceFilter] ?? null : null,
  }
}

export function schedulePatch(initial: ScheduleBuilderState, state: ScheduleBuilderState) {
  const before = schedulePayload(initial)
  const after = schedulePayload(state)
  const patch: Record<string, unknown> = {}
  for (const key of Object.keys(after) as (keyof typeof after)[]) {
    if (JSON.stringify(before[key]) !== JSON.stringify(after[key])) patch[key] = after[key]
  }
  // PATCH treats null as omitted. An area edit must also clear the other location.
  if ("city" in patch || "zip_codes" in patch) {
    patch.city = after.city ?? ""
    patch.zip_codes = after.zip_codes ?? []
  }
  if (state.audienceFilter !== initial.audienceFilter) patch.filters = after.filters ?? {}
  return patch
}
