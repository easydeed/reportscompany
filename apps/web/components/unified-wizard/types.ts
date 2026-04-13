export type AudienceFilter = "all" | "first_time" | "luxury" | "families" | "condo" | "investors"

export type DeliveryMode = "send_now" | "schedule"
export type Cadence = "weekly" | "biweekly" | "monthly" | "quarterly"

export type Recipient =
  | { type: "contact"; id: string; name: string; email: string }
  | { type: "group"; id: string; name: string; memberCount: number }
  | { type: "manual_email"; email: string }

export interface WizardState {
  reportType: string | null
  audience: AudienceFilter
  areaType: "city" | "zip"
  city: string | null
  zipCodes: string[]
  lookbackDays: 7 | 14 | 30 | 60 | 90 | null
  deliveryMode: DeliveryMode
  downloadPdf: boolean
  sendViaEmail: boolean
  recipientEmails: string[]
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
  reportType: null,
  audience: "all",
  areaType: "city",
  city: null,
  zipCodes: [],
  lookbackDays: null,
  deliveryMode: "send_now",
  downloadPdf: true,
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

// ─── Report Types ───

export interface ReportTypeConfig {
  id: string
  title: string
  description: string
  icon: string
  category: "gallery" | "data" | "analytics"
  defaultLookback: 7 | 14 | 30 | 60 | 90
  hasAudienceStep: boolean
}

export const REPORT_TYPES: ReportTypeConfig[] = [
  {
    id: "new_listings_gallery",
    title: "New Listings Gallery",
    description: "Photo gallery of the newest homes hitting the market. Great for buyer prospecting and social media.",
    icon: "image",
    category: "gallery",
    defaultLookback: 14,
    hasAudienceStep: true,
  },
  {
    id: "featured_listings",
    title: "Featured Listings",
    description: "Showcase your top active listings with large premium photo cards. Ideal for listing agents and social posts.",
    icon: "award",
    category: "gallery",
    defaultLookback: 90,
    hasAudienceStep: false,
  },
  {
    id: "open_houses",
    title: "Open Houses",
    description: "This weekend\u2019s open houses with times, photos, and details. Send to your buyer list before the weekend.",
    icon: "calendar-clock",
    category: "gallery",
    defaultLookback: 7,
    hasAudienceStep: false,
  },
  {
    id: "closed",
    title: "Closed Sales",
    description: "Recently sold homes with prices, days on market, and a detailed sales data table. Perfect for seller prospecting.",
    icon: "badge-dollar-sign",
    category: "data",
    defaultLookback: 30,
    hasAudienceStep: true,
  },
  {
    id: "inventory",
    title: "Active Inventory",
    description: "What\u2019s currently on the market \u2014 active listings, supply levels, pricing trends, and months of inventory.",
    icon: "building-2",
    category: "data",
    defaultLookback: 30,
    hasAudienceStep: true,
  },
  {
    id: "market_snapshot",
    title: "Market Snapshot",
    description: "The full picture \u2014 median prices, inventory, days on market, list-to-sale ratio, and AI-powered market analysis.",
    icon: "trending-up",
    category: "analytics",
    defaultLookback: 30,
    hasAudienceStep: false,
  },
  {
    id: "price_bands",
    title: "Price Bands",
    description: "Market activity broken down by price segment \u2014 see where buyers and sellers are most active in your city.",
    icon: "bar-chart-3",
    category: "analytics",
    defaultLookback: 30,
    hasAudienceStep: false,
  },
  {
    id: "new_listings",
    title: "New Listings Analytics",
    description: "New inventory trends with detailed property rows, pricing analysis, and Low/Median/High comparisons.",
    icon: "list-ordered",
    category: "analytics",
    defaultLookback: 30,
    hasAudienceStep: true,
  },
]

// ─── Audience cards metadata ───

export const AUDIENCES: {
  id: AudienceFilter
  label: string
  description: string
}[] = [
  { id: "all", label: "All Listings", description: "Show all homes \u2014 no price or size filters" },
  { id: "first_time", label: "First-Time Buyers", description: "Affordable single-family homes under 70% of local median price (2+ bed, 2+ bath)" },
  { id: "luxury", label: "Luxury Homes", description: "Premium single-family homes priced above 150% of local median" },
  { id: "families", label: "Family Homes", description: "Spacious family homes with 3+ bedrooms and 2+ bathrooms" },
  { id: "condo", label: "Condo Watch", description: "All condominiums and townhomes in the area" },
  { id: "investors", label: "Investor Deals", description: "Budget-friendly homes under 50% of local median \u2014 ideal for investors" },
]

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

// ─── Helpers ───

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
