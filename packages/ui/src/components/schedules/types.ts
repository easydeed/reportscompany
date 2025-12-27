// Schedule Types
export type ReportType = "market_snapshot" | "new_listings" | "inventory" | "closed" | "price_bands" | "open_houses" | "new_listings_gallery" | "featured_listings"

export type AreaMode = "city" | "zips"

export type Cadence = "weekly" | "monthly"

export type Weekday = "monday" | "tuesday" | "wednesday" | "thursday" | "friday" | "saturday" | "sunday"

// Property subtype for filtering
export type PropertySubtype = "SingleFamilyResidence" | "Condominium"

// Report filters for presets
export interface ReportFilters {
  minbeds?: number
  minbaths?: number
  minprice?: number
  maxprice?: number
  subtype?: PropertySubtype
}

// Preset definition for Smart Presets
export interface PresetDefinition {
  key: string
  name: string
  icon: string  // Emoji for simplicity
  tagline: string
  report_type: ReportType
  lookback_days: number
  filters: ReportFilters
}

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
  filters: ReportFilters  // NEW: Preset filters
  preset_key?: string  // Track which preset was used (for analytics)

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
  open_houses: "Open Houses",
  new_listings_gallery: "New Listings (Photo Gallery)",
  featured_listings: "Featured Listings (Photo Grid)",
}

// ============================================================================
// SMART PRESETS - Pre-configured report templates for common audiences
// ============================================================================
export const SMART_PRESETS: PresetDefinition[] = [
  {
    key: "first_time_buyer",
    name: "First-Time Buyer",
    icon: "🏠",
    tagline: "Starter homes under $950K",
    report_type: "new_listings_gallery",
    lookback_days: 14,
    filters: {
      minbeds: 2,
      minbaths: 2,
      maxprice: 950000,
      subtype: "SingleFamilyResidence"
    }
  },
  {
    key: "condo_watch",
    name: "Condo Watch",
    icon: "🏢",
    tagline: "New condos on the market",
    report_type: "new_listings_gallery",
    lookback_days: 14,
    filters: {
      minbeds: 1,
      minbaths: 1,
      subtype: "Condominium"
    }
  },
  {
    key: "luxury_showcase",
    name: "Luxury Showcase",
    icon: "💎",
    tagline: "Premium homes $2M+",
    report_type: "featured_listings",
    lookback_days: 30,
    filters: {
      minprice: 2000000,
      subtype: "SingleFamilyResidence"
    }
  },
  {
    key: "family_homes",
    name: "Family Homes",
    icon: "👨‍👩‍👧‍👦",
    tagline: "4+ bedroom properties",
    report_type: "new_listings",
    lookback_days: 14,
    filters: {
      minbeds: 4,
      minbaths: 2,
      subtype: "SingleFamilyResidence"
    }
  },
  {
    key: "investor_deals",
    name: "Investor Deals",
    icon: "📈",
    tagline: "Properties under $500K",
    report_type: "new_listings",
    lookback_days: 7,
    filters: {
      maxprice: 500000
    }
  },
]

export const weekdayLabels: Record<Weekday, string> = {
  monday: "Monday",
  tuesday: "Tuesday",
  wednesday: "Wednesday",
  thursday: "Thursday",
  friday: "Friday",
  saturday: "Saturday",
  sunday: "Sunday",
}
