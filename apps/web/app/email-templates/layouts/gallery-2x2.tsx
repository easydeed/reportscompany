import { EmailHeader } from './email-header';
import { EmailFooter } from './email-footer';

const sampleListings = [
  {
    image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop',
    price: '$1,295,000',
    address: '2847 Waverly Dr',
    location: 'Silver Lake, 90039',
    beds: 3,
    baths: 2,
    sqft: '1,850',
  },
  {
    image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop',
    price: '$875,000',
    address: '1420 Micheltorena St',
    location: 'Silver Lake, 90026',
    beds: 2,
    baths: 2,
    sqft: '1,200',
  },
  {
    image: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
    price: '$2,150,000',
    address: '3021 Sunset Blvd',
    location: 'Silver Lake, 90039',
    beds: 4,
    baths: 3.5,
    sqft: '2,800',
  },
  {
    image: 'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=600&h=400&fit=crop',
    price: '$599,000',
    address: '915 Hyperion Ave',
    location: 'Silver Lake, 90027',
    beds: 2,
    baths: 1,
    sqft: '950',
  },
];

export function Gallery2x2Layout() {
  return (
    <div className="font-sans">
      <EmailHeader
        reportType="Featured Listings"
        title="Featured Listings – Silver Lake"
      />

      {/* Main Content */}
      <div className="bg-white px-10 py-10">
        {/* AI Narrative - 2-3 sentences */}
        <div className="mb-8">
          <p className="text-[16px] leading-[1.8] text-stone-900">
            Hand-picked properties showcasing the best of Silver Lake. These four featured homes represent exceptional value across a range of price points, from a charming starter on Hyperion to an expansive entertainer&apos;s dream on Sunset.
          </p>
        </div>

        {/* Gallery Count */}
        <div className="flex items-center gap-3 mb-6">
          <span className="inline-flex items-center justify-center w-8 h-8 bg-[#1B365D] text-white text-sm font-bold rounded-full">
            4
          </span>
          <span className="text-sm font-semibold text-stone-900">Featured Listings in Silver Lake</span>
          <div className="flex-1 h-px bg-stone-200" />
        </div>

        {/* 2x2 Grid - Large Photos */}
        <div className="grid grid-cols-2 gap-4 mb-10">
          {sampleListings.map((listing, idx) => (
            <div key={idx} className="bg-white rounded-lg border border-stone-200 overflow-hidden shadow-sm">
              <img
                src={listing.image}
                alt={listing.address}
                className="w-full h-[180px] object-cover"
              />
              <div className="p-4">
                <p className="font-serif text-[20px] font-bold text-[#1B365D] mb-1">
                  {listing.price}
                </p>
                <p className="text-[14px] font-semibold text-stone-900 truncate mb-0.5">
                  {listing.address}
                </p>
                <p className="text-[12px] text-stone-500 mb-3">
                  {listing.location}
                </p>
                <p className="text-[12px] text-stone-600">
                  {listing.beds} Bed &bull; {listing.baths} Bath &bull; {listing.sqft} SF
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Take Callout */}
        <div className="bg-[#B8860B]/8 border border-[#B8860B]/25 rounded-lg p-5 mb-8">
          <div className="flex items-start gap-3">
            <span className="text-[#B8860B] text-xl">$</span>
            <p className="text-sm font-medium text-stone-900 leading-relaxed">
              These curated properties offer something for every buyer. From the $599K entry point to the $2.1M flagship, Silver Lake continues to deliver diverse options in one of LA&apos;s most sought-after neighborhoods.
            </p>
          </div>
        </div>

        {/* CTA Button */}
        <div className="bg-[#1B365D]/5 rounded-lg p-6 text-center mb-6">
          <a
            href="#"
            className="inline-block bg-[#1B365D] text-white font-semibold text-sm px-10 py-4 rounded-lg hover:bg-[#152a4a] transition"
          >
            View All Listings
          </a>
        </div>

        <EmailFooter />
      </div>
    </div>
  );
}
