import type { PreviewReportType } from "./sample-data"
import { PREVIEW_CONTENT } from "./sample-data"

const TYPE_LABELS: Record<PreviewReportType, string> = {
  market_snapshot: "Market Update",
  new_listings_gallery: "New Listings",
  new_listings: "New Listings",
  closed: "Closed Sales",
  inventory: "Inventory Report",
  featured_listings: "Featured Listings",
  price_bands: "Price Bands",
  open_houses: "Open Houses",
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
  const content = PREVIEW_CONTENT[reportType]
  const metricValue = content?.heroValue
  const metricLabel = content?.heroLabel

  return (
    <div
      className="text-white"
      style={{
        background: `linear-gradient(115deg, ${primaryColor} 0%, ${primaryColor} 30%, ${accentColor} 100%)`,
      }}
    >
      {/* Row 1: Logo */}
      {headerLogoUrl ? (
        <div className="pt-3 pb-1 text-center">
          <img
            src={headerLogoUrl}
            alt={displayName || "Logo"}
            className="mx-auto h-[40px] w-auto object-contain"
          />
        </div>
      ) : displayName ? (
        <div className="pt-3 pb-1 text-center text-[11px] font-semibold tracking-wide opacity-90 uppercase">
          {displayName}
        </div>
      ) : (
        <div className="pt-3" />
      )}

      {/* Row 2: 65/35 split — title+meta LEFT, metric RIGHT */}
      <div className="flex items-center px-5 py-2">
        <div className="flex-[0_0_65%] min-w-0">
          <h1
            className="text-[20px] font-bold leading-tight text-white"
            style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
          >
            {typeLabel} <span className="font-normal opacity-85">&mdash; {areaName}</span>
          </h1>
          <p className="mt-0.5 text-[10px] opacity-70">
            Last {lookbackDays} days &bull; Live MLS Data
          </p>
        </div>
        {metricValue && (
          <div className="flex-[0_0_35%] text-right">
            <div
              className="text-[24px] font-bold leading-none text-white"
              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
            >
              {metricValue}
            </div>
            {metricLabel && (
              <div className="mt-0.5 text-[9px] font-medium uppercase tracking-wider opacity-70">
                {metricLabel}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Row 3: Bottom padding */}
      <div className="pb-3" />
    </div>
  )
}
