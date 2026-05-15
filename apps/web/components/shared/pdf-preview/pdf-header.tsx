interface PdfHeaderProps {
  primaryColor: string
  accentColor: string
  headerLogoUrl: string | null
  displayName: string | null
  reportTitle: string
  areaName: string
  lookbackDays: number
  audienceLabel: string | null
}

// Gradient header band that mirrors the band rendered at the top of every
// market report PDF (apps/worker/src/worker/templates/market/_header.html).
export function PdfHeader({
  primaryColor,
  accentColor,
  headerLogoUrl,
  displayName,
  reportTitle,
  areaName,
  lookbackDays,
  audienceLabel,
}: PdfHeaderProps) {
  return (
    <div
      className="flex items-center justify-between gap-3 px-4 py-3 text-white"
      style={{
        background: `linear-gradient(115deg, ${primaryColor} 0%, ${primaryColor} 55%, ${accentColor} 100%)`,
      }}
    >
      <div className="min-w-0 flex-1">
        <div className="text-[8px] font-medium uppercase tracking-[0.18em] text-white/70">
          {displayName || "TrendyReports"}
        </div>
        <div className="mt-0.5 text-[15px] font-bold leading-tight text-white">
          {reportTitle}
        </div>
        <div className="mt-0.5 text-[9px] text-white/80">
          {areaName}
          {lookbackDays ? ` · Last ${lookbackDays} days` : ""}
          {audienceLabel ? ` · ${audienceLabel}` : ""}
        </div>
      </div>
      <div className="flex h-9 w-16 flex-shrink-0 items-center justify-end">
        {headerLogoUrl ? (
          <img
            src={headerLogoUrl}
            alt=""
            className="max-h-full max-w-full object-contain"
          />
        ) : (
          <div className="flex h-7 w-7 items-center justify-center rounded bg-white/20 text-[8px] font-bold text-white">
            {(displayName || "MR").slice(0, 2).toUpperCase()}
          </div>
        )}
      </div>
    </div>
  )
}
