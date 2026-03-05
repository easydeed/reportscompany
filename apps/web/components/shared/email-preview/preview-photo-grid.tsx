import type { SampleListing } from "./sample-data"

interface PreviewPhotoGridProps {
  listings: SampleListing[]
  layout: "2x2" | "3x2" | "stacked" | "large-cards"
  primaryColor: string
  accentColor: string
}

export function PreviewPhotoGrid({
  listings,
  layout,
  primaryColor,
  accentColor,
}: PreviewPhotoGridProps) {
  if (layout === "stacked") {
    return (
      <div className="space-y-2">
        {listings.slice(0, 3).map((listing, i) => (
          <StackedCard key={i} listing={listing} primaryColor={primaryColor} />
        ))}
      </div>
    )
  }

  if (layout === "large-cards") {
    return (
      <div className="grid grid-cols-2 gap-2">
        {listings.slice(0, 4).map((listing, i) => (
          <LargeCard key={i} listing={listing} primaryColor={primaryColor} />
        ))}
      </div>
    )
  }

  const cols = layout === "3x2" ? "grid-cols-3" : "grid-cols-2"
  const count = layout === "3x2" ? 6 : 4

  return (
    <div className={`grid ${cols} gap-1.5`}>
      {listings.slice(0, count).map((listing, i) => (
        <PhotoCard
          key={i}
          listing={listing}
          primaryColor={primaryColor}
          accentColor={accentColor}
        />
      ))}
    </div>
  )
}

function PhotoCard({
  listing,
  primaryColor,
  accentColor,
}: {
  listing: SampleListing
  primaryColor: string
  accentColor: string
}) {
  const badgeBg = listing.badge === "Sold" ? primaryColor : accentColor

  return (
    <div className="overflow-hidden rounded-md border border-stone-200 bg-white">
      <div className="relative aspect-[4/3]">
        <img
          src={listing.photo}
          alt={listing.address}
          className="h-full w-full object-cover"
        />
        {listing.badge && (
          <span
            className="absolute right-1 top-1 rounded px-1.5 py-0.5 text-[7px] font-bold uppercase tracking-wide text-white"
            style={{ backgroundColor: badgeBg }}
          >
            {listing.badge}
          </span>
        )}
      </div>
      <div className="px-2 py-1.5">
        <div
          className="text-[11px] font-bold"
          style={{ color: primaryColor }}
        >
          {listing.price}
        </div>
        <div className="text-[9px] text-stone-700 truncate">{listing.address}</div>
        <div className="text-[8px] text-stone-400">{listing.specs}</div>
      </div>
    </div>
  )
}

function LargeCard({
  listing,
  primaryColor,
}: {
  listing: SampleListing
  primaryColor: string
}) {
  return (
    <div className="overflow-hidden rounded-lg border border-stone-200 bg-white">
      <div className="aspect-[4/3]">
        <img
          src={listing.photo}
          alt={listing.address}
          className="h-full w-full object-cover"
        />
      </div>
      <div className="px-2.5 py-2">
        <div
          className="text-[12px] font-bold"
          style={{ color: primaryColor }}
        >
          {listing.price}
        </div>
        <div className="mt-0.5 text-[10px] font-medium text-stone-800">{listing.address}</div>
        <div className="text-[9px] text-stone-400">{listing.specs}</div>
      </div>
    </div>
  )
}

function StackedCard({
  listing,
  primaryColor,
}: {
  listing: SampleListing
  primaryColor: string
}) {
  return (
    <div className="flex gap-2.5 rounded-lg border border-stone-200 bg-white p-2">
      <div className="h-16 w-20 flex-shrink-0 overflow-hidden rounded">
        <img
          src={listing.photo}
          alt={listing.address}
          className="h-full w-full object-cover"
        />
      </div>
      <div className="min-w-0 flex-1 py-0.5">
        <div
          className="text-[12px] font-bold"
          style={{ color: primaryColor }}
        >
          {listing.price}
        </div>
        <div className="text-[10px] font-medium text-stone-800 truncate">{listing.address}</div>
        <div className="text-[9px] text-stone-400">{listing.specs}</div>
      </div>
    </div>
  )
}
