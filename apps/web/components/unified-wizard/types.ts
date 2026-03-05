export type StoryType =
  | "just_listed"
  | "just_sold"
  | "market_update"
  | "whats_available"
  | "showcase"

export type AudienceFilter = "all" | "first_time" | "luxury" | "families" | "condo" | "investors"

export type DeliveryMode = "send_now" | "schedule"
export type Cadence = "weekly" | "biweekly" | "monthly" | "quarterly"

export type Recipient =
  | { type: "contact"; id: string; name: string; email: string }
  | { type: "group"; id: string; name: string; memberCount: number }
  | { type: "manual_email"; email: string }

export interface WizardState {
  story: StoryType | null
  audience: AudienceFilter
  areaType: "city" | "zip"
  city: string | null
  zipCodes: string[]
  lookbackDays: 7 | 14 | 30 | 60 | 90 | null
  deliveryMode: DeliveryMode
  // Send now
  viewInBrowser: boolean
  downloadPdf: boolean
  sendViaEmail: boolean
  recipientEmails: string[]
  // Schedule
  scheduleName: string
  cadence: Cadence
  dayOfWeek: number
  dayOfMonth: number
  sendHour: number
  sendMinute: number
  timezone: string
  recipients: Recipient[]
}

export const INITIAL_STATE: WizardState = {
  story: null,
  audience: "all",
  areaType: "city",
  city: null,
  zipCodes: [],
  lookbackDays: null,
  deliveryMode: "send_now",
  viewInBrowser: true,
  downloadPdf: false,
  sendViaEmail: false,
  recipientEmails: [],
  scheduleName: "",
  cadence: "weekly",
  dayOfWeek: 1,
  dayOfMonth: 1,
  sendHour: 9,
  sendMinute: 0,
  timezone: "America/Los_Angeles",
  recipients: [],
}

// ─── Story → report_type mapping ───

export const STORY_TO_REPORT_TYPE: Record<StoryType, string> = {
  just_listed: "new_listings_gallery",
  just_sold: "closed",
  market_update: "market_snapshot",
  whats_available: "inventory",
  showcase: "featured_listings",
}

// ─── Story → default lookback ───

export const STORY_DEFAULT_LOOKBACK: Record<StoryType, 7 | 14 | 30 | 60 | 90> = {
  just_listed: 14,
  just_sold: 30,
  market_update: 30,
  whats_available: 30,
  showcase: 90,
}

// ─── Story cards metadata ───

export const STORIES: {
  id: StoryType
  title: string
  description: string
  bestFor: string
  icon: string
}[] = [
  {
    id: "just_listed",
    title: "What Just Listed",
    description: "Photo gallery of newest homes on the market",
    bestFor: "Buyer drips, prospecting",
    icon: "🏠",
  },
  {
    id: "just_sold",
    title: "What Just Sold",
    description: "Recent sales with prices, DOM & a data table",
    bestFor: "Seller prospecting, CMAs",
    icon: "💰",
  },
  {
    id: "market_update",
    title: "Market Update",
    description: "Median prices, inventory levels, trends — the full picture",
    bestFor: "Monthly sphere updates",
    icon: "📊",
  },
  {
    id: "whats_available",
    title: "What's Available",
    description: "Active listings, supply levels, inventory months",
    bestFor: "Buyer coaching, investors",
    icon: "📦",
  },
  {
    id: "showcase",
    title: "Showcase My Listings",
    description: "Your top 4 most impressive active listings",
    bestFor: "Listing agents, luxury",
    icon: "⭐",
  },
]

// ─── Audience cards metadata ───

export const AUDIENCES: {
  id: AudienceFilter
  label: string
  description: string
}[] = [
  { id: "all", label: "All Listings", description: "No filters applied" },
  { id: "first_time", label: "First-Time Buyers", description: "2+ bed, 2+ bath, SFR, ≤70% median" },
  { id: "luxury", label: "Luxury Homes", description: "SFR, ≥150% median" },
  { id: "families", label: "Family Homes", description: "3+ bed, 2+ bath, SFR" },
  { id: "condo", label: "Condo Watch", description: "Condos only" },
  { id: "investors", label: "Investor Deals", description: "≤50% median" },
]

// Audience → API filters
export const AUDIENCE_FILTER_PRESETS: Record<string, {
  minbeds?: number
  minbaths?: number
  subtype?: string
  price_strategy?: { mode: string; value: number }
  preset_display_name: string
}> = {
  first_time: { minbeds: 2, minbaths: 2, subtype: "SingleFamilyResidence", price_strategy: { mode: "maxprice_pct_of_median_list", value: 0.70 }, preset_display_name: "First-Time Buyer" },
  luxury: { subtype: "SingleFamilyResidence", price_strategy: { mode: "minprice_pct_of_median_list", value: 1.50 }, preset_display_name: "Luxury" },
  families: { minbeds: 3, minbaths: 2, subtype: "SingleFamilyResidence", preset_display_name: "Family Homes" },
  condo: { subtype: "Condominium", preset_display_name: "Condo Watch" },
  investors: { price_strategy: { mode: "maxprice_pct_of_median_list", value: 0.50 }, preset_display_name: "Investor Deals" },
}

// ─── Preview mapping ───

export function getPreviewReportType(story: StoryType | null) {
  if (!story) return "market_snapshot" as const
  const map: Record<StoryType, string> = {
    just_listed: "new_listings_gallery",
    just_sold: "closed",
    market_update: "market_snapshot",
    whats_available: "inventory",
    showcase: "featured_listings",
  }
  return map[story] as "market_snapshot" | "new_listings_gallery" | "closed" | "inventory" | "featured_listings"
}

export function getAudienceLabel(audience: AudienceFilter): string | null {
  if (audience === "all") return null
  return AUDIENCES.find((a) => a.id === audience)?.label || null
}

export function getAreaDisplay(state: WizardState): string {
  if (state.city) return state.city
  if (state.zipCodes.length === 1) return `ZIP ${state.zipCodes[0]}`
  if (state.zipCodes.length <= 3) return `ZIPs ${state.zipCodes.join(", ")}`
  if (state.zipCodes.length > 0) return `${state.zipCodes.length} ZIP codes`
  return "Your Area"
}
