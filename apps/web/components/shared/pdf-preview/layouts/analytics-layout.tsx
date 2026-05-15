import type { PdfLayoutProps } from "./types"

// Page 1 of the new_listings analytics PDF: large hero stat, stat grid, and a
// dense vertical listing list (rather than a photo grid).
export function AnalyticsLayout({
  content,
  primaryColor,
  accentColor,
  sectionLabel,
}: PdfLayoutProps) {
  const stats = content.stats.slice(0, 4)
  const listings = content.listings.slice(0, 5)

  return (
    <div className="flex flex-1 min-h-0 flex-col gap-2.5 px-4 py-3">
      <div className="flex items-baseline justify-between gap-3">
        <h2
          className="text-[12px] font-bold uppercase tracking-wider"
          style={{ color: primaryColor }}
        >
          {sectionLabel}
        </h2>
        <div className="text-right">
          <div
            className="text-[20px] font-bold leading-none"
            style={{ color: primaryColor }}
          >
            {content.heroValue}
          </div>
          <div className="text-[7px] uppercase tracking-wider text-stone-500">
            {content.heroLabel}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-1.5">
        {stats.map((s) => (
          <div
            key={s.label}
            className="rounded-md px-1.5 py-1.5 text-center"
            style={{ backgroundColor: `${accentColor}10` }}
          >
            <div
              className="text-[11px] font-bold leading-tight"
              style={{ color: primaryColor }}
            >
              {s.value}
            </div>
            <div className="mt-0.5 text-[6.5px] uppercase tracking-wider text-stone-500">
              {s.label}
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-1 flex-col gap-1">
        {listings.map((l, i) => (
          <div
            key={`${l.address}-${i}`}
            className="flex items-center gap-2 rounded-md border border-stone-200 px-2 py-1"
          >
            <div className="aspect-[4/3] h-8 flex-shrink-0 overflow-hidden rounded bg-stone-100">
              <img src={l.photo} alt="" className="h-full w-full object-cover" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-[8px] font-semibold text-stone-800">
                {l.address}
              </div>
              <div className="text-[6.5px] text-stone-500">{l.specs}</div>
            </div>
            {l.badge && (
              <span
                className="rounded-full px-1.5 py-0.5 text-[6.5px] font-semibold"
                style={{ color: accentColor, border: `1px solid ${accentColor}55` }}
              >
                {l.badge}
              </span>
            )}
            <div
              className="text-[10px] font-bold"
              style={{ color: primaryColor }}
            >
              {l.price}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
