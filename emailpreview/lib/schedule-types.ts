export type ReportType =
  | "market_snapshot"
  | "new_listings_gallery"
  | "closed"
  | "inventory"
  | "price_bands"
  | "open_houses"

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

export interface BrandingContext {
  primaryColor: string
  accentColor: string
  emailLogoUrl: string | null
}

export interface ProfileContext {
  name: string
  jobTitle: string
  avatarUrl: string | null
  phone: string
  email: string
}

export const REPORT_TYPE_LABELS: Record<ReportType, string> = {
  market_snapshot: "Market Snapshot",
  new_listings_gallery: "New Listings",
  closed: "Closed Sales",
  inventory: "Inventory Report",
  price_bands: "Price Analysis",
  open_houses: "Open Houses",
}

export const REPORT_TYPE_ICONS: Record<ReportType, string> = {
  market_snapshot: "📊",
  new_listings_gallery: "📸",
  closed: "🏠",
  inventory: "📦",
  price_bands: "💰",
  open_houses: "🚪",
}

export const AUDIENCE_FILTERS = [
  {
    id: "all" as const,
    name: "All Listings",
    description: "No filters - show everything",
  },
  {
    id: "first_time" as const,
    name: "First-Time Buyers",
    description: "2+ beds, 2+ baths, SFR, ≤70% median price",
  },
  {
    id: "luxury" as const,
    name: "Luxury Clients",
    description: "SFR, ≥150% median price",
  },
  {
    id: "families" as const,
    name: "Families",
    description: "3+ beds, 2+ baths, SFR",
  },
  {
    id: "condo" as const,
    name: "Condo Buyers",
    description: "Condos only",
  },
  {
    id: "investors" as const,
    name: "Investors",
    description: "≤50% median price",
  },
]

export const DAYS_OF_WEEK = ["S", "M", "T", "W", "T", "F", "S"]
export const DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

export function getAreaDisplay(state: ScheduleBuilderState): string {
  if (state.city) {
    return state.city
  }
  if (state.zipCodes.length === 1) {
    return `ZIP ${state.zipCodes[0]}`
  }
  if (state.zipCodes.length <= 3) {
    return `ZIPs ${state.zipCodes.join(", ")}`
  }
  return `${state.zipCodes.length} ZIP codes`
}

export function getEmailSubject(state: ScheduleBuilderState): string {
  const reportLabels: Record<ReportType, string> = {
    market_snapshot: "Market Snapshot",
    new_listings_gallery:
      state.audienceFilter && state.audienceFilter !== "all"
        ? state.audienceFilterName || "New Listings"
        : "New Listings",
    closed: "Closed Sales",
    inventory: "Inventory Report",
    price_bands: "Price Analysis",
    open_houses: "Open Houses",
  }

  const label = reportLabels[state.reportType]
  const area = getAreaDisplay(state) || "Your Area"

  return `📊 Your ${label} for ${area} is Ready!`
}
