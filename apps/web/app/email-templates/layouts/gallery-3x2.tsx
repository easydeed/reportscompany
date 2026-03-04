import { EmailHeader } from './email-header';
import { EmailFooter } from './email-footer';

const sampleListings = [
  {
    image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop',
    price: '$1,295,000',
    address: '2847 Waverly Dr',
    beds: 3,
    baths: 2,
  },
  {
    image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop',
    price: '$875,000',
    address: '1420 Micheltorena',
    beds: 2,
    baths: 2,
  },
  {
    image: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
    price: '$2,150,000',
    address: '3021 Sunset Blvd',
    beds: 4,
    baths: 3.5,
  },
  {
    image: 'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=600&h=400&fit=crop',
    price: '$599,000',
    address: '915 Hyperion Ave',
    beds: 2,
    baths: 1,
  },
  {
    image: 'https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=600&h=400&fit=crop',
    price: '$1,100,000',
    address: '3340 Silver Lake',
    beds: 4,
    baths: 3,
  },
  {
    image: 'https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600&h=400&fit=crop',
    price: '$780,000',
    address: '2100 Griffith Park',
    beds: 2,
    baths: 2,
  },
];

export function Gallery3x2Layout() {
  return (
    <div className="font-sans">
      <EmailHeader
        reportType="New Listings"
        title="New Listings – Silver Lake"
      />

      {/* Main Content */}
      <div className="bg-white px-10 py-10">
        {/* AI Narrative - 2 sentences */}
        <div className="mb-8">
          <p className="text-[15px] leading-[1.7] text-stone-900">
            Six fresh opportunities just hit the market in Silver Lake. These new listings span from $599K to $2.15M, offering options for first-time buyers and move-up families alike.
          </p>
        </div>

        {/* Gallery Count */}
        <div className="flex items-center gap-3 mb-5">
          <span className="inline-flex items-center justify-center w-7 h-7 bg-[#1B365D] text-white text-xs font-bold rounded-full">
            6
          </span>
          <span className="text-sm font-semibold text-stone-900">New Listings This Week</span>
          <div className="flex-1 h-px bg-stone-200" />
        </div>

        {/* 3x2 Grid - Compact but photo-forward */}
        <div className="grid grid-cols-3 gap-3 mb-10">
          {sampleListings.map((listing, idx) => (
            <div key={idx} className="bg-white rounded-lg border border-stone-200 overflow-hidden">
              <img
                src={listing.image}
                alt={listing.address}
                className="w-full h-[110px] object-cover"
              />
              <div className="p-2.5">
                <p className="font-serif text-[15px] font-bold text-[#1B365D] mb-0.5 truncate">
                  {listing.price}
                </p>
                <p className="text-[11px] font-medium text-stone-800 truncate mb-1">
                  {listing.address}
                </p>
                <p className="text-[10px] text-stone-500">
                  {listing.beds}bd / {listing.baths}ba
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
              New inventory is hitting the market faster than usual this spring. Move quickly on properties under $1M — they&apos;re typically under contract within two weeks.
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
