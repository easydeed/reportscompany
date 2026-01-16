"use client"

import {
  type ScheduleBuilderState,
  type BrandingContext,
  type ProfileContext,
  REPORT_TYPE_LABELS,
} from "./types"

interface EmailPreviewProps {
  state: ScheduleBuilderState
  branding: BrandingContext
  profile: ProfileContext
  area: string
}

export function EmailPreview({ state, branding, profile, area }: EmailPreviewProps) {
  const getHeaderTitle = () => {
    if (state.reportType === "new_listings_gallery" && state.audienceFilter && state.audienceFilter !== "all") {
      return `${state.audienceFilterName || "New Listings"} – ${area || "Your Area"}`
    }
    return `${REPORT_TYPE_LABELS[state.reportType]} – ${area || "Your Area"}`
  }

  return (
    <div className="mx-auto max-w-full font-sans text-sm">
      {/* Email Header */}
      <div
        className="rounded-t-xl px-6 py-8 text-center text-white"
        style={{
          background: `linear-gradient(135deg, ${branding.primaryColor} 0%, ${branding.accentColor} 100%)`,
        }}
      >
        {/* Logo */}
        {branding.emailLogoUrl ? (
          <img 
            src={branding.emailLogoUrl} 
            alt={branding.displayName || "Logo"}
            className="mx-auto mb-4 h-8 w-auto"
          />
        ) : (
          <div className="mb-4 mx-auto w-28 h-8 bg-white/20 rounded flex items-center justify-center text-xs font-semibold">
            {branding.displayName || "TrendyReports"}
          </div>
        )}

        {/* Badge */}
        <div className="inline-block bg-white/20 px-3 py-1 rounded-full text-[10px] uppercase tracking-wide mb-2">
          {REPORT_TYPE_LABELS[state.reportType]}
        </div>

        {/* Title */}
        <h1 className="text-lg font-bold mb-1">{getHeaderTitle()}</h1>

        {/* Subtitle */}
        <p className="text-[11px] opacity-90">Last {state.lookbackDays} days • Live MLS Data</p>
      </div>

      {/* Email Body */}
      <div className="bg-white p-6">
        {/* Insight Box */}
        <div className="bg-stone-50 border border-stone-200 rounded-md p-3 mb-5 text-xs text-stone-600">
          The {area || "selected area"} market showed strong activity this period with median prices holding steady.
          Here&apos;s your latest report summary...
        </div>

        {/* Report-Specific Content */}
        <ReportContent state={state} branding={branding} />

        {/* CTA Button */}
        <div className="text-center my-5">
          <button
            className="inline-block px-6 py-3 rounded-md text-white font-semibold text-sm cursor-default"
            style={{ backgroundColor: branding.primaryColor }}
          >
            View Full Report →
          </button>
        </div>

        {/* Agent Footer */}
        <div className="flex items-center gap-3 pt-5 mt-5 border-t border-stone-200">
          <div
            className="w-12 h-12 rounded-full bg-stone-200 flex items-center justify-center text-lg shrink-0 overflow-hidden"
            style={{ border: `2px solid ${branding.primaryColor}` }}
          >
            {profile.avatarUrl ? (
              <img
                src={profile.avatarUrl}
                alt={profile.name}
                className="w-full h-full rounded-full object-cover"
              />
            ) : (
              <span className="text-stone-500 font-medium">
                {profile.name?.charAt(0) || "?"}
              </span>
            )}
          </div>
          <div className="min-w-0">
            <div className="font-semibold text-stone-900 truncate">{profile.name}</div>
            {profile.jobTitle && (
              <div className="text-[11px] text-stone-500 truncate">{profile.jobTitle}</div>
            )}
            <div className="text-[11px] truncate" style={{ color: branding.primaryColor }}>
              {[profile.phone, profile.email].filter(Boolean).join(" • ")}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-stone-50 rounded-b-xl px-4 py-4 text-center text-[10px] text-stone-500">
        Powered by {branding.displayName || "TrendyReports"} • <span className="underline cursor-pointer">Unsubscribe</span>
      </div>
    </div>
  )
}

function ReportContent({ state, branding }: { state: ScheduleBuilderState; branding: BrandingContext }) {
  switch (state.reportType) {
    case "market_snapshot":
      return <MarketSnapshotContent />
    case "new_listings":
    case "new_listings_gallery":
      return <NewListingsContent audienceFilter={state.audienceFilterName} />
    case "closed":
      return <ClosedSalesContent />
    case "inventory":
      return <InventoryContent />
    case "price_bands":
      return <PriceAnalysisContent primaryColor={branding.primaryColor} />
    case "open_houses":
      return <OpenHousesContent />
    case "featured_listings":
      return <FeaturedListingsContent />
    default:
      return <MarketSnapshotContent />
  }
}

function MarketSnapshotContent() {
  return (
    <>
      {/* Hero Metric */}
      <div className="text-center mb-4">
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-1">Median Sale Price</div>
        <div className="text-3xl font-bold text-stone-900">$1.15M</div>
      </div>

      {/* Stats Bar */}
      <div className="flex bg-stone-50 border border-stone-200 rounded-lg overflow-hidden mb-5">
        <div className="flex-1 p-3 text-center border-r border-stone-200">
          <div className="text-[9px] uppercase text-stone-500">Closed Sales</div>
          <div className="text-lg font-semibold text-stone-900">42</div>
        </div>
        <div className="flex-1 p-3 text-center border-r border-stone-200">
          <div className="text-[9px] uppercase text-stone-500">Avg DOM</div>
          <div className="text-lg font-semibold text-stone-900">24</div>
        </div>
        <div className="flex-1 p-3 text-center">
          <div className="text-[9px] uppercase text-stone-500">MOI</div>
          <div className="text-lg font-semibold text-stone-900">2.4</div>
        </div>
      </div>

      {/* Market Activity */}
      <div className="mb-4">
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-2">Market Activity</div>
        <div className="flex bg-stone-50 border border-stone-200 rounded-lg overflow-hidden">
          <div className="flex-1 p-3 text-center border-r border-stone-200">
            <div className="text-[9px] uppercase text-stone-500">New Listings</div>
            <div className="text-lg font-semibold text-stone-900">47</div>
          </div>
          <div className="flex-1 p-3 text-center border-r border-stone-200">
            <div className="text-[9px] uppercase text-stone-500">Pending</div>
            <div className="text-lg font-semibold text-stone-900">23</div>
          </div>
          <div className="flex-1 p-3 text-center">
            <div className="text-[9px] uppercase text-stone-500">Sale-to-List</div>
            <div className="text-lg font-semibold text-stone-900">98.5%</div>
          </div>
        </div>
      </div>

      {/* Property Types */}
      <div>
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-2">By Property Type</div>
        <div className="flex gap-2 text-xs">
          <div className="flex-1 bg-stone-50 border border-stone-200 rounded-md p-2 text-center">
            <div className="font-semibold">78</div>
            <div className="text-stone-500">Single Family</div>
          </div>
          <div className="flex-1 bg-stone-50 border border-stone-200 rounded-md p-2 text-center">
            <div className="font-semibold">42</div>
            <div className="text-stone-500">Condos</div>
          </div>
          <div className="flex-1 bg-stone-50 border border-stone-200 rounded-md p-2 text-center">
            <div className="font-semibold">7</div>
            <div className="text-stone-500">Townhomes</div>
          </div>
        </div>
      </div>
    </>
  )
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

function NewListingsContent({ audienceFilter }: { audienceFilter?: string | null }) {
  return (
    <>
      {/* Hero Metric */}
      <div className="text-center mb-4">
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-1">
          {audienceFilter ? `${audienceFilter} Listings` : "New Listings"}
        </div>
        <div className="text-3xl font-bold text-stone-900">127</div>
      </div>

      {/* Stats Bar */}
      <div className="flex bg-stone-50 border border-stone-200 rounded-lg overflow-hidden mb-5">
        <div className="flex-1 p-3 text-center border-r border-stone-200">
          <div className="text-[9px] uppercase text-stone-500">Median Price</div>
          <div className="text-lg font-semibold text-stone-900">$985K</div>
        </div>
        <div className="flex-1 p-3 text-center">
          <div className="text-[9px] uppercase text-stone-500">Starting At</div>
          <div className="text-lg font-semibold text-stone-900">$425K</div>
        </div>
      </div>

      {/* Listing Gallery */}
      <div className="mb-4">
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-2">
          12 {audienceFilter || "New"} Listings
        </div>
        <div className="grid grid-cols-3 gap-2">
          {[
            { price: "$1.2M", beds: "4bd/3ba" },
            { price: "$985K", beds: "3bd/2ba" },
            { price: "$750K", beds: "3bd/2ba" },
            { price: "$695K", beds: "2bd/2ba" },
            { price: "$1.4M", beds: "5bd/4ba" },
            { price: "$825K", beds: "3bd/2ba" },
          ].map((listing, i) => (
            <div key={i} className="bg-stone-100 rounded-md overflow-hidden text-center">
              <div className="h-14 overflow-hidden">
                <img src={SAMPLE_PHOTOS[i]} alt={`Property ${i + 1}`} className="w-full h-full object-cover" />
              </div>
              <div className="p-2">
                <div className="font-semibold text-xs">{listing.price}</div>
                <div className="text-[10px] text-stone-500">{listing.beds}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

function ClosedSalesContent() {
  return (
    <>
      {/* Hero Metric */}
      <div className="text-center mb-4">
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-1">Total Closed</div>
        <div className="text-3xl font-bold text-stone-900">42</div>
      </div>

      {/* Stats Bar */}
      <div className="flex bg-stone-50 border border-stone-200 rounded-lg overflow-hidden mb-5">
        <div className="flex-1 p-3 text-center border-r border-stone-200">
          <div className="text-[9px] uppercase text-stone-500">Median Price</div>
          <div className="text-lg font-semibold text-stone-900">$1.08M</div>
        </div>
        <div className="flex-1 p-3 text-center border-r border-stone-200">
          <div className="text-[9px] uppercase text-stone-500">Avg DOM</div>
          <div className="text-lg font-semibold text-stone-900">18</div>
        </div>
        <div className="flex-1 p-3 text-center">
          <div className="text-[9px] uppercase text-stone-500">Close-to-List</div>
          <div className="text-lg font-semibold text-stone-900">98.2%</div>
        </div>
      </div>

      {/* Recently Sold Table */}
      <div>
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-2">Recently Sold</div>
        <div className="border border-stone-200 rounded-lg overflow-hidden text-xs">
          <div className="grid grid-cols-4 bg-stone-100 px-3 py-2 font-medium text-stone-600">
            <div>Address</div>
            <div className="text-center">Beds</div>
            <div className="text-center">Baths</div>
            <div className="text-right">Price</div>
          </div>
          {[
            { addr: "123 Oak St", beds: 4, baths: 3, price: "$1.2M" },
            { addr: "456 Maple Dr", beds: 3, baths: 2, price: "$985K" },
            { addr: "789 Pine Ln", beds: 3, baths: 2, price: "$875K" },
          ].map((sale, i) => (
            <div key={i} className="grid grid-cols-4 px-3 py-2 border-t border-stone-200">
              <div className="truncate">{sale.addr}</div>
              <div className="text-center">{sale.beds}</div>
              <div className="text-center">{sale.baths}</div>
              <div className="text-right font-medium">{sale.price}</div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

function InventoryContent() {
  return (
    <>
      {/* Hero Metric */}
      <div className="text-center mb-4">
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-1">Active Listings</div>
        <div className="text-3xl font-bold text-stone-900">127</div>
      </div>

      {/* Stats Bar */}
      <div className="flex bg-stone-50 border border-stone-200 rounded-lg overflow-hidden mb-5">
        <div className="flex-1 p-3 text-center border-r border-stone-200">
          <div className="text-[9px] uppercase text-stone-500">New This Month</div>
          <div className="text-lg font-semibold text-stone-900">23</div>
        </div>
        <div className="flex-1 p-3 text-center border-r border-stone-200">
          <div className="text-[9px] uppercase text-stone-500">Median DOM</div>
          <div className="text-lg font-semibold text-stone-900">24</div>
        </div>
        <div className="flex-1 p-3 text-center">
          <div className="text-[9px] uppercase text-stone-500">MOI</div>
          <div className="text-lg font-semibold text-stone-900">2.4</div>
        </div>
      </div>

      {/* Active Listings Table */}
      <div>
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-2">Active Listings</div>
        <div className="border border-stone-200 rounded-lg overflow-hidden text-xs">
          <div className="grid grid-cols-4 bg-stone-100 px-3 py-2 font-medium text-stone-600">
            <div>Address</div>
            <div className="text-center">Beds</div>
            <div className="text-center">DOM</div>
            <div className="text-right">Price</div>
          </div>
          {[
            { addr: "101 Elm St", beds: 4, dom: 12, price: "$1.35M" },
            { addr: "202 Birch Ave", beds: 3, dom: 28, price: "$895K" },
            { addr: "303 Cedar Way", beds: 5, dom: 5, price: "$1.7M" },
          ].map((listing, i) => (
            <div key={i} className="grid grid-cols-4 px-3 py-2 border-t border-stone-200">
              <div className="truncate">{listing.addr}</div>
              <div className="text-center">{listing.beds}</div>
              <div className="text-center">{listing.dom}</div>
              <div className="text-right font-medium">{listing.price}</div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

function PriceAnalysisContent({ primaryColor }: { primaryColor: string }) {
  return (
    <>
      {/* Hero Metric */}
      <div className="text-center mb-4">
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-1">Total Listings</div>
        <div className="text-3xl font-bold text-stone-900">127</div>
      </div>

      {/* Stats Bar */}
      <div className="flex bg-stone-50 border border-stone-200 rounded-lg overflow-hidden mb-5">
        <div className="flex-1 p-3 text-center border-r border-stone-200">
          <div className="text-[9px] uppercase text-stone-500">Median Price</div>
          <div className="text-lg font-semibold text-stone-900">$985K</div>
        </div>
        <div className="flex-1 p-3 text-center border-r border-stone-200">
          <div className="text-[9px] uppercase text-stone-500">Avg DOM</div>
          <div className="text-lg font-semibold text-stone-900">24</div>
        </div>
        <div className="flex-1 p-3 text-center">
          <div className="text-[9px] uppercase text-stone-500">Price Range</div>
          <div className="text-base font-semibold text-stone-900">$400K-$2.5M</div>
        </div>
      </div>

      {/* Price Tiers */}
      <div>
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-2">Price Tiers</div>
        <div className="space-y-2">
          {[
            { label: "Entry Level", range: "$0-$500K", count: 12, opacity: 0.4 },
            { label: "Move-Up", range: "$500K-$1M", count: 28, opacity: 0.7 },
            { label: "Luxury", range: "$1M+", count: 10, opacity: 1 },
          ].map((tier, i) => (
            <div key={i} className="flex items-center gap-3 bg-stone-50 border border-stone-200 rounded-md p-3">
              <div 
                className="w-2 h-2 rounded-full" 
                style={{ backgroundColor: primaryColor, opacity: tier.opacity }} 
              />
              <div className="flex-1">
                <div className="font-medium text-xs">{tier.label}</div>
                <div className="text-[10px] text-stone-500">{tier.range}</div>
              </div>
              <div className="text-sm font-semibold">{tier.count} listings</div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

function OpenHousesContent() {
  return (
    <>
      {/* Hero Metric */}
      <div className="text-center mb-4">
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-1">Open Houses</div>
        <div className="text-3xl font-bold text-stone-900">15</div>
      </div>

      {/* Stats Bar */}
      <div className="flex bg-stone-50 border border-stone-200 rounded-lg overflow-hidden mb-5">
        <div className="flex-1 p-3 text-center border-r border-stone-200">
          <div className="text-[9px] uppercase text-stone-500">Saturday</div>
          <div className="text-lg font-semibold text-stone-900">8</div>
        </div>
        <div className="flex-1 p-3 text-center">
          <div className="text-[9px] uppercase text-stone-500">Sunday</div>
          <div className="text-lg font-semibold text-stone-900">7</div>
        </div>
      </div>

      {/* Open Houses List */}
      <div>
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-2">This Weekend</div>
        <div className="space-y-2">
          {[
            { addr: "123 Oak St", time: "Sat 1-4pm", price: "$1.2M" },
            { addr: "456 Maple Dr", time: "Sun 12-3pm", price: "$985K" },
            { addr: "789 Pine Ln", time: "Sat & Sun 1-4pm", price: "$875K" },
          ].map((oh, i) => (
            <div
              key={i}
              className="flex items-center justify-between bg-stone-50 border border-stone-200 rounded-md p-3 text-xs"
            >
              <div>
                <div className="font-medium">{oh.addr}</div>
                <div className="text-stone-500">{oh.time}</div>
              </div>
              <div className="font-semibold">{oh.price}</div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

function FeaturedListingsContent() {
  return (
    <>
      {/* Hero Metric */}
      <div className="text-center mb-4">
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-1">Featured Homes</div>
        <div className="text-3xl font-bold text-stone-900">6</div>
      </div>

      {/* Stats Bar */}
      <div className="flex bg-stone-50 border border-stone-200 rounded-lg overflow-hidden mb-5">
        <div className="flex-1 p-3 text-center border-r border-stone-200">
          <div className="text-[9px] uppercase text-stone-500">Highest Price</div>
          <div className="text-lg font-semibold text-stone-900">$2.4M</div>
        </div>
        <div className="flex-1 p-3 text-center">
          <div className="text-[9px] uppercase text-stone-500">Avg Sq Ft</div>
          <div className="text-lg font-semibold text-stone-900">3,200</div>
        </div>
      </div>

      {/* Featured Gallery */}
      <div className="mb-4">
        <div className="text-[10px] uppercase tracking-wide text-stone-500 mb-2">Featured Properties</div>
        <div className="grid grid-cols-3 gap-2">
          {[
            { price: "$2.4M", beds: "5bd/4ba" },
            { price: "$1.9M", beds: "4bd/3ba" },
            { price: "$1.6M", beds: "4bd/3ba" },
          ].map((listing, i) => (
            <div key={i} className="bg-stone-100 rounded-md overflow-hidden text-center">
              <div className="h-14 overflow-hidden">
                <img src={SAMPLE_PHOTOS[i]} alt={`Property ${i + 1}`} className="w-full h-full object-cover" />
              </div>
              <div className="p-2">
                <div className="font-semibold text-xs">{listing.price}</div>
                <div className="text-[10px] text-stone-500">{listing.beds}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

