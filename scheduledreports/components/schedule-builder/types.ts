export type ReportType = "new_listings" | "market_update" | "closed_sales" | "inventory" | "price_bands" | "open_houses"

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
