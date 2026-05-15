import type { PdfLayoutProps } from "./types"

// Page 1 of the price_bands PDF: 4 price-band hero cards followed by a couple
// of representative listings.
export function PricebandsLayout({
  content,
  primaryColor,
  accentColor,
  sectionLabel,
}: PdfLayoutProps) {
  // PREVIEW_CONTENT.price_bands.stats already has 4 entries shaped as price
  // bands (Under $700K, $700K–$1M, …). Use them as the hero cards.
  const bandLabels = ["Entry", "Move-Up", "Premium", "Luxury"]
  const bands = content.stats.slice(0, 4)
  const listings = content.listings.slice(0, 2)

  return (
    <div className="flex flex-1 min-h-0 flex-col gap-2.5 px-4 py-3">
      <h2
        className="text-[12px] font-bold uppercase tracking-wider"
        style={{ color: primaryColor }}
      >
        {sectionLabel}
      </h2>

      <div className="grid grid-cols-4 gap-1.5">
        {bands.map((b, i) => (
          <div
            key={b.label}
            className="rounded-md border border-stone-200 px-2 py-2"
          >
            <div
              className="text-[7px] font-semibold uppercase tracking-wider"
              style={{ color: accentColor }}
            >
              {bandLabels[i] ?? `Band ${i + 1}`}
            </div>
            <div className="mt-0.5 text-[8px] text-stone-600">{b.label}</div>
            <div
              className="mt-1 text-[16px] font-bold leading-none"
              style={{ color: primaryColor }}
            >
              {b.value}
            </div>
            <div className="mt-0.5 text-[6.5px] uppercase tracking-wider text-stone-400">
              listings
            </div>
          </div>
        ))}
      </div>

      <div className="grid flex-1 grid-cols-2 gap-1.5">
        {listings.map((l, i) => (
          <div
            key={`${l.address}-${i}`}
            className="flex flex-col overflow-hidden rounded-md border border-stone-200 bg-white"
          >
            <div className="aspect-[4/3] overflow-hidden bg-stone-100">
              <img src={l.photo} alt="" className="h-full w-full object-cover" />
            </div>
            <div className="px-2 py-1.5">
              <div
                className="text-[11px] font-bold leading-tight"
                style={{ color: primaryColor }}
              >
                {l.price}
              </div>
              <div className="truncate text-[7.5px] text-stone-700">{l.address}</div>
              <div className="text-[7px] text-stone-500">{l.specs}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
