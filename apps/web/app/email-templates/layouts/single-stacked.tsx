import { EmailHeader } from './email-header';
import { EmailFooter } from './email-footer';

const sampleListings = [
  {
    image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&h=450&fit=crop',
    price: '$2,150,000',
    address: '3021 Sunset Boulevard',
    location: 'Silver Lake, CA 90039',
    beds: 4,
    baths: 3.5,
    sqft: '2,800',
    year: 2024,
    description: 'Stunning contemporary home with panoramic city views, chef\'s kitchen with premium appliances, and a resort-style backyard.',
  },
  {
    image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&h=450&fit=crop',
    price: '$1,295,000',
    address: '2847 Waverly Drive',
    location: 'Silver Lake, CA 90039',
    beds: 3,
    baths: 2,
    sqft: '1,850',
    year: 1928,
    description: 'Beautifully renovated Craftsman with original details preserved, light-filled living spaces, and a tranquil garden oasis.',
  },
  {
    image: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800&h=450&fit=crop',
    price: '$875,000',
    address: '1420 Micheltorena Street',
    location: 'Silver Lake, CA 90026',
    beds: 2,
    baths: 2,
    sqft: '1,200',
    year: 2019,
    description: 'Modern townhome with an open floor plan, private rooftop deck, and walkable access to Sunset Junction shops.',
  },
];

export function SingleStackedLayout() {
  return (
    <div className="font-sans">
      <EmailHeader
        reportType="Featured Listings"
        title="Luxury Homes – Silver Lake"
      />

      {/* Main Content */}
      <div className="bg-white px-10 py-10">
        {/* AI Narrative - 2-3 sentences */}
        <div className="mb-10">
          <p className="text-[16px] leading-[1.8] text-stone-900">
            Three exceptional properties that define Silver Lake living. From a stunning contemporary masterpiece to a lovingly restored Craftsman, these homes represent the pinnacle of what this iconic neighborhood has to offer.
          </p>
        </div>

        {/* Property Cards - Full Width Stacked */}
        <div className="space-y-6 mb-10">
          {sampleListings.map((listing, idx) => (
            <div key={idx}>
              {/* Property Card */}
              <div className="rounded-xl border border-stone-200 overflow-hidden shadow-sm">
                {/* Hero Image - Full Width */}
                <img
                  src={listing.image}
                  alt={listing.address}
                  className="w-full h-[240px] object-cover"
                />
                
                {/* Property Details */}
                <div className="p-5">
                  <p className="font-serif text-[22px] font-bold text-[#1B365D] mb-1">
                    {listing.price}
                  </p>
                  <p className="text-[15px] font-semibold text-stone-900 mb-0.5">
                    {listing.address}
                  </p>
                  <p className="text-[12px] text-stone-500 mb-4">
                    {listing.location}
                  </p>
                  
                  {/* Badges Row */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    <span className="inline-block px-3 py-1 bg-[#1B365D]/8 rounded-md text-[11px] font-medium text-[#1B365D]">
                      {listing.beds} Bed
                    </span>
                    <span className="inline-block px-3 py-1 bg-[#1B365D]/8 rounded-md text-[11px] font-medium text-[#1B365D]">
                      {listing.baths} Bath
                    </span>
                    <span className="inline-block px-3 py-1 bg-[#1B365D]/8 rounded-md text-[11px] font-medium text-[#1B365D]">
                      {listing.sqft} SF
                    </span>
                    <span className="inline-block px-3 py-1 bg-[#1B365D]/8 rounded-md text-[11px] font-medium text-[#1B365D]">
                      Built {listing.year}
                    </span>
                  </div>
                  
                  {/* Description */}
                  <p className="text-[13px] text-stone-600 leading-relaxed italic">
                    &ldquo;{listing.description}&rdquo;
                  </p>
                </div>
              </div>
              
              {/* Branded Divider */}
              {idx < sampleListings.length - 1 && (
                <div className="flex items-center justify-center py-4">
                  <div className="w-16 h-0.5 bg-gradient-to-r from-[#1B365D] to-[#B8860B] rounded-full" />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* CTA Button */}
        <div className="bg-[#1B365D]/5 rounded-lg p-6 text-center mb-6">
          <a
            href="#"
            className="inline-block bg-[#1B365D] text-white font-semibold text-sm px-10 py-4 rounded-lg hover:bg-[#152a4a] transition"
          >
            Schedule a Private Showing
          </a>
        </div>

        <EmailFooter />
      </div>
    </div>
  );
}
