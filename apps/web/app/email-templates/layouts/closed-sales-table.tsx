import { EmailHeader } from './email-header';
import { EmailFooter } from './email-footer';

const notableSales = [
  {
    image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop',
    price: '$2,150,000',
    address: '3021 Sunset Blvd',
    beds: 4,
    baths: 3.5,
  },
  {
    image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop',
    price: '$1,295,000',
    address: '2847 Waverly Dr',
    beds: 3,
    baths: 2,
  },
  {
    image: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
    price: '$1,100,000',
    address: '3340 Silver Lake',
    beds: 4,
    baths: 3,
  },
  {
    image: 'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=600&h=400&fit=crop',
    price: '$875,000',
    address: '1420 Micheltorena',
    beds: 2,
    baths: 2,
  },
];

const salesTable = [
  { address: '3021 Sunset Blvd', bedBath: '4/3.5', price: '$2,150,000', dom: 8 },
  { address: '2847 Waverly Dr', bedBath: '3/2', price: '$1,295,000', dom: 12 },
  { address: '3340 Silver Lake Blvd', bedBath: '4/3', price: '$1,100,000', dom: 21 },
  { address: '1420 Micheltorena St', bedBath: '2/2', price: '$875,000', dom: 14 },
  { address: '2100 Griffith Park Blvd', bedBath: '2/2', price: '$780,000', dom: 18 },
  { address: '1847 Lucile Ave', bedBath: '2/1', price: '$725,000', dom: 9 },
  { address: '915 Hyperion Ave', bedBath: '2/1', price: '$599,000', dom: 6 },
  { address: '2456 Riverside Dr', bedBath: '1/1', price: '$549,000', dom: 23 },
];

export function ClosedSalesTableLayout() {
  return (
    <div className="font-sans">
      <EmailHeader
        reportType="Closed Sales"
        title="Recent Sales – Silver Lake"
      />

      {/* Main Content */}
      <div className="bg-white px-10 py-10">
        {/* AI Narrative - 3-4 sentences */}
        <div className="mb-8">
          <p className="text-[16px] leading-[1.8] text-stone-900">
            Silver Lake saw 8 homes close escrow this month, totaling $9.07M in sales volume. The median sale price came in at $875K, with properties spending an average of just 14 days on market. Three homes sold above asking price, signaling continued buyer demand in the neighborhood.
          </p>
        </div>

        {/* HERO STAT */}
        <div className="text-center py-8 mb-8 bg-stone-50 rounded-xl">
          <p className="font-serif text-[48px] font-bold text-[#1B365D] leading-none mb-2">
            8
          </p>
          <p className="text-[11px] uppercase tracking-wider text-stone-500 font-medium">
            Homes Sold This Month
          </p>
        </div>

        {/* 2x2 Photo Grid - Notable Sales with SOLD badge */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-5">
            <span className="inline-flex items-center justify-center w-8 h-8 bg-[#1B365D] text-white text-sm font-bold rounded-full">
              4
            </span>
            <span className="text-sm font-semibold text-stone-900">Notable Sales</span>
            <div className="flex-1 h-px bg-stone-200" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            {notableSales.map((sale, idx) => (
              <div key={idx} className="bg-white rounded-lg border border-stone-200 overflow-hidden">
                <div className="relative">
                  <img
                    src={sale.image}
                    alt={sale.address}
                    className="w-full h-[130px] object-cover"
                  />
                  {/* SOLD Badge */}
                  <span className="absolute top-2 left-2 bg-[#B8860B] text-white text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded">
                    Sold
                  </span>
                </div>
                <div className="p-3">
                  <p className="font-serif text-[16px] font-bold text-[#1B365D] mb-0.5">
                    {sale.price}
                  </p>
                  <p className="text-[12px] font-medium text-stone-800 truncate">
                    {sale.address}
                  </p>
                  <p className="text-[10px] text-stone-500">
                    {sale.beds}bd / {sale.baths}ba
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Data Table */}
        <div className="mb-10">
          <div className="rounded-xl overflow-hidden border border-stone-200">
            {/* Table Header */}
            <div className="bg-[#1B365D] text-white">
              <div className="grid grid-cols-4 text-[11px] font-semibold uppercase tracking-wider">
                <div className="px-4 py-3">Address</div>
                <div className="px-4 py-3 text-center">Bd/Ba</div>
                <div className="px-4 py-3 text-right">Sale Price</div>
                <div className="px-4 py-3 text-right">DOM</div>
              </div>
            </div>
            
            {/* Table Rows */}
            {salesTable.map((row, idx) => (
              <div
                key={idx}
                className={`grid grid-cols-4 text-[13px] ${
                  idx % 2 === 0 ? 'bg-white' : 'bg-stone-50'
                }`}
              >
                <div className="px-4 py-3 font-medium text-stone-900 truncate">
                  {row.address}
                </div>
                <div className="px-4 py-3 text-center text-stone-600">
                  {row.bedBath}
                </div>
                <div className="px-4 py-3 text-right font-serif font-semibold text-[#1B365D]">
                  {row.price}
                </div>
                <div className="px-4 py-3 text-right text-stone-600">
                  {row.dom}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Take Callout */}
        <div className="bg-[#B8860B]/8 border border-[#B8860B]/25 rounded-lg p-5 mb-8">
          <div className="flex items-start gap-3">
            <span className="text-[#B8860B] text-xl">$</span>
            <p className="text-sm font-medium text-stone-900 leading-relaxed">
              Properties under $800K are moving fastest, with an average of just 11 days on market. If you&apos;re thinking of selling, now is an excellent time to capitalize on buyer urgency.
            </p>
          </div>
        </div>

        {/* CTA Button */}
        <div className="bg-[#1B365D]/5 rounded-lg p-6 text-center mb-6">
          <a
            href="#"
            className="inline-block bg-[#1B365D] text-white font-semibold text-sm px-10 py-4 rounded-lg hover:bg-[#152a4a] transition"
          >
            Get Your Home&apos;s Value
          </a>
        </div>

        <EmailFooter />
      </div>
    </div>
  );
}
