export type ReportType = "new_listings" | "new_listings_gallery" | "market_snapshot" | "closed" | "inventory" | "price_bands" | "open_houses" | "featured_listings"

export type AudienceFilter = "all" | "first_time" | "luxury" | "families" | "condo" | "investors" | null

export type Recipient =
  | { type: "contact"; id: string; name: string; email: string }
  | { type: "group"; id: string; name: string; memberCount: number }
  | { type: "manual_email"; email: string }

export interface ScheduleBuilderState {
  name: string
  reportType: ReportType
  lookbackDays: 7 | 14 | 30 | 60 | 90
  areaType: "city" | "zip"
  city: string | null
  zipCodes: string[]
  audienceFilter: AudienceFilter
  audienceFilterName: string | null
  cadence: "weekly" | "monthly"
  weeklyDow: 0 | 1 | 2 | 3 | 4 | 5 | 6
  monthlyDom: number
  sendHour: number
  sendMinute: number
  timezone: string
  recipients: Recipient[]
  includeAttachment: boolean
}

export type SectionStatus = "complete" | "warning" | "optional" | "incomplete"

// Branding context from /v1/account/branding
export interface BrandingContext {
  primaryColor: string
  accentColor: string
  emailLogoUrl: string | null
  displayName: string | null
}

// Profile context from /v1/users/me
export interface ProfileContext {
  name: string
  jobTitle: string | null
  avatarUrl: string | null
  phone: string | null
  email: string
}

// Map UI audience filter to API filters (SMART PRESETS)
export const AUDIENCE_FILTER_PRESETS: Record<string, {
  minbeds?: number
  minbaths?: number
  subtype?: string
  price_strategy?: { mode: string; value: number }
  preset_display_name: string
}> = {
  first_time: {
    minbeds: 2,
    minbaths: 2,
    subtype: "SingleFamilyResidence",
    price_strategy: { mode: "maxprice_pct_of_median_list", value: 0.70 },
    preset_display_name: "First-Time Buyer"
  },
  luxury: {
    subtype: "SingleFamilyResidence",
    price_strategy: { mode: "minprice_pct_of_median_list", value: 1.50 },
    preset_display_name: "Luxury"
  },
  families: {
    minbeds: 3,
    minbaths: 2,
    subtype: "SingleFamilyResidence",
    preset_display_name: "Family Homes"
  },
  condo: {
    subtype: "Condominium",
    preset_display_name: "Condo Watch"
  },
  investors: {
    price_strategy: { mode: "maxprice_pct_of_median_list", value: 0.50 },
    preset_display_name: "Investor Deals"
  }
}

// Human-readable labels
export const REPORT_TYPE_LABELS: Record<ReportType, string> = {
  market_snapshot: "Market Update",
  new_listings: "New Listings",
  new_listings_gallery: "New Listings",
  closed: "Closed Sales",
  inventory: "Inventory Report",
  price_bands: "Price Analysis",
  open_houses: "Open Houses",
  featured_listings: "Featured Listings",
}

// Helper functions
export function getAreaDisplay(state: ScheduleBuilderState): string {
  if (state.city) return state.city
  if (state.zipCodes.length === 1) return `ZIP ${state.zipCodes[0]}`
  if (state.zipCodes.length <= 3) return `ZIPs ${state.zipCodes.join(", ")}`
  if (state.zipCodes.length > 0) return `${state.zipCodes.length} ZIP codes`
  return "Select an area"
}

export function getEmailSubject(state: ScheduleBuilderState): string {
  const getLabel = () => {
    if (state.reportType === "new_listings_gallery" && state.audienceFilter && state.audienceFilter !== "all") {
      return state.audienceFilterName || "New Listings"
    }
    return REPORT_TYPE_LABELS[state.reportType] || state.reportType
  }
  const label = getLabel()
  const area = getAreaDisplay(state)
  return `Your ${label} for ${area} is Ready!`
}
