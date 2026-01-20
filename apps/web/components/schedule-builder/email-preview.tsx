"use client"

import type {
  ScheduleBuilderState,
  BrandingContext,
  ProfileContext,
} from "./types"
import { REPORT_TYPE_LABELS } from "./types"

interface EmailPreviewProps {
  state: ScheduleBuilderState
  branding: BrandingContext
  profile: ProfileContext
  area: string
}

// Sample property images
const SAMPLE_PHOTOS = [
  "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=200&h=150&fit=crop",
  "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=200&h=150&fit=crop",
  "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=200&h=150&fit=crop",
  "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=200&h=150&fit=crop",
  "https://images.unsplash.com/photo-1583608205776-bfd35f0d9f83?w=200&h=150&fit=crop",
  "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=200&h=150&fit=crop",
]

export function EmailPreview({ state, branding, profile, area }: EmailPreviewProps) {
  const getReportLabel = () => {
    if (!state.reportType) return "Report"
    return REPORT_TYPE_LABELS[state.reportType] || "Report"
  }

  const getHeaderTitle = () => {
    if (state.reportType === "new_listings_gallery" && state.audienceFilter && state.audienceFilter !== "all") {
      return `${state.audienceFilterName || "New Listings"} – ${area || "Your Area"}`
    }
    return `${getReportLabel()} – ${area || "Your Area"}`
  }

  return (
    <div className="mx-auto font-sans text-sm">
      {/* Email Header - Gradient allowed in preview */}
      <div
        className="rounded-t-lg px-5 py-6 text-center text-white"
        style={{
          background: `linear-gradient(135deg, ${branding.primaryColor} 0%, ${branding.accentColor} 100%)`,
        }}
      >
        {branding.emailLogoUrl ? (
          <img 
            src={branding.emailLogoUrl} 
            alt={branding.displayName || "Logo"}
            className="mx-auto mb-3 h-6 w-auto"
          />
        ) : (
          <div className="mb-3 text-xs font-semibold opacity-90">
            {branding.displayName || "TrendyReports"}
          </div>
        )}
        <div className="inline-block bg-white/20 px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wide mb-1">
          {getReportLabel()}
        </div>
        <h1 className="text-base font-bold">{getHeaderTitle()}</h1>
        <p className="text-[10px] opacity-90 mt-1">Last {state.lookbackDays || 30} days • Live MLS Data</p>
      </div>

      {/* Email Body */}
      <div className="bg-white p-4 border-x border-gray-200">
        <div className="bg-gray-50 border border-gray-200 rounded p-2 mb-4 text-xs text-gray-600">
          The {area || "selected area"} market showed strong activity this period with median prices holding steady.
        </div>

        <ReportContent state={state} branding={branding} />

        <div className="text-center my-4">
          <button
            className="inline-block px-4 py-2 rounded text-white text-xs font-semibold"
            style={{ backgroundColor: branding.primaryColor }}
          >
            View Full Report →
          </button>
        </div>

        {/* Agent Footer */}
        <div className="flex items-center gap-3 pt-4 mt-4 border-t border-gray-200">
          <div
            className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-sm overflow-hidden"
            style={{ border: `2px solid ${branding.primaryColor}` }}
          >
            {profile.avatarUrl ? (
              <img src={profile.avatarUrl} alt={profile.name} className="w-full h-full object-cover" />
            ) : (
              <span className="text-gray-500 font-medium">{profile.name?.charAt(0) || "?"}</span>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className="font-semibold text-sm text-gray-900">{profile.name}</p>
            {profile.jobTitle && <p className="text-[10px] text-gray-500">{profile.jobTitle}</p>}
            <p className="text-[10px]" style={{ color: branding.primaryColor }}>
              {[profile.phone, profile.email].filter(Boolean).join(" • ")}
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-50 rounded-b-lg px-4 py-3 text-center text-[10px] text-gray-500 border border-t-0 border-gray-200">
        Powered by {branding.displayName || "TrendyReports"} • <span className="underline cursor-pointer">Unsubscribe</span>
      </div>
    </div>
  )
}

function ReportContent({ state, branding }: { state: ScheduleBuilderState; branding: BrandingContext }) {
  switch (state.reportType) {
    case "market_snapshot":
      return (
        <>
          <div className="text-center mb-3">
            <div className="text-[10px] uppercase tracking-wide text-gray-500">Median Sale Price</div>
            <div className="text-2xl font-bold text-gray-900">$1.15M</div>
          </div>
          <div className="flex bg-gray-50 border border-gray-200 rounded overflow-hidden mb-3">
            {[
              { label: "Closed", value: "42" },
              { label: "Avg DOM", value: "24" },
              { label: "MOI", value: "2.4" },
            ].map((stat, i) => (
              <div key={stat.label} className={`flex-1 p-2 text-center ${i < 2 ? 'border-r border-gray-200' : ''}`}>
                <div className="text-[9px] uppercase text-gray-500">{stat.label}</div>
                <div className="text-base font-semibold text-gray-900">{stat.value}</div>
              </div>
            ))}
          </div>
        </>
      )

    case "new_listings_gallery":
      return (
        <>
          <div className="text-center mb-3">
            <div className="text-[10px] uppercase tracking-wide text-gray-500">
              {state.audienceFilterName || "New Listings"}
            </div>
            <div className="text-2xl font-bold text-gray-900">127</div>
          </div>
          <div className="flex bg-gray-50 border border-gray-200 rounded overflow-hidden mb-3">
            <div className="flex-1 p-2 text-center border-r border-gray-200">
              <div className="text-[9px] uppercase text-gray-500">Median</div>
              <div className="text-base font-semibold text-gray-900">$985K</div>
            </div>
            <div className="flex-1 p-2 text-center">
              <div className="text-[9px] uppercase text-gray-500">Starting</div>
              <div className="text-base font-semibold text-gray-900">$425K</div>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-1.5 mb-2">
            {SAMPLE_PHOTOS.slice(0, 6).map((photo, i) => (
              <div key={i} className="relative aspect-[4/3] rounded overflow-hidden">
                <img src={photo} alt={`Property ${i + 1}`} className="w-full h-full object-cover" />
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-1">
                  <p className="text-white text-[9px] font-medium">${(650 + i * 125)}K</p>
                </div>
              </div>
            ))}
          </div>
        </>
      )

    case "closed":
      return (
        <>
          <div className="text-center mb-3">
            <div className="text-[10px] uppercase tracking-wide text-gray-500">Total Closed</div>
            <div className="text-2xl font-bold text-gray-900">42</div>
          </div>
          <div className="flex bg-gray-50 border border-gray-200 rounded overflow-hidden mb-3">
            {[
              { label: "Median", value: "$1.08M" },
              { label: "Avg DOM", value: "18" },
              { label: "Close-List", value: "98.2%" },
            ].map((stat, i) => (
              <div key={stat.label} className={`flex-1 p-2 text-center ${i < 2 ? 'border-r border-gray-200' : ''}`}>
                <div className="text-[9px] uppercase text-gray-500">{stat.label}</div>
                <div className="text-sm font-semibold text-gray-900">{stat.value}</div>
              </div>
            ))}
          </div>
          <div className="border border-gray-200 rounded overflow-hidden text-xs">
            <div className="grid grid-cols-4 bg-gray-100 px-2 py-1.5 font-medium text-gray-600">
              <div>Address</div>
              <div className="text-center">Beds</div>
              <div className="text-center">Baths</div>
              <div className="text-right">Price</div>
            </div>
            {[
              { addr: "123 Oak St", beds: 4, baths: 3, price: "$1.2M" },
              { addr: "456 Maple", beds: 3, baths: 2, price: "$985K" },
            ].map((sale, i) => (
              <div key={i} className="grid grid-cols-4 px-2 py-1.5 border-t border-gray-200">
                <div className="truncate">{sale.addr}</div>
                <div className="text-center">{sale.beds}</div>
                <div className="text-center">{sale.baths}</div>
                <div className="text-right font-medium">{sale.price}</div>
              </div>
            ))}
          </div>
        </>
      )

    case null:
      return (
        <div className="text-center py-6 text-gray-400 text-xs">
          Select a report type to preview
        </div>
      )

    default:
      return (
        <div className="text-center py-6 text-gray-400 text-xs">
          Preview for this report type
        </div>
      )
  }
}
