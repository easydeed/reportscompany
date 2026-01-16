"use client"

import { Calendar, MapPin, Clock, Eye } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { ScheduleBuilderState } from "./types"

interface PreviewPanelProps {
  state: ScheduleBuilderState
}

const reportTypeLabels: Record<string, { icon: string; label: string }> = {
  new_listings: { icon: "📸", label: "New Listings" },
  market_update: { icon: "📊", label: "Market Update" },
  closed_sales: { icon: "🏠", label: "Closed Sales" },
  inventory: { icon: "📦", label: "Inventory" },
  price_bands: { icon: "💰", label: "Price Bands" },
  open_houses: { icon: "🚪", label: "Open Houses" },
}

const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

export function PreviewPanel({ state }: PreviewPanelProps) {
  const reportInfo = reportTypeLabels[state.reportType]
  const scheduleName = state.name || "Untitled Schedule"
  const areaDisplay =
    state.areaType === "city"
      ? state.city || "Select an area"
      : state.zipCodes.length > 0
        ? `${state.zipCodes.length} ZIP codes`
        : "Select an area"

  const cadenceText =
    state.cadence === "weekly"
      ? `Every ${dayNames[state.weeklyDow]}`
      : `Monthly on the ${state.monthlyDom}${getOrdinalSuffix(state.monthlyDom)}`

  const timeText = `${state.sendHour.toString().padStart(2, "0")}:${state.sendMinute.toString().padStart(2, "0")}`
  const timezoneShort = state.timezone === "America/Los_Angeles" ? "PT" : "ET"

  // Calculate next send date
  const nextSendDate = getNextSendDate(state)

  return (
    <div className="sticky top-24">
      <div className="rounded-xl border bg-background shadow-sm">
        {/* Header */}
        <div className="border-b px-4 py-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">REPORT PREVIEW</span>
            <span className="text-xs text-muted-foreground">Updates as you configure</span>
          </div>
        </div>

        {/* Preview Content */}
        <div className="p-4">
          <div className="rounded-lg border bg-muted/30">
            {/* Report Header */}
            <div className="rounded-t-lg bg-violet-600 px-4 py-4 text-white">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{reportInfo.icon}</span>
                <div>
                  <div className="text-sm font-medium opacity-90">{reportInfo.label}</div>
                  <div className="text-lg font-semibold">{scheduleName}</div>
                </div>
              </div>
            </div>

            {/* Meta Info */}
            <div className="flex items-center gap-4 border-b px-4 py-3 text-sm">
              <div className="flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                <span>{areaDisplay}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                <span>Last {state.lookbackDays} days</span>
              </div>
            </div>

            {/* Report Type Specific Content */}
            <div className="p-4">
              <ReportPreviewContent reportType={state.reportType} />
            </div>

            {/* View Full Report Button */}
            <div className="px-4 pb-4">
              <Button
                variant="outline"
                className="w-full text-violet-600 border-violet-200 hover:bg-violet-50 bg-transparent"
              >
                View Full Report →
              </Button>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between rounded-b-lg border-t bg-muted/50 px-4 py-3 text-xs text-muted-foreground">
              <div className="flex items-center gap-1.5 font-medium">
                <span className="text-violet-600">TR</span>
                <span>TrendyReports</span>
              </div>
              <span>Sent {cadenceText.toLowerCase()}</span>
            </div>
          </div>
        </div>

        {/* Next Send Info */}
        <div className="border-t px-4 py-3">
          <div className="flex items-center gap-2 rounded-lg bg-violet-50 px-3 py-2 text-sm">
            <Clock className="h-4 w-4 text-violet-600" />
            <span className="text-violet-900">
              Next send: {nextSendDate} at {timeText} {timezoneShort}
            </span>
          </div>
        </div>

        {/* Preview Full Report Button */}
        <div className="border-t px-4 py-3">
          <Button variant="outline" className="w-full gap-2 bg-transparent">
            <Eye className="h-4 w-4" />
            Preview Full Report
          </Button>
        </div>
      </div>
    </div>
  )
}

function ReportPreviewContent({ reportType }: { reportType: string }) {
  switch (reportType) {
    case "market_update":
      return (
        <div className="grid grid-cols-2 gap-3">
          <StatCard label="Median Price" value="$1.15M" change="+4.2%" positive />
          <StatCard label="Active Listings" value="127" change="-8%" positive={false} />
          <StatCard label="Avg Days on Market" value="24 days" change="-3 days" positive />
          <StatCard label="Sold Last Month" value="42" change="+12%" positive />
        </div>
      )
    case "new_listings":
      return (
        <div className="space-y-2">
          <ListingCard address="123 Oak Street" price="$1,250,000" beds={4} baths={3} sqft="2,450" />
          <ListingCard address="456 Maple Ave" price="$985,000" beds={3} baths={2} sqft="1,850" />
          <div className="pt-2 text-center text-sm text-violet-600">View All Listings →</div>
        </div>
      )
    case "closed_sales":
      return (
        <div className="space-y-3">
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="text-lg font-semibold">$1.08M</div>
              <div className="text-xs text-muted-foreground">Avg Sale Price</div>
            </div>
            <div>
              <div className="text-lg font-semibold">98.2%</div>
              <div className="text-xs text-muted-foreground">List-to-Sale</div>
            </div>
            <div>
              <div className="text-lg font-semibold">18 days</div>
              <div className="text-xs text-muted-foreground">Avg DOM</div>
            </div>
          </div>
        </div>
      )
    case "inventory":
      return (
        <div className="space-y-3">
          <div className="text-center">
            <div className="text-3xl font-bold text-violet-600">127</div>
            <div className="text-sm text-muted-foreground">Active Listings</div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center text-sm">
            <div className="rounded-lg bg-muted/50 p-2">
              <div className="font-medium">78</div>
              <div className="text-xs text-muted-foreground">SFR</div>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <div className="font-medium">42</div>
              <div className="text-xs text-muted-foreground">Condo</div>
            </div>
            <div className="rounded-lg bg-muted/50 p-2">
              <div className="font-medium">7</div>
              <div className="text-xs text-muted-foreground">Multi</div>
            </div>
          </div>
          <div className="text-center text-sm text-muted-foreground">2.4 months of supply</div>
        </div>
      )
    case "price_bands":
      return (
        <div className="space-y-2">
          <PriceBandBar label="Under $500K" value={12} max={50} />
          <PriceBandBar label="$500K-$750K" value={28} max={50} />
          <PriceBandBar label="$750K-$1M" value={45} max={50} />
          <PriceBandBar label="$1M-$1.5M" value={32} max={50} />
          <PriceBandBar label="$1.5M+" value={10} max={50} />
        </div>
      )
    case "open_houses":
      return (
        <div className="space-y-2">
          <OpenHouseCard address="789 Pine Ln" date="Sat, Jan 18" time="1-4 PM" price="$1,150,000" />
          <OpenHouseCard address="321 Cedar Rd" date="Sun, Jan 19" time="2-5 PM" price="$875,000" />
        </div>
      )
    default:
      return null
  }
}

function StatCard({
  label,
  value,
  change,
  positive,
}: {
  label: string
  value: string
  change: string
  positive: boolean
}) {
  return (
    <div className="rounded-lg border bg-background p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
      <div className={`text-xs ${positive ? "text-emerald-600" : "text-red-500"}`}>
        {positive ? "↑" : "↓"} {change}
      </div>
    </div>
  )
}

function ListingCard({
  address,
  price,
  beds,
  baths,
  sqft,
}: {
  address: string
  price: string
  beds: number
  baths: number
  sqft: string
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-background p-2">
      <div className="h-12 w-12 rounded bg-muted" />
      <div className="flex-1">
        <div className="text-sm font-medium">{price}</div>
        <div className="text-xs text-muted-foreground">{address}</div>
        <div className="text-xs text-muted-foreground">
          {beds} bd · {baths} ba · {sqft} sqft
        </div>
      </div>
    </div>
  )
}

function PriceBandBar({ label, value, max }: { label: string; value: number; max: number }) {
  const percentage = (value / max) * 100
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span>{label}</span>
        <span className="text-muted-foreground">{value}</span>
      </div>
      <div className="h-2 rounded-full bg-muted">
        <div className="h-full rounded-full bg-violet-500" style={{ width: `${percentage}%` }} />
      </div>
    </div>
  )
}

function OpenHouseCard({
  address,
  date,
  time,
  price,
}: {
  address: string
  date: string
  time: string
  price: string
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border bg-background p-2">
      <div>
        <div className="text-sm font-medium">{address}</div>
        <div className="text-xs text-muted-foreground">
          {date} · {time}
        </div>
      </div>
      <div className="text-sm font-medium text-violet-600">{price}</div>
    </div>
  )
}

function getOrdinalSuffix(n: number): string {
  const s = ["th", "st", "nd", "rd"]
  const v = n % 100
  return s[(v - 20) % 10] || s[v] || s[0]
}

function getNextSendDate(state: ScheduleBuilderState): string {
  const now = new Date()
  const targetDate = new Date(now)

  if (state.cadence === "weekly") {
    const currentDay = now.getDay()
    const daysUntilTarget = (state.weeklyDow - currentDay + 7) % 7 || 7
    targetDate.setDate(now.getDate() + daysUntilTarget)
  } else {
    if (now.getDate() >= state.monthlyDom) {
      targetDate.setMonth(now.getMonth() + 1)
    }
    targetDate.setDate(state.monthlyDom)
  }

  return targetDate.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  })
}
