import { EmailHeader } from './email-header';
import { EmailFooter } from './email-footer';

const sampleListings = [
  {
    image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop',
    price: '$1,295,000',
    address: '2847 Waverly Dr',
    location: 'Silver Lake',
    beds: 3,
    baths: 2,
    sqft: '1,850',
  },
  {
    image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop',
    price: '$875,000',
    address: '1420 Micheltorena St',
    location: 'Silver Lake',
    beds: 2,
    baths: 2,
    sqft: '1,200',
  },
  {
    image: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
    price: '$2,150,000',
    address: '3021 Sunset Blvd',
    location: 'Silver Lake',
    beds: 4,
    baths: 3.5,
    sqft: '2,800',
  },
  {
    image: 'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=600&h=400&fit=crop',
    price: '$599,000',
    address: '915 Hyperion Ave',
    location: 'Silver Lake',
    beds: 2,
    baths: 1,
    sqft: '950',
  },
];

export function MarketNarrativeLayout() {
  return (
    <div className="font-sans">
      <EmailHeader
        reportType="Market Snapshot"
        title="Silver Lake Market Report"
      />

      {/* Main Content */}
      <div className="bg-white px-10 py-10">
        {/* AI Narrative - THE HOOK */}
        <div className="mb-10">
          <p className="text-[16px] leading-[1.8] text-stone-900">
            Silver Lake&apos;s housing market heated up this month with a 12% jump in median sale prices, fueled by razor-thin inventory below the $1M mark. Three homes on Hyperion Avenue alone sold above asking in the last 30 days — a signal that buyer competition is intensifying heading into spring. If you&apos;ve been considering listing, the window of peak demand is approaching fast. For sellers, the current market dynamics create an ideal window to maximize your return.
          </p>
        </div>

        {/* HERO STAT - One massive number */}
        <div className="text-center py-10 mb-8">
          <p className="font-serif text-[56px] font-bold text-[#1B365D] leading-none mb-2">
            $925,000
          </p>
          <p className="text-[11px] uppercase tracking-wider text-stone-500 font-medium mb-2">
            Median Sale Price
          </p>
          <p className="text-[13px] text-emerald-600 font-semibold">
            <span className="inline-block mr-1">&#9650;</span> 8.2% vs last year
          </p>
        </div>

        {/* 2x2 Photo Grid */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-5">
            <span className="inline-flex items-center justify-center w-8 h-8 bg-[#1B365D] text-white text-sm font-bold rounded-full">
              4
            </span>
            <span className="text-sm font-semibold text-stone-900">Notable Sales</span>
            <div className="flex-1 h-px bg-stone-200" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            {sampleListings.map((listing, idx) => (
              <div key={idx} className="bg-white rounded-lg border border-stone-200 overflow-hidden">
                <img
                  src={listing.image}
                  alt={listing.address}
                  className="w-full h-[160px] object-cover"
                />
                <div className="p-3">
                  <p className="font-serif text-[18px] font-bold text-[#1B365D] mb-1">
                    {listing.price}
                  </p>
                  <p className="text-[13px] font-semibold text-stone-900 truncate">
                    {listing.address}
                  </p>
                  <p className="text-[11px] text-stone-500 mb-2">
                    {listing.location}
                  </p>
                  <div className="flex gap-1">
                    <span className="inline-block px-2 py-0.5 bg-[#1B365D]/8 rounded text-[10px] font-medium text-[#1B365D]">
                      {listing.beds} Bed
                    </span>
                    <span className="inline-block px-2 py-0.5 bg-[#1B365D]/8 rounded text-[10px] font-medium text-[#1B365D]">
                      {listing.baths} Bath
                    </span>
                    <span className="inline-block px-2 py-0.5 bg-[#1B365D]/8 rounded text-[10px] font-medium text-[#1B365D]">
                      {listing.sqft} SF
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Secondary Stats - Stacked Vertically */}
        <div className="mb-10">
          <div className="border-t border-stone-200">
            <div className="flex justify-between items-center py-4 border-b border-stone-100">
              <span className="text-sm text-stone-600">Active Listings</span>
              <span className="font-serif text-2xl font-bold text-stone-900">42</span>
            </div>
            <div className="flex justify-between items-center py-4 border-b border-stone-100">
              <span className="text-sm text-stone-600">Avg Days on Market</span>
              <span className="font-serif text-2xl font-bold text-stone-900">24</span>
            </div>
            <div className="flex justify-between items-center py-4">
              <span className="text-sm text-stone-600">Sale-to-List Ratio</span>
              <span className="font-serif text-2xl font-bold text-stone-900">101.3%</span>
            </div>
          </div>
        </div>

        {/* Quick Take Callout */}
        <div className="bg-[#B8860B]/8 border border-[#B8860B]/25 rounded-lg p-5 mb-8">
          <div className="flex items-start gap-3">
            <span className="text-[#B8860B] text-xl">$</span>
            <p className="text-sm font-medium text-stone-900 leading-relaxed">
              Sellers are firmly in control. With only 2.1 months of inventory and prices averaging 101% of asking, well-priced homes in Silver Lake are moving fast.
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
