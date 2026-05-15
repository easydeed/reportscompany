import type { PdfLayoutProps } from "./types"

// Page 1 of the closed/inventory PDFs: section heading, stat row, a few
// hero cards, and a preview of the data table.
export function ClosedInventoryLayout({
  content,
  primaryColor,
  sectionLabel,
}: PdfLayoutProps) {
  const stats = content.stats.slice(0, 3)
  const heroListings = content.listings.slice(0, 3)
  const tableRows = content.tableRows.slice(0, 4)

  return (
    <div className="flex flex-1 min-h-0 flex-col gap-2.5 px-4 py-3">
      <div className="flex items-baseline justify-between">
        <h2
          className="text-[12px] font-bold uppercase tracking-wider"
          style={{ color: primaryColor }}
        >
          {sectionLabel}
        </h2>
        {content.totalAvailable != null && (
          <span className="text-[8px] text-stone-500">
            {content.totalAvailable} total
          </span>
        )}
      </div>

      {stats.length > 0 && (
        <div className="grid grid-cols-3 gap-1.5">
          {stats.map((s) => (
            <div
              key={s.label}
              className="rounded-md border border-stone-200 px-2 py-1.5"
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

      <div className="grid grid-cols-3 gap-1.5">
        {heroListings.map((l, i) => (
          <div
            key={`${l.address}-${i}`}
            className="relative aspect-[4/3] overflow-hidden rounded-md bg-stone-100"
          >
            <img src={l.photo} alt="" className="h-full w-full object-cover" />
            {l.badge && (
              <span
                className="absolute left-1 top-1 rounded px-1 py-0.5 text-[7px] font-semibold text-white"
                style={{ backgroundColor: primaryColor }}
              >
                {l.badge}
              </span>
            )}
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent px-1.5 py-0.5">
              <div className="text-[9px] font-bold text-white">{l.price}</div>
              <div className="truncate text-[6.5px] text-white/90">{l.address}</div>
            </div>
          </div>
        ))}
      </div>

      {tableRows.length > 0 && (
        <div className="flex-1 overflow-hidden rounded-md border border-stone-200 text-[7.5px]">
          <div
            className="grid grid-cols-[1.6fr_0.6fr_0.6fr_0.8fr_0.8fr_0.5fr] gap-1 px-2 py-1 text-[7px] font-semibold uppercase tracking-wider text-stone-500"
            style={{ backgroundColor: `${primaryColor}0F` }}
          >
            <span>Address</span>
            <span>Beds</span>
            <span>Baths</span>
            <span>SqFt</span>
            <span>Price</span>
            <span>DOM</span>
          </div>
          {tableRows.map((r) => (
            <div
              key={r.address}
              className="grid grid-cols-[1.6fr_0.6fr_0.6fr_0.8fr_0.8fr_0.5fr] gap-1 border-t border-stone-100 px-2 py-1 text-stone-700"
            >
              <span className="truncate">{r.address}</span>
              <span>{r.beds}</span>
              <span>{r.baths}</span>
              <span>{r.sqft}</span>
              <span style={{ color: primaryColor }} className="font-semibold">
                {r.price}
              </span>
              <span>{r.dom}d</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
