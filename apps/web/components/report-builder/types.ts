import { BarChart3, Camera, Home, Package, DollarSign, DoorOpen } from "lucide-react"
import type { LucideIcon } from "lucide-react"

export type ReportType = 
  | "market_snapshot" 
  | "new_listings_gallery" 
  | "closed" 
  | "inventory" 
  | "price_bands" 
  | "open_houses"

export type LookbackDays = 7 | 14 | 30 | 60 | 90

export type AreaType = "city" | "zip"

export type AudienceFilter = "all" | "first_time" | "luxury" | "families" | "condo" | "investors" | null

export interface EmailRecipient {
  type: "contact" | "manual_email"
  id?: string
  name?: string
  email: string
}

export interface ReportBuilderState {
  reportType: ReportType
  lookbackDays: LookbackDays
  areaType: AreaType
  city: string | null
  zipCodes: string[]
  audienceFilter: AudienceFilter
  audienceFilterName: string | null
  viewInBrowser: boolean
  downloadPdf: boolean
  downloadSocialImage: boolean
  sendViaEmail: boolean
  emailRecipients: EmailRecipient[]
}

export type SectionStatus = "complete" | "warning" | "optional" | "incomplete"

// Branding context from /v1/account/branding
export interface BrandingContext {
  primaryColor: string
  accentColor: string
  pdfHeaderLogoUrl: string | null
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

// Report type configuration
export const REPORT_TYPE_CONFIG: Record<ReportType, { 
  label: string
  description: string
  icon: LucideIcon 
}> = {
  market_snapshot: { label: "Market Snapshot", description: "Stats & trends", icon: BarChart3 },
  new_listings_gallery: { label: "New Listings", description: "Photo gallery", icon: Camera },
  closed: { label: "Closed Sales", description: "Recently sold", icon: Home },
  inventory: { label: "Inventory Report", description: "Available now", icon: Package },
  price_bands: { label: "Price Analysis", description: "Price distribution", icon: DollarSign },
  open_houses: { label: "Open Houses", description: "Upcoming events", icon: DoorOpen },
}

export const LOOKBACK_OPTIONS: LookbackDays[] = [7, 14, 30, 60, 90]

export const AUDIENCE_FILTERS = [
  { value: "all" as const, label: "All Listings", description: "No filters - show everything" },
  { value: "first_time" as const, label: "First-Time Buyers", description: "2+ beds, 2+ baths, SFR, ≤70% median price" },
  { value: "luxury" as const, label: "Luxury Clients", description: "SFR, ≥150% median price" },
  { value: "families" as const, label: "Families", description: "3+ beds, 2+ baths, SFR" },
  { value: "condo" as const, label: "Condo Buyers", description: "Condos only" },
  { value: "investors" as const, label: "Investors", description: "≤50% median price" },
]

export const DELIVERY_OPTIONS = [
  {
    key: "viewInBrowser" as const,
    label: "View in Browser",
    description: "Open the interactive web report",
    icon: "🌐",
  },
  {
    key: "downloadPdf" as const,
    label: "Download PDF",
    description: "High-quality PDF for printing or sharing",
    icon: "📄",
  },
  {
    key: "downloadSocialImage" as const,
    label: "Download Social Image",
    description: "Instagram/Facebook story-sized image",
    icon: "📱",
  },
  {
    key: "sendViaEmail" as const,
    label: "Send via Email",
    description: "Email the report to specific recipients",
    icon: "📧",
  },
]

// API payload mapping for report generation
export interface ReportApiPayload {
  report_type: string
  city: string | null
  zip_codes: string[] | null
  lookback_days: number
  filters?: {
    minbeds?: number
    minbaths?: number
    subtype?: string
    price_strategy?: { mode: string; value: number }
    preset_display_name?: string
  } | null
}

// Map UI audience filter to API filters
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

// Helper functions
export function getAreaDisplay(state: ReportBuilderState): string {
  if (state.areaType === "city" && state.city) {
    return state.city
  }
  if (state.areaType === "zip" && state.zipCodes.length > 0) {
    if (state.zipCodes.length === 1) return `ZIP ${state.zipCodes[0]}`
    if (state.zipCodes.length <= 3) return `ZIPs ${state.zipCodes.join(", ")}`
    return `${state.zipCodes.length} ZIP codes`
  }
  return ""
}

export function getReportTitle(state: ReportBuilderState): string {
  const config = REPORT_TYPE_CONFIG[state.reportType]
  if (state.reportType === "new_listings_gallery" && state.audienceFilterName && state.audienceFilter !== "all") {
    return state.audienceFilterName
  }
  return config.label
}

