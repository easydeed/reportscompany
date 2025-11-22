// Schedule Types
export type ReportType = "market_snapshot" | "new_listings" | "inventory" | "closed" | "price_bands" | "new_listings_gallery" | "featured_listings"

export type AreaMode = "city" | "zips"

export type Cadence = "weekly" | "monthly"

export type Weekday = "monday" | "tuesday" | "wednesday" | "thursday" | "friday" | "saturday" | "sunday"

export interface Schedule {
  id: string
  name: string
  report_type: ReportType
  area_mode: AreaMode
  city?: string
  zips?: string[]
  lookback_days: number
  cadence: Cadence
  weekday?: Weekday
  monthly_day?: number
  time: string // HH:MM format
  recipients: string[]
  active: boolean
  next_run: string
  last_run?: string
  created_at: string
}

export interface ScheduleRun {
  id: string
  schedule_id: string
  created_at: string
  status: "pending" | "processing" | "completed" | "failed"
  finished_at?: string
  error?: string
}

// Typed recipient for API
export interface TypedRecipient {
  type: "contact" | "sponsored_agent" | "group" | "manual_email"
  id?: string
  email?: string
}

export interface ScheduleWizardState {
  // Step 1: Basics
  name: string
  report_type: ReportType | null
  lookback_days: number

  // Step 2: Area
  area_mode: AreaMode
  city: string
  zips: string[]

  // Step 3: Cadence
  cadence: Cadence
  weekday: Weekday
  monthly_day: number
  time: string

  // Step 4: Recipients
  recipients: string[]  // Legacy: for display only
  typedRecipients?: TypedRecipient[]  // New: for API submission
}

export const reportTypeLabels: Record<ReportType, string> = {
  market_snapshot: "Market Snapshot",
  new_listings: "New Listings",
  inventory: "Inventory Report",
  closed: "Closed Sales",
  price_bands: "Price Bands",
  new_listings_gallery: "New Listings (Photo Gallery)",
  featured_listings: "Featured Listings (Photo Grid)",
}

export const weekdayLabels: Record<Weekday, string> = {
  monday: "Monday",
  tuesday: "Tuesday",
  wednesday: "Wednesday",
  thursday: "Thursday",
  friday: "Friday",
  saturday: "Saturday",
  sunday: "Sunday",
}
