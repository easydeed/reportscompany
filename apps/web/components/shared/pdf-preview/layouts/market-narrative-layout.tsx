import type { PdfLayoutProps } from "./types"

// Page 1 of the Market Snapshot PDF: hero stat + AI narrative + stat grid +
// compact 2x2 listing sample.
export function MarketNarrativeLayout({
  content,
  primaryColor,
  accentColor,
  sectionLabel,
}: PdfLayoutProps) {
  const stats = content.stats.slice(0, 4)
  const listings = content.listings.slice(0, 4)

  return (
    <div className="flex flex-1 min-h-0 flex-col gap-2.5 px-4 py-3">
      <div className="flex items-baseline justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[7px] uppercase tracking-wider text-stone-500">
            {content.heroLabel}
          </div>
          <div
            className="text-[24px] font-bold leading-none"
            style={{ color: primaryColor }}
          >
            {content.heroValue}
          </div>
          {content.heroSub && (
            <div className="mt-0.5 text-[8px] text-stone-500">{content.heroSub}</div>
          )}
        </div>
        <h2
          className="flex-shrink-0 text-[10px] font-bold uppercase tracking-wider"
          style={{ color: primaryColor }}
        >
          {sectionLabel}
        </h2>
      </div>

      <div
        className="rounded-md px-2.5 py-2"
        style={{
          backgroundColor: `${accentColor}10`,
          borderLeft: `3px solid ${accentColor}`,
        }}
      >
        <div
          className="mb-0.5 text-[7px] font-semibold uppercase tracking-wider"
          style={{ color: accentColor }}
        >
          Market Insight
        </div>
        <p className="text-[8px] leading-snug text-stone-700">{content.narrative}</p>
      </div>

      <div className="grid grid-cols-4 gap-1.5">
        {stats.map((s) => (
          <div
            key={s.label}
            className="rounded-md border border-stone-200 px-1.5 py-1.5 text-center"
          >
            <div
              className="text-[12px] font-bold leading-tight"
              style={{ color: primaryColor }}
            >
              {s.value}
            </div>
            <div className="mt-0.5 text-[6.5px] uppercase tracking-wider text-stone-500">
              {s.label}
            </div>
            {s.sub && <div className="text-[6px] text-stone-400">{s.sub}</div>}
          </div>
        ))}
      </div>

      <div className="grid flex-1 grid-cols-2 gap-1.5">
        {listings.map((l, i) => (
          <div
            key={`${l.address}-${i}`}
            className="relative aspect-[4/3] overflow-hidden rounded-md bg-stone-100"
          >
            <img src={l.photo} alt="" className="h-full w-full object-cover" />
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent px-1.5 py-1">
              <div
                className="text-[9px] font-bold text-white"
              >
                {l.price}
              </div>
              <div className="truncate text-[6.5px] text-white/90">{l.address}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
