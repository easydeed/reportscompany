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
  cadence: "weekly" | "monthly"
  weeklyDow: 0 | 1 | 2 | 3 | 4 | 5 | 6
  monthlyDom: number
  sendHour: number
  sendMinute: number
  timezone: string
  recipients: Recipient[]
  includeAttachment: boolean
}

export type SectionStatus = "complete" | "warning" | "optional"

// API payload mapping for schedule creation
export interface ScheduleApiPayload {
  name: string
  report_type: string
  city: string | null
  zip_codes: string[] | null
  lookback_days: number
  cadence: string
  weekly_dow: number | null
  monthly_dom: number | null
  send_hour: number
  send_minute: number
  timezone: string
  recipients: Array<{ type: string; id?: string; email?: string }>
  include_attachment: boolean
  active: boolean
  filters: {
    minbeds?: number
    minbaths?: number
    minprice?: number
    maxprice?: number
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

