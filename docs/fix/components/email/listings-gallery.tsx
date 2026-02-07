import { DollarSign } from "lucide-react";
import Image from "next/image";

const LISTINGS = [
  {
    address: "742 Sunset Blvd",
    city: "Los Angeles",
    zip: "90028",
    price: "$1,250,000",
    beds: 4,
    baths: 3,
    sqft: "2,800",
    image: "/images/property-1.jpg",
  },
  {
    address: "1831 Echo Park Ave",
    city: "Los Angeles",
    zip: "90026",
    price: "$689,000",
    beds: 2,
    baths: 2,
    sqft: "1,200",
    image: "/images/property-2.jpg",
  },
  {
    address: "4521 Franklin Ave",
    city: "Los Angeles",
    zip: "90027",
    price: "$925,000",
    beds: 3,
    baths: 2,
    sqft: "1,650",
    image: "/images/property-3.jpg",
  },
  {
    address: "2200 Beachwood Dr",
    city: "Los Angeles",
    zip: "90068",
    price: "$1,475,000",
    beds: 5,
    baths: 4,
    sqft: "3,200",
    image: "/images/property-4.jpg",
  },
  {
    address: "915 Hyperion Ave",
    city: "Los Angeles",
    zip: "90029",
    price: "$599,000",
    beds: 2,
    baths: 1,
    sqft: "950",
    image: "/images/property-5.jpg",
  },
  {
    address: "3340 Waverly Dr",
    city: "Los Angeles",
    zip: "90027",
    price: "$1,100,000",
    beds: 4,
    baths: 3,
    sqft: "2,400",
    image: "/images/property-6.jpg",
  },
];

function PropertyCard({
  listing,
}: {
  listing: (typeof LISTINGS)[number];
}) {
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
      {/* Photo with price overlay */}
      <div className="relative aspect-[16/10] w-full overflow-hidden bg-muted">
        <Image
          src={listing.image || "/placeholder.svg"}
          alt={listing.address}
          fill
          className="object-cover"
        />
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent px-3 pb-2.5 pt-8">
          <span className="font-serif text-lg font-bold text-white">
            {listing.price}
          </span>
        </div>
      </div>
      {/* Details */}
      <div className="px-3.5 py-3">
        <p className="text-sm font-semibold text-foreground">
          {listing.address}
        </p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          {listing.city}, {listing.zip}
        </p>
        <div className="mt-2 flex items-center gap-1.5">
          <span className="rounded bg-[#1e3a5f]/[0.07] px-1.5 py-0.5 text-[10px] font-medium text-[#1e3a5f]">
            {listing.beds} Bed
          </span>
          <span className="rounded bg-[#1e3a5f]/[0.07] px-1.5 py-0.5 text-[10px] font-medium text-[#1e3a5f]">
            {listing.baths} Bath
          </span>
          <span className="rounded bg-[#1e3a5f]/[0.07] px-1.5 py-0.5 text-[10px] font-medium text-[#1e3a5f]">
            {listing.sqft} SF
          </span>
        </div>
      </div>
    </div>
  );
}

export function ListingsGallery() {
  return (
    <div className="px-8 py-8">
      {/* AI Insight */}
      <div className="mb-8 rounded-lg border-l-4 border-[#1e3a5f] bg-[#1e3a5f]/[0.04] px-5 py-4">
        <p className="text-sm leading-relaxed text-foreground/80">
          Fresh opportunities in Los Angeles&mdash;24 new properties just hit
          the market. With a median asking price of $725K, there&apos;s
          something for every buyer.
        </p>
      </div>

      {/* Gallery Count Badge */}
      <div className="mb-6 flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-full bg-[#1e3a5f] px-4 py-1.5">
          <span className="text-sm font-bold text-white">24</span>
        </div>
        <span className="text-sm font-semibold text-foreground">
          New Listings
        </span>
        <div className="h-px flex-1 bg-border" />
      </div>

      {/* Property Grid */}
      <div className="mb-8 grid grid-cols-2 gap-4">
        {LISTINGS.map((listing) => (
          <PropertyCard key={listing.address} listing={listing} />
        ))}
      </div>

      {/* Quick Take Callout */}
      <div className="mb-8 rounded-lg border border-[#b8860b]/20 bg-[#b8860b]/[0.06] p-5">
        <div className="flex items-start gap-3">
          <DollarSign className="mt-0.5 h-5 w-5 shrink-0 text-[#b8860b]" />
          <p className="text-sm font-medium leading-relaxed text-foreground">
            Seller&apos;s market conditions: 2.8 months of inventory indicates
            strong demand in Los Angeles.
          </p>
        </div>
      </div>

      {/* CTA */}
      <div className="rounded-lg bg-[#1e3a5f]/[0.04] px-6 py-6 text-center">
        <a
          href="#"
          className="inline-block rounded-lg bg-[#1e3a5f] px-8 py-3.5 text-sm font-semibold tracking-wide text-white transition-opacity hover:opacity-90"
        >
          View All Listings
        </a>
      </div>
    </div>
  );
}
