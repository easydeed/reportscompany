"use client"

import type { 
  ReportBuilderState, 
  ReportType, 
  BrandingContext, 
  ProfileContext 
} from "./types"

interface ReportPreviewProps {
  state: ReportBuilderState
  branding: BrandingContext
  profile: ProfileContext
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

function getAreaDisplay(state: ReportBuilderState): string {
  if (state.areaType === "city" && state.city) return state.city
  if (state.areaType === "zip" && state.zipCodes.length > 0) {
    if (state.zipCodes.length === 1) return `ZIP ${state.zipCodes[0]}`
    return `${state.zipCodes.length} ZIP codes`
  }
  return "Select an area"
}

function getReportTitle(state: ReportBuilderState): string {
  if (!state.reportType) return "Select Report Type"
  if (state.reportType === "new_listings_gallery" && state.audienceFilterName && state.audienceFilter !== "all") {
    return state.audienceFilterName
  }
  const titles: Record<ReportType, string> = {
    market_snapshot: "Market Update",
    new_listings_gallery: "New Listings",
    closed: "Closed Sales",
    inventory: "Inventory Report",
    price_bands: "Price Analysis",
    open_houses: "Open Houses",
  }
  return titles[state.reportType]
}

export function ReportPreview({ state, branding, profile }: ReportPreviewProps) {
  const areaDisplay = getAreaDisplay(state)
  const reportTitle = getReportTitle(state)

  return (
    <div className="space-y-4">
      {/* Report Mockup - This is where gradients ARE allowed (it's the preview) */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        {/* Header with Gradient (allowed in preview) */}
        <div 
          className="px-5 py-6 text-center text-white"
          style={{
            background: `linear-gradient(135deg, ${branding.primaryColor} 0%, ${branding.accentColor} 100%)`,
          }}
        >
          {branding.pdfHeaderLogoUrl ? (
            <img 
              src={branding.pdfHeaderLogoUrl} 
              alt={branding.displayName || "Logo"}
              className="mx-auto mb-3 h-6 w-auto"
            />
          ) : (
            <div className="mb-2 text-xs font-semibold opacity-90">
              {branding.displayName || "TrendyReports"}
            </div>
          )}
          <h2 className="text-lg font-bold">{reportTitle}</h2>
          <p className="mt-1 text-sm opacity-90">{areaDisplay}</p>
          <div className="mt-2 inline-block rounded-full bg-white/20 px-3 py-1 text-xs">
            Last {state.lookbackDays || 30} days
          </div>
        </div>

        {/* Content based on report type */}
        <div className="p-4">
          <ReportContent 
            reportType={state.reportType} 
            primaryColor={branding.primaryColor}
            accentColor={branding.accentColor}
          />
        </div>

        {/* Agent Footer */}
        <div className="border-t border-gray-100 bg-gray-50 px-4 py-3">
          <div className="flex items-center gap-3">
            <div 
              className="h-10 w-10 rounded-full flex items-center justify-center text-sm font-semibold text-white overflow-hidden"
              style={{ backgroundColor: branding.primaryColor }}
            >
              {profile.avatarUrl ? (
                <img src={profile.avatarUrl} alt={profile.name} className="w-full h-full object-cover" />
              ) : (
                profile.name?.charAt(0) || "?"
              )}
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-medium text-sm text-gray-900">{profile.name}</p>
              <p className="text-xs text-gray-500">
                {[profile.phone, profile.email].filter(Boolean).join(" · ")}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Info Summary */}
      <div className="text-center text-xs text-gray-500">
        {reportTitle} · {areaDisplay} · Last {state.lookbackDays || 30} days
      </div>
    </div>
  )
}

function ReportContent({ reportType, primaryColor, accentColor }: { reportType: ReportType; primaryColor: string; accentColor: string }) {
  switch (reportType) {
    case "market_snapshot":
      return (
        <div className="space-y-4">
          <div className="text-center py-2">
            <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Median Sale Price</p>
            <p className="text-3xl font-bold mt-1" style={{ color: primaryColor }}>$1,150,000</p>
            <p className="text-xs text-green-600 font-medium mt-1">↑ 4.2% vs last month</p>
          </div>
          
          <div className="grid grid-cols-4 gap-2">
            {[
              { label: "Closed", value: "42" },
              { label: "Avg DOM", value: "24" },
              { label: "MOI", value: "2.4" },
              { label: "Pending", value: "18" },
            ].map((stat) => (
              <div key={stat.label} className="rounded-lg bg-gray-50 p-2 text-center">
                <p className="text-lg font-bold text-gray-900">{stat.value}</p>
                <p className="text-[10px] text-gray-500">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      )

    case "new_listings_gallery":
      return (
        <div className="space-y-4">
          <div className="text-center py-2">
            <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">New Listings</p>
            <p className="text-3xl font-bold mt-1" style={{ color: primaryColor }}>127</p>
          </div>

          <div className="grid grid-cols-3 gap-2">
            {[
              { label: "Median", value: "$985K" },
              { label: "Starting", value: "$425K" },
              { label: "Up To", value: "$2.8M" },
            ].map((stat) => (
              <div key={stat.label} className="rounded-lg bg-gray-50 p-2 text-center">
                <p className="text-base font-bold text-gray-900">{stat.value}</p>
                <p className="text-[10px] text-gray-500">{stat.label}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-3 gap-1.5">
            {SAMPLE_PHOTOS.slice(0, 6).map((photo, i) => (
              <div key={i} className="relative aspect-[4/3] rounded overflow-hidden bg-gray-100">
                <img src={photo} alt={`Property ${i + 1}`} className="w-full h-full object-cover" />
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-1.5">
                  <p className="text-white text-[10px] font-semibold">${(650 + i * 125)}K</p>
                </div>
              </div>
            ))}
          </div>
          <p className="text-center text-[10px] text-gray-400">+ 121 more listings</p>
        </div>
      )

    case "closed":
      return (
        <div className="space-y-4">
          <div className="text-center py-2">
            <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Closed Sales</p>
            <p className="text-3xl font-bold mt-1" style={{ color: primaryColor }}>42</p>
            <p className="text-xs text-gray-500 mt-1">$48.5M Total Volume</p>
          </div>

          <div className="grid grid-cols-3 gap-2">
            {[
              { label: "Median", value: "$1.08M" },
              { label: "Avg DOM", value: "18" },
              { label: "Close-List", value: "98.2%" },
            ].map((stat) => (
              <div key={stat.label} className="rounded-lg bg-gray-50 p-2 text-center">
                <p className="text-base font-bold text-gray-900">{stat.value}</p>
                <p className="text-[10px] text-gray-500">{stat.label}</p>
              </div>
            ))}
          </div>

          <div className="space-y-1.5">
            {[
              { addr: "123 Oak Street", price: "$1,275,000", dom: "12" },
              { addr: "456 Maple Lane", price: "$985,000", dom: "8" },
              { addr: "789 Palm Avenue", price: "$1,450,000", dom: "21" },
            ].map((sale, i) => (
              <div key={i} className="flex items-center justify-between rounded bg-gray-50 px-2 py-1.5">
                <span className="text-xs text-gray-700">{sale.addr}</span>
                <div className="text-right">
                  <span className="text-xs font-semibold" style={{ color: primaryColor }}>{sale.price}</span>
                  <span className="text-[10px] text-gray-400 ml-1">{sale.dom}d</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )

    case "inventory":
      return (
        <div className="space-y-4">
          <div className="text-center py-2">
            <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Active Inventory</p>
            <p className="text-3xl font-bold mt-1" style={{ color: primaryColor }}>127</p>
          </div>

          <div className="grid grid-cols-3 gap-2">
            {[
              { label: "New", value: "+23", color: "text-green-600" },
              { label: "Median DOM", value: "24" },
              { label: "MOI", value: "2.4" },
            ].map((stat) => (
              <div key={stat.label} className="rounded-lg bg-gray-50 p-2 text-center">
                <p className={`text-base font-bold ${stat.color || "text-gray-900"}`}>{stat.value}</p>
                <p className="text-[10px] text-gray-500">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      )

    case "price_bands":
      return (
        <div className="space-y-4">
          <div className="text-center py-2">
            <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Median List Price</p>
            <p className="text-3xl font-bold mt-1" style={{ color: primaryColor }}>$985K</p>
          </div>

          <div className="space-y-2">
            {[
              { label: "Entry Level", range: "Under $750K", count: 18, pct: 14 },
              { label: "Move-Up", range: "$750K - $1.2M", count: 52, pct: 41 },
              { label: "Premium", range: "$1.2M - $2M", count: 38, pct: 30 },
              { label: "Luxury", range: "Over $2M", count: 19, pct: 15 },
            ].map((band, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="w-20 text-gray-500">{band.label}</span>
                <div className="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden">
                  <div 
                    className="h-full rounded-full" 
                    style={{ width: `${band.pct}%`, backgroundColor: primaryColor, opacity: 0.5 + (i * 0.15) }} 
                  />
                </div>
                <span className="w-8 text-right font-semibold text-gray-700">{band.count}</span>
              </div>
            ))}
          </div>
        </div>
      )

    case "open_houses":
      return (
        <div className="space-y-4">
          <div className="text-center py-2">
            <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Open Houses This Weekend</p>
            <p className="text-3xl font-bold mt-1" style={{ color: primaryColor }}>15</p>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-lg p-3 text-center" style={{ backgroundColor: `${primaryColor}15` }}>
              <p className="text-xl font-bold" style={{ color: primaryColor }}>8</p>
              <p className="text-xs text-gray-600">Saturday</p>
            </div>
            <div className="rounded-lg p-3 text-center" style={{ backgroundColor: `${accentColor}15` }}>
              <p className="text-xl font-bold" style={{ color: accentColor }}>7</p>
              <p className="text-xs text-gray-600">Sunday</p>
            </div>
          </div>
        </div>
      )

    default:
      return null
  }
}
