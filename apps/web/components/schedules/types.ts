// Schedule Types - Adapted for backend API schema

export type ReportType =
  | "market_snapshot"
  | "new_listings"
  | "inventory"
  | "closed"
  | "price_bands"
  | "open_houses"
  | "new_listings_gallery"
  | "featured_listings"

export type Cadence = "weekly" | "monthly"

// Backend API Schedule interface
export interface Schedule {
  id: string
  account_id: string
  name: string
  report_type: ReportType
  city?: string | null
  zip_codes?: string[] | null
  lookback_days: number
  cadence: Cadence
  weekly_dow?: number | null // 0=Sun, 1=Mon, ..., 6=Sat
  monthly_dom?: number | null // 1-28
  send_hour: number // 0-23
  send_minute: number // 0-59
  recipients: string[]
  include_attachment: boolean
  active: boolean
  last_run_at?: string | null
  next_run_at?: string | null
  created_at: string
}

// Backend API Schedule Run interface
export interface ScheduleRun {
  id: string
  schedule_id: string
  report_run_id?: string | null
  status: "queued" | "processing" | "completed" | "failed"
  error?: string | null
  started_at?: string | null
  finished_at?: string | null
  created_at: string
}

// UI-friendly weekday names
export type Weekday = "sunday" | "monday" | "tuesday" | "wednesday" | "thursday" | "friday" | "saturday"

// Wizard state (UI model)
export interface ScheduleWizardState {
  // Step 1: Basics
  name: string
  report_type: ReportType | null
  lookback_days: number

  // Step 2: Area
  area_mode: "city" | "zips"
  city: string
  zips: string[]

  // Step 3: Cadence
  cadence: Cadence
  weekday: Weekday // UI uses weekday names
  monthly_day: number
  time: string // HH:MM format for UI

  // Step 4: Recipients
  recipients: string[]
}

// Helper: Convert weekday name to dow number
export function weekdayToDow(weekday: Weekday): number {
  const map: Record<Weekday, number> = {
    sunday: 0,
    monday: 1,
    tuesday: 2,
    wednesday: 3,
    thursday: 4,
    friday: 5,
    saturday: 6,
  }
  return map[weekday]
}

// Helper: Convert dow number to weekday name
export function dowToWeekday(dow: number): Weekday {
  const map: Weekday[] = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
  return map[dow] || "monday"
}

// Helper: Convert time string (HH:MM) to hour/minute
export function parseTime(time: string): { hour: number; minute: number } {
  const [hour, minute] = time.split(":").map(Number)
  return { hour: hour || 9, minute: minute || 0 }
}

// Helper: Format hour/minute to time string (HH:MM)
export function formatTime(hour: number, minute: number): string {
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`
}

// Helper: Convert wizard state to API payload
export function wizardStateToApiPayload(state: ScheduleWizardState): Partial<Schedule> {
  const { hour, minute } = parseTime(state.time)

  return {
    name: state.name,
    report_type: state.report_type!,
    city: state.area_mode === "city" ? state.city : null,
    zip_codes: state.area_mode === "zips" ? state.zips : null,
    lookback_days: state.lookback_days,
    cadence: state.cadence,
    weekly_dow: state.cadence === "weekly" ? weekdayToDow(state.weekday) : null,
    monthly_dom: state.cadence === "monthly" ? state.monthly_day : null,
    send_hour: hour,
    send_minute: minute,
    recipients: state.recipients,
    include_attachment: false, // v1: link-only
    active: true,
  }
}

// Helper: Convert API schedule to wizard state
export function apiScheduleToWizardState(schedule: Schedule): ScheduleWizardState {
  return {
    name: schedule.name,
    report_type: schedule.report_type,
    lookback_days: schedule.lookback_days,
    area_mode: schedule.city ? "city" : "zips",
    city: schedule.city || "",
    zips: schedule.zip_codes || [],
    cadence: schedule.cadence,
    weekday: schedule.weekly_dow !== null && schedule.weekly_dow !== undefined 
      ? dowToWeekday(schedule.weekly_dow) 
      : "monday",
    monthly_day: schedule.monthly_dom || 1,
    time: formatTime(schedule.send_hour, schedule.send_minute),
    recipients: schedule.recipients,
  }
}

export const reportTypeLabels: Record<ReportType, string> = {
  market_snapshot: "Market Snapshot",
  new_listings: "New Listings",
  inventory: "Inventory Report",
  closed: "Closed Sales",
  price_bands: "Price Bands",
  open_houses: "Open Houses",
  new_listings_gallery: "New Listings Gallery",
  featured_listings: "Featured Listings",
}

export const weekdayLabels: Record<Weekday, string> = {
  sunday: "Sunday",
  monday: "Monday",
  tuesday: "Tuesday",
  wednesday: "Wednesday",
  thursday: "Thursday",
  friday: "Friday",
  saturday: "Saturday",
}

