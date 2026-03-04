import { EmailHeader } from './email-header';
import { EmailFooter } from './email-footer';

const sampleListings = [
  {
    image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop',
    price: '$2,150,000',
    address: '3021 Sunset Boulevard',
    location: 'Silver Lake, 90039',
    beds: 4,
    baths: 3.5,
    sqft: '2,800',
  },
  {
    image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop',
    price: '$1,295,000',
    address: '2847 Waverly Drive',
    location: 'Silver Lake, 90039',
    beds: 3,
    baths: 2,
    sqft: '1,850',
  },
  {
    image: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
    price: '$1,100,000',
    address: '3340 Silver Lake Blvd',
    location: 'Silver Lake, 90039',
    beds: 4,
    baths: 3,
    sqft: '2,400',
  },
  {
    image: 'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=600&h=400&fit=crop',
    price: '$875,000',
    address: '1420 Micheltorena St',
    location: 'Silver Lake, 90026',
    beds: 2,
    baths: 2,
    sqft: '1,200',
  },
  {
    image: 'https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=600&h=400&fit=crop',
    price: '$780,000',
    address: '2100 Griffith Park Blvd',
    location: 'Silver Lake, 90039',
    beds: 2,
    baths: 2,
    sqft: '1,100',
  },
  {
    image: 'https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600&h=400&fit=crop',
    price: '$725,000',
    address: '1847 Lucile Avenue',
    location: 'Silver Lake, 90026',
    beds: 2,
    baths: 1,
    sqft: '980',
  },
  {
    image: 'https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=600&h=400&fit=crop',
    price: '$599,000',
    address: '915 Hyperion Avenue',
    location: 'Silver Lake, 90027',
    beds: 2,
    baths: 1,
    sqft: '950',
  },
  {
    image: 'https://images.unsplash.com/photo-1600566752355-35792bedcfea?w=600&h=400&fit=crop',
    price: '$549,000',
    address: '2456 Riverside Drive',
    location: 'Silver Lake, 90039',
    beds: 1,
    baths: 1,
    sqft: '720',
  },
];

export function LargeListLayout() {
  return (
    <div className="font-sans">
      <EmailHeader
        reportType="New Listings"
        title="All New Listings – Silver Lake"
      />

      {/* Main Content */}
      <div className="bg-white px-10 py-10">
        {/* AI Narrative */}
        <div className="mb-8">
          <p className="text-[16px] leading-[1.8] text-stone-900">
            Eight new listings hit the Silver Lake market this week, ranging from a $549K starter condo to a $2.15M contemporary showpiece. Here&apos;s everything that&apos;s fresh on the market.
          </p>
        </div>

        {/* Gallery Count Badge */}
        <div className="flex items-center gap-3 mb-6">
          <span className="inline-flex items-center justify-center px-4 py-1.5 bg-[#1B365D] text-white text-sm font-bold rounded-full">
            8
          </span>
          <span className="text-sm font-semibold text-stone-900">New Listings</span>
          <div className="flex-1 h-px bg-stone-200" />
        </div>

        {/* Property Rows - Photo Left, Details Right */}
        <div className="border border-stone-200 rounded-xl overflow-hidden mb-10">
          {sampleListings.map((listing, idx) => (
            <div
              key={idx}
              className={`flex items-stretch ${
                idx !== sampleListings.length - 1 ? 'border-b border-stone-100' : ''
              }`}
            >
              {/* Photo */}
              <div className="flex-shrink-0 w-[160px]">
                <img
                  src={listing.image}
                  alt={listing.address}
                  className="w-full h-[120px] object-cover"
                />
              </div>
              
              {/* Details */}
              <div className="flex-1 p-4 flex flex-col justify-center">
                <p className="font-serif text-[18px] font-bold text-[#1B365D] mb-1">
                  {listing.price}
                </p>
                <p className="text-[14px] font-semibold text-stone-900 mb-0.5">
                  {listing.address}
                </p>
                <p className="text-[12px] text-stone-500 mb-2">
                  {listing.location}
                </p>
                <p className="text-[11px] text-stone-600">
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
              The under-$800K segment is particularly active this week. If you&apos;re a first-time buyer or investor, these properties won&apos;t last long in today&apos;s competitive market.
            </p>
          </div>
        </div>

        {/* CTA Button */}
        <div className="bg-[#1B365D]/5 rounded-lg p-6 text-center mb-6">
          <a
            href="#"
            className="inline-block bg-[#1B365D] text-white font-semibold text-sm px-10 py-4 rounded-lg hover:bg-[#152a4a] transition"
          >
            View Full Report
          </a>
        </div>

        <EmailFooter />
      </div>
    </div>
  );
}
