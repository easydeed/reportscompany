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

// ============================================================================
// SOUTHERN CALIFORNIA CITIES (CRMLS Coverage Area)
// ============================================================================
// Counties: Los Angeles, Orange, San Diego, Riverside, San Bernardino,
// Ventura, Santa Barbara, Imperial, Kern (south)
// ============================================================================
export const SOCAL_CITIES: string[] = [
  // Los Angeles County - Major Cities
  "Los Angeles", "Long Beach", "Santa Clarita", "Glendale", "Lancaster",
  "Palmdale", "Pomona", "Torrance", "Pasadena", "El Monte",
  "Downey", "Inglewood", "West Covina", "Norwalk", "Burbank",
  "Compton", "South Gate", "Carson", "Santa Monica", "Whittier",
  "Hawthorne", "Alhambra", "Lakewood", "Bellflower", "Baldwin Park",
  "Lynwood", "Redondo Beach", "Pico Rivera", "Montebello", "Monterey Park",
  "Gardena", "Huntington Park", "Arcadia", "Diamond Bar", "Paramount",
  "Rosemead", "Glendora", "Cerritos", "La Mirada", "Covina",
  "Azusa", "La Puente", "San Dimas", "Culver City", "West Hollywood",
  "Claremont", "Monrovia", "Bell Gardens", "Manhattan Beach", "Beverly Hills",
  "Rancho Palos Verdes", "San Gabriel", "Hermosa Beach", "Temple City", "La Verne",
  "Duarte", "Calabasas", "Walnut", "Lawndale", "El Segundo",
  "Agoura Hills", "Malibu", "Palos Verdes Estates", "Rolling Hills",
  
  // Orange County
  "Anaheim", "Santa Ana", "Irvine", "Huntington Beach", "Garden Grove",
  "Orange", "Fullerton", "Costa Mesa", "Mission Viejo", "Westminster",
  "Newport Beach", "Buena Park", "Lake Forest", "Tustin", "Yorba Linda",
  "San Clemente", "Laguna Niguel", "La Habra", "Fountain Valley", "Placentia",
  "Rancho Santa Margarita", "Aliso Viejo", "Cypress", "Brea", "Stanton",
  "San Juan Capistrano", "Dana Point", "Laguna Beach", "Laguna Hills", "Seal Beach",
  "Los Alamitos", "Laguna Woods", "La Palma", "Villa Park",
  
  // San Diego County
  "San Diego", "Chula Vista", "Oceanside", "Escondido", "Carlsbad",
  "El Cajon", "Vista", "San Marcos", "Encinitas", "National City",
  "La Mesa", "Santee", "Poway", "Imperial Beach", "Solana Beach",
  "Lemon Grove", "Coronado", "Del Mar",
  
  // Riverside County
  "Riverside", "Moreno Valley", "Corona", "Murrieta", "Temecula",
  "Menifee", "Hemet", "Lake Elsinore", "Indio", "Perris",
  "Palm Desert", "Palm Springs", "San Jacinto", "La Quinta", "Eastvale",
  "Jurupa Valley", "Cathedral City", "Beaumont", "Coachella", "Wildomar",
  "Banning", "Desert Hot Springs", "Norco", "Rancho Mirage", "Indian Wells",
  
  // San Bernardino County
  "San Bernardino", "Fontana", "Rancho Cucamonga", "Ontario", "Victorville",
  "Rialto", "Hesperia", "Chino", "Chino Hills", "Upland",
  "Apple Valley", "Redlands", "Highland", "Colton", "Yucaipa",
  "Montclair", "Adelanto", "Loma Linda", "Barstow", "Twentynine Palms",
  "Yucca Valley", "Grand Terrace", "Big Bear Lake",
  
  // Ventura County
  "Oxnard", "Thousand Oaks", "Simi Valley", "Ventura", "Camarillo",
  "Moorpark", "Santa Paula", "Port Hueneme", "Fillmore", "Ojai",
  
  // Santa Barbara County
  "Santa Barbara", "Santa Maria", "Lompoc", "Goleta", "Carpinteria",
  "Guadalupe", "Solvang", "Buellton",
  
  // Imperial County
  "El Centro", "Calexico", "Brawley", "Imperial", "Holtville",
  
  // Kern County (Southern portion)
  "Bakersfield", "Tehachapi", "California City", "Ridgecrest", "Arvin",
  "Wasco", "Delano", "Shafter", "Taft", "Maricopa",
].sort()

// ============================================================================
// SIMPLIFIED UI - Audience Targeting (v2.0)
// ============================================================================
// Two main report types: New Listings (Gallery) and Market Update (Snapshot)
// Audience dropdown filters the New Listings report for different segments.
// ============================================================================

export interface AudienceOption {
  key: string
  name: string
  description: string
  filters: ReportFilters
}

export const AUDIENCE_OPTIONS: AudienceOption[] = [
  {
    key: "all",
    name: "All Listings",
    description: "No filters - show everything",
    filters: {}
  },
  {
    key: "first_time_buyers",
    name: "First-Time Buyers",
    description: "Affordable homes ≤70% of local median",
    filters: {
      minbeds: 2,
      minbaths: 2,
      subtype: "SingleFamilyResidence",
      price_strategy: {
        mode: "maxprice_pct_of_median_list",
        value: 0.70
      },
      preset_display_name: "First-Time Buyer"
    }
  },
  {
    key: "luxury_clients",
    name: "Luxury Clients",
    description: "Premium homes ≥150% of local median",
    filters: {
      subtype: "SingleFamilyResidence",
      price_strategy: {
        mode: "minprice_pct_of_median_list",
        value: 1.50
      },
      preset_display_name: "Luxury Showcase"
    }
  },
  {
    key: "families",
    name: "Families (3+ beds)",
    description: "Larger homes for growing families",
    filters: {
      minbeds: 3,
      minbaths: 2,
      subtype: "SingleFamilyResidence",
      preset_display_name: "Family Homes"
    }
  },
  {
    key: "condo_buyers",
    name: "Condo Buyers",
    description: "Condos and townhomes",
    filters: {
      subtype: "Condominium",
      preset_display_name: "Condo Watch"
    }
  },
  {
    key: "investors",
    name: "Investors",
    description: "Budget-friendly ≤50% of local median",
    filters: {
      price_strategy: {
        mode: "maxprice_pct_of_median_list",
        value: 0.50
      },
      preset_display_name: "Investor Deals"
    }
  },
]
