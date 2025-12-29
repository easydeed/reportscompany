// Schedule Types
export type ReportType = "market_snapshot" | "new_listings" | "inventory" | "closed" | "price_bands" | "open_houses" | "new_listings_gallery" | "featured_listings"

export type AreaMode = "city" | "zips"

export type Cadence = "weekly" | "monthly"

export type Weekday = "monday" | "tuesday" | "wednesday" | "thursday" | "friday" | "saturday" | "sunday"

// Property subtype for filtering
export type PropertySubtype = "SingleFamilyResidence" | "Condominium"

// Price strategy modes for market-adaptive presets
export type PriceStrategyMode = 
  | "maxprice_pct_of_median_list"   // e.g., 70% of median list price
  | "maxprice_pct_of_median_close"  // e.g., 70% of median close price
  | "minprice_pct_of_median_list"   // e.g., 150% of median (luxury)
  | "minprice_pct_of_median_close"

// Market-adaptive price strategy (resolves at runtime based on area)
export interface PriceStrategy {
  mode: PriceStrategyMode
  value: number  // Percentage as decimal (0.70 = 70%)
}

// Report filters for presets (supports both absolute and adaptive pricing)
export interface ReportFilters {
  minbeds?: number
  minbaths?: number
  minprice?: number           // Absolute min price (fallback)
  maxprice?: number           // Absolute max price (fallback)
  subtype?: PropertySubtype
  price_strategy?: PriceStrategy  // Market-adaptive pricing (preferred)
  preset_display_name?: string    // Custom name for PDF headers (e.g., "First-Time Buyer")
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
// SMART PRESETS - Market-Adaptive Report Templates
// ============================================================================
// These presets use price_strategy for market-adaptive pricing.
// At runtime, the worker resolves percentages to actual dollar amounts
// based on the selected area's median prices.
//
// Example: First-Time Buyer with 70% of median
//   - In Irvine (median ~$2.4M): resolves to maxprice ~$1.68M
//   - In Riverside (median ~$500K): resolves to maxprice ~$350K
// ============================================================================
export const SMART_PRESETS: PresetDefinition[] = [
  {
    key: "first_time_buyer",
    name: "First-Time Buyer",
    icon: "🏠",
    tagline: "Starter homes under ~70% of local median",
    report_type: "new_listings_gallery",
    lookback_days: 14,
    filters: {
      minbeds: 2,
      minbaths: 2,
      subtype: "SingleFamilyResidence",
      price_strategy: {
        mode: "maxprice_pct_of_median_list",
        value: 0.70  // 70% of median list price
      }
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
      // No price_strategy = no price filter (all condos)
    }
  },
  {
    key: "luxury_showcase",
    name: "Luxury Showcase",
    icon: "💎",
    tagline: "Premium homes above ~150% of local median",
    report_type: "featured_listings",
    lookback_days: 30,
    filters: {
      subtype: "SingleFamilyResidence",
      price_strategy: {
        mode: "minprice_pct_of_median_list",
        value: 1.50  // 150% of median list price (luxury segment)
      }
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
      // No price_strategy = all price ranges with 4+ beds
    }
  },
  {
    key: "investor_deals",
    name: "Investor Deals",
    icon: "📈",
    tagline: "Budget-friendly under ~50% of local median",
    report_type: "new_listings",
    lookback_days: 7,
    filters: {
      price_strategy: {
        mode: "maxprice_pct_of_median_list",
        value: 0.50  // 50% of median (true deals)
      }
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
