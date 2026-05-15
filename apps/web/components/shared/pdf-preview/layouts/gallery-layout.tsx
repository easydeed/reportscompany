import type { PdfLayoutProps } from "./types"

// Two-column photo gallery for new_listings_gallery / featured_listings /
// open_houses. Renders the first 6 listings as the "first page" sample.
export function GalleryLayout({
  content,
  primaryColor,
  accentColor,
  sectionLabel,
}: PdfLayoutProps) {
  const listings = content.listings.slice(0, 6)
  const heroStats = content.stats.slice(0, 3)

  return (
    <div className="flex flex-1 min-h-0 flex-col gap-2.5 px-4 py-3">
      <div className="flex items-baseline justify-between">
        <h2
          className="text-[12px] font-bold uppercase tracking-wider"
          style={{ color: primaryColor }}
        >
          {sectionLabel}
        </h2>
        {content.galleryCount != null && (
          <span
            className="rounded-full px-2 py-0.5 text-[8px] font-semibold text-white"
            style={{ backgroundColor: accentColor }}
          >
            {content.galleryCount} listings
          </span>
        )}
      </div>

      {heroStats.length > 0 && (
        <div className="flex gap-1.5">
          {heroStats.map((s) => (
            <div
              key={s.label}
              className="flex-1 rounded-md border border-stone-200 px-2 py-1.5"
            >
              <div className="text-[7px] uppercase tracking-wider text-stone-500">
                {s.label}
              </div>
              <div
                className="text-[12px] font-bold leading-tight"
                style={{ color: primaryColor }}
              >
                {s.value}
              </div>
              {s.sub && <div className="text-[6.5px] text-stone-400">{s.sub}</div>}
            </div>
          ))}
        </div>
      )}

      <div className="grid flex-1 grid-cols-2 gap-1.5">
        {listings.map((l, i) => (
          <div
            key={`${l.address}-${i}`}
            className="flex flex-col overflow-hidden rounded-md border border-stone-200 bg-white"
          >
            <div className="aspect-[4/3] overflow-hidden bg-stone-100">
              <img src={l.photo} alt="" className="h-full w-full object-cover" />
            </div>
            <div className="px-1.5 py-1">
              <div
                className="text-[10px] font-bold leading-tight"
                style={{ color: primaryColor }}
              >
                {l.price}
              </div>
              <div className="truncate text-[7px] text-stone-700">{l.address}</div>
              <div className="text-[6.5px] text-stone-500">{l.specs}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
