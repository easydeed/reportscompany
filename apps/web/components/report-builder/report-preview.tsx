"use client"

import type { 
  ReportBuilderState, 
  ReportType, 
  BrandingContext, 
  ProfileContext 
} from "./types"
import { REPORT_TYPE_CONFIG, getAreaDisplay, getReportTitle } from "./types"

interface ReportPreviewProps {
  state: ReportBuilderState
  branding: BrandingContext
  profile: ProfileContext
  onPreview?: () => void
}

// Sample property images for realistic previews
const SAMPLE_PHOTOS = [
  "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=300&h=200&fit=crop",
  "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=300&h=200&fit=crop",
  "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=300&h=200&fit=crop",
  "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=300&h=200&fit=crop",
  "https://images.unsplash.com/photo-1583608205776-bfd35f0d9f83?w=300&h=200&fit=crop",
  "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=300&h=200&fit=crop",
]

const SAMPLE_ADDRESSES = [
  "123 Maple Dr",
  "456 Oak Lane",
  "789 Palm Ave",
  "321 Cedar Ct",
  "654 Birch Way",
  "987 Pine Rd",
]

export function ReportPreview({ state, branding, profile }: ReportPreviewProps) {
  const areaDisplay = getAreaDisplay(state)
  const reportTitle = getReportTitle(state)

  return (
    <div className="overflow-hidden rounded-lg border bg-white shadow-sm dark:bg-slate-950">
      {/* Header with Gradient */}
      <div 
        className="px-6 py-8 text-center text-white"
        style={{
          background: `linear-gradient(135deg, ${branding.primaryColor} 0%, ${branding.accentColor} 100%)`,
        }}
      >
        {branding.pdfHeaderLogoUrl ? (
          <img 
            src={branding.pdfHeaderLogoUrl} 
            alt={branding.displayName || "Logo"}
            className="mx-auto mb-4 h-8 w-auto"
          />
        ) : (
          <div className="mb-3 text-sm font-semibold opacity-90">
            {branding.displayName || "TrendyReports"}
          </div>
        )}
        <h2 className="text-xl font-bold">{reportTitle}</h2>
        {areaDisplay && <p className="mt-2 text-base opacity-95">{areaDisplay}</p>}
        <div className="mt-2 inline-block rounded-full bg-white/20 px-3 py-1 text-xs font-medium">
          Last {state.lookbackDays} Days • Live MLS Data
        </div>
      </div>

      {/* Content based on report type */}
      <div className="p-5">
        <ReportContent 
          reportType={state.reportType} 
          primaryColor={branding.primaryColor}
          accentColor={branding.accentColor}
        />
      </div>

      {/* Agent Footer */}
      <div className="border-t bg-slate-50 px-5 py-4 dark:bg-slate-900">
        <div className="flex items-center gap-4">
          <div 
            className="h-12 w-12 rounded-full flex items-center justify-center text-base font-semibold text-white overflow-hidden ring-2 ring-white shadow-md"
            style={{ backgroundColor: branding.primaryColor }}
          >
            {profile.avatarUrl ? (
              <img src={profile.avatarUrl} alt={profile.name} className="w-full h-full object-cover" />
            ) : (
              profile.name?.charAt(0) || "?"
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className="font-semibold text-sm">{profile.name}</p>
            <p className="text-xs text-muted-foreground">{profile.jobTitle || "Real Estate Agent"}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              {[profile.phone, profile.email].filter(Boolean).join(" • ")}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function ReportContent({ reportType, primaryColor, accentColor }: { reportType: ReportType; primaryColor: string; accentColor: string }) {
  switch (reportType) {
    case "market_snapshot":
      return (
        <div className="space-y-5">
          {/* Hero Metric */}
          <div className="text-center py-2">
            <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Median Sale Price</p>
            <p className="text-4xl font-bold mt-1" style={{ color: primaryColor }}>$1,150,000</p>
            <p className="text-sm text-emerald-600 font-medium mt-1">↑ 4.2% vs last month</p>
          </div>
          
          {/* Stats Grid */}
          <div className="grid grid-cols-4 gap-3">
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-2xl font-bold" style={{ color: primaryColor }}>42</p>
              <p className="text-[11px] text-muted-foreground font-medium">Closed Sales</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-2xl font-bold">24</p>
              <p className="text-[11px] text-muted-foreground font-medium">Avg DOM</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-2xl font-bold">2.4</p>
              <p className="text-[11px] text-muted-foreground font-medium">MOI</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-2xl font-bold">18</p>
              <p className="text-[11px] text-muted-foreground font-medium">Pending</p>
            </div>
          </div>

          {/* Mini Chart */}
          <div className="rounded-xl p-4" style={{ background: `linear-gradient(135deg, ${primaryColor}15, ${accentColor}10)` }}>
            <p className="text-xs font-semibold text-muted-foreground mb-2">Price Trend (6 months)</p>
            <div className="flex items-end gap-1 h-12">
              {[65, 72, 68, 80, 85, 92].map((h, i) => (
                <div key={i} className="flex-1 rounded-t" style={{ height: `${h}%`, backgroundColor: primaryColor, opacity: 0.3 + (i * 0.1) }} />
              ))}
            </div>
          </div>
        </div>
      )

    case "new_listings_gallery":
      return (
        <div className="space-y-5">
          {/* Hero Metric */}
          <div className="text-center py-2">
            <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">New Listings This Week</p>
            <p className="text-4xl font-bold mt-1" style={{ color: primaryColor }}>127</p>
          </div>

          {/* Stats Bar */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-lg font-bold" style={{ color: primaryColor }}>$985K</p>
              <p className="text-[11px] text-muted-foreground font-medium">Median Price</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-lg font-bold">$425K</p>
              <p className="text-[11px] text-muted-foreground font-medium">Starting From</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-lg font-bold">$2.8M</p>
              <p className="text-[11px] text-muted-foreground font-medium">Up To</p>
            </div>
          </div>

          {/* Property Grid */}
          <div className="grid grid-cols-3 gap-2">
            {SAMPLE_PHOTOS.slice(0, 6).map((photo, i) => (
              <div key={i} className="relative aspect-[4/3] rounded-lg overflow-hidden bg-slate-100">
                <img src={photo} alt={`Property ${i + 1}`} className="w-full h-full object-cover" />
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
                  <p className="text-white text-xs font-semibold">${(650 + i * 125)}K</p>
                </div>
              </div>
            ))}
          </div>
          <p className="text-center text-xs text-muted-foreground">+ 121 more listings</p>
        </div>
      )

    case "closed":
      return (
        <div className="space-y-5">
          {/* Hero Metric */}
          <div className="text-center py-2">
            <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Closed Sales</p>
            <p className="text-4xl font-bold mt-1" style={{ color: primaryColor }}>42</p>
            <p className="text-sm text-muted-foreground mt-1">$48.5M Total Volume</p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-lg font-bold" style={{ color: primaryColor }}>$1.08M</p>
              <p className="text-[11px] text-muted-foreground font-medium">Median Price</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-lg font-bold">18</p>
              <p className="text-[11px] text-muted-foreground font-medium">Avg DOM</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-lg font-bold">98.2%</p>
              <p className="text-[11px] text-muted-foreground font-medium">Close-to-List</p>
            </div>
          </div>

          {/* Recent Sales List */}
          <div className="space-y-2">
            <p className="text-xs font-semibold text-muted-foreground">Recent Closings</p>
            {[
              { addr: "123 Oak Street", price: "$1,275,000", dom: "12" },
              { addr: "456 Maple Lane", price: "$985,000", dom: "8" },
              { addr: "789 Palm Avenue", price: "$1,450,000", dom: "21" },
            ].map((sale, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2.5 dark:bg-slate-900">
                <span className="text-sm font-medium">{sale.addr}</span>
                <div className="text-right">
                  <span className="text-sm font-bold" style={{ color: primaryColor }}>{sale.price}</span>
                  <span className="text-xs text-muted-foreground ml-2">{sale.dom} DOM</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )

    case "inventory":
      return (
        <div className="space-y-5">
          {/* Hero Metric */}
          <div className="text-center py-2">
            <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Active Inventory</p>
            <p className="text-4xl font-bold mt-1" style={{ color: primaryColor }}>127</p>
            <p className="text-sm text-amber-600 font-medium mt-1">↓ 8 from last week</p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-lg font-bold text-emerald-600">+23</p>
              <p className="text-[11px] text-muted-foreground font-medium">New This Week</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-lg font-bold">24</p>
              <p className="text-[11px] text-muted-foreground font-medium">Median DOM</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-lg font-bold">2.4</p>
              <p className="text-[11px] text-muted-foreground font-medium">MOI</p>
            </div>
          </div>

          {/* Price Distribution */}
          <div className="space-y-2">
            <p className="text-xs font-semibold text-muted-foreground">Price Distribution</p>
            <div className="space-y-1.5">
              {[
                { label: "Under $750K", count: 18, pct: 14 },
                { label: "$750K - $1M", count: 34, pct: 27 },
                { label: "$1M - $1.5M", count: 45, pct: 35 },
                { label: "Over $1.5M", count: 30, pct: 24 },
              ].map((band, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <span className="w-24 text-muted-foreground">{band.label}</span>
                  <div className="flex-1 h-3 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div 
                      className="h-full rounded-full" 
                      style={{ width: `${band.pct}%`, backgroundColor: primaryColor, opacity: 0.5 + (i * 0.15) }} 
                    />
                  </div>
                  <span className="w-8 text-right font-semibold">{band.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )

    case "price_bands":
      return (
        <div className="space-y-5">
          {/* Hero Metric */}
          <div className="text-center py-2">
            <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Price Analysis</p>
            <p className="text-4xl font-bold mt-1" style={{ color: primaryColor }}>$985K</p>
            <p className="text-sm text-muted-foreground mt-1">Median List Price</p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-lg font-bold">$425K - $2.8M</p>
              <p className="text-[11px] text-muted-foreground font-medium">Price Range</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3 text-center dark:bg-slate-900">
              <p className="text-lg font-bold">$485</p>
              <p className="text-[11px] text-muted-foreground font-medium">Avg $/SqFt</p>
            </div>
          </div>

          {/* Price Bands */}
          <div className="space-y-3">
            <p className="text-xs font-semibold text-muted-foreground">Market Segments</p>
            {[
              { label: "Entry Level", range: "Under $750K", count: 18, color: "#22c55e" },
              { label: "Move-Up", range: "$750K - $1.2M", count: 52, color: primaryColor },
              { label: "Premium", range: "$1.2M - $2M", count: 38, color: accentColor },
              { label: "Luxury", range: "Over $2M", count: 19, color: "#f59e0b" },
            ].map((band, i) => (
              <div key={i} className="flex items-center gap-3 rounded-lg bg-slate-50 px-3 py-2.5 dark:bg-slate-900">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: band.color }} />
                <div className="flex-1">
                  <p className="text-sm font-semibold">{band.label}</p>
                  <p className="text-xs text-muted-foreground">{band.range}</p>
                </div>
                <p className="text-lg font-bold">{band.count}</p>
              </div>
            ))}
          </div>
        </div>
      )

    case "open_houses":
      return (
        <div className="space-y-5">
          {/* Hero Metric */}
          <div className="text-center py-2">
            <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Open Houses This Weekend</p>
            <p className="text-4xl font-bold mt-1" style={{ color: primaryColor }}>15</p>
          </div>

          {/* Day Split */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl p-4 text-center" style={{ backgroundColor: `${primaryColor}15` }}>
              <p className="text-3xl font-bold" style={{ color: primaryColor }}>8</p>
              <p className="text-sm font-medium">Saturday</p>
              <p className="text-xs text-muted-foreground">Jan 18</p>
            </div>
            <div className="rounded-xl p-4 text-center" style={{ backgroundColor: `${accentColor}15` }}>
              <p className="text-3xl font-bold" style={{ color: accentColor }}>7</p>
              <p className="text-sm font-medium">Sunday</p>
              <p className="text-xs text-muted-foreground">Jan 19</p>
            </div>
          </div>

          {/* Open House List */}
          <div className="space-y-2">
            <p className="text-xs font-semibold text-muted-foreground">Featured Open Houses</p>
            {[
              { addr: "123 Oak St", time: "Sat 1-4pm", price: "$1.2M" },
              { addr: "456 Maple Ln", time: "Sun 2-5pm", price: "$985K" },
              { addr: "789 Palm Ave", time: "Sat & Sun 12-3pm", price: "$1.45M" },
            ].map((oh, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2.5 dark:bg-slate-900">
                <div>
                  <p className="text-sm font-medium">{oh.addr}</p>
                  <p className="text-xs text-muted-foreground">{oh.time}</p>
                </div>
                <p className="text-sm font-bold" style={{ color: primaryColor }}>{oh.price}</p>
              </div>
            ))}
          </div>
        </div>
      )

    default:
      return null
  }
}

