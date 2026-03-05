import type { PreviewReportType } from "./sample-data"

const TYPE_LABELS: Record<PreviewReportType, string> = {
  market_snapshot: "Market Update",
  new_listings_gallery: "New Listings",
  closed: "Closed Sales",
  inventory: "Inventory Report",
  featured_listings: "Featured Listings",
}

interface PreviewHeaderProps {
  primaryColor: string
  accentColor: string
  headerLogoUrl?: string | null
  displayName?: string | null
  reportType: PreviewReportType
  audienceLabel?: string | null
  areaName?: string
  lookbackDays?: number
}

export function PreviewHeader({
  primaryColor,
  accentColor,
  headerLogoUrl,
  displayName,
  reportType,
  audienceLabel,
  areaName = "Your Area",
  lookbackDays = 30,
}: PreviewHeaderProps) {
  const typeLabel = audienceLabel || TYPE_LABELS[reportType] || "Report"
  const title = `${typeLabel} – ${areaName}`

  return (
    <div
      className="px-5 py-5 text-center text-white"
      style={{
        background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)`,
      }}
    >
      {headerLogoUrl ? (
        <img
          src={headerLogoUrl}
          alt={displayName || "Logo"}
          className="mx-auto mb-2.5 h-6 w-auto object-contain"
        />
      ) : displayName ? (
        <div className="mb-2.5 text-[11px] font-semibold tracking-wide opacity-90 uppercase">
          {displayName}
        </div>
      ) : null}

      <div className="inline-block rounded-full bg-white/20 px-2.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider mb-1.5">
        {TYPE_LABELS[reportType]}
      </div>

      <h1 className="text-[15px] font-bold leading-tight">{title}</h1>

      <p className="mt-1 text-[10px] opacity-80">
        Last {lookbackDays} days &bull; Live MLS Data
      </p>
    </div>
  )
}
