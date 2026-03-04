import { EmailHeader } from './email-header';
import { EmailFooter } from './email-footer';

export function MarketAnalyticsLayout() {
  return (
    <div className="font-sans">
      <EmailHeader
        reportType="Market Analytics"
        title="Year-Over-Year Trends – Silver Lake"
      />

      {/* Main Content */}
      <div className="bg-white px-10 py-10">
        {/* AI Narrative - 4-6 sentences, most detailed */}
        <div className="mb-10">
          <p className="text-[16px] leading-[1.8] text-stone-900">
            Silver Lake&apos;s housing market heated up this month with a 12% jump in median sale prices, fueled by razor-thin inventory below the $1M mark. The neighborhood has seen inventory drop 12% compared to this time last year, creating urgency among buyers and driving sale-to-list ratios above 100%. Three homes on Hyperion Avenue alone sold above asking in the last 30 days — a signal that buyer competition is intensifying heading into spring. If you&apos;ve been considering listing, the window of peak demand is approaching fast.
          </p>
        </div>

        {/* HERO STAT with Trend */}
        <div className="text-center py-10 mb-8 bg-stone-50 rounded-xl">
          <p className="font-serif text-[56px] font-bold text-[#1B365D] leading-none mb-2">
            $925,000
          </p>
          <p className="text-[13px] text-emerald-600 font-semibold mb-1">
            <span className="inline-block mr-1">&#9650;</span> 8.2% vs last year
          </p>
          <p className="text-[11px] uppercase tracking-wider text-stone-500 font-medium">
            Median Sale Price
          </p>
        </div>

        {/* Stacked Stats with Trend Indicators */}
        <div className="mb-10">
          <div className="border border-stone-200 rounded-xl overflow-hidden">
            {/* Stat Row 1 */}
            <div className="flex items-center justify-between px-5 py-4 bg-white">
              <span className="text-sm text-stone-600">Active Listings</span>
              <div className="flex items-center gap-3">
                <span className="font-serif text-2xl font-bold text-stone-900">42</span>
                <span className="text-xs font-semibold text-red-500 flex items-center">
                  <span className="mr-0.5">&#9660;</span> 12% vs last year
                </span>
              </div>
            </div>
            
            {/* Stat Row 2 */}
            <div className="flex items-center justify-between px-5 py-4 bg-stone-50">
              <span className="text-sm text-stone-600">Days on Market</span>
              <div className="flex items-center gap-3">
                <span className="font-serif text-2xl font-bold text-stone-900">24</span>
                <span className="text-xs font-semibold text-emerald-600 flex items-center">
                  <span className="mr-0.5">&#9650;</span> 3 days faster
                </span>
              </div>
            </div>
            
            {/* Stat Row 3 */}
            <div className="flex items-center justify-between px-5 py-4 bg-white">
              <span className="text-sm text-stone-600">Inventory Months</span>
              <div className="flex items-center gap-3">
                <span className="font-serif text-2xl font-bold text-stone-900">2.1</span>
                <span className="text-xs font-semibold text-[#B8860B] flex items-center">
                  <span className="mr-0.5">&rarr;</span> Seller&apos;s Market
                </span>
              </div>
            </div>
            
            {/* Stat Row 4 */}
            <div className="flex items-center justify-between px-5 py-4 bg-stone-50">
              <span className="text-sm text-stone-600">Sale-to-List Ratio</span>
              <div className="flex items-center gap-3">
                <span className="font-serif text-2xl font-bold text-stone-900">101.3%</span>
                <span className="text-xs font-semibold text-emerald-600 flex items-center">
                  <span className="mr-0.5">&#9650;</span> Above asking
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Before/After Comparison Card */}
        <div className="mb-10">
          <p className="text-xs font-semibold uppercase tracking-wider text-stone-500 mb-3">Year-Over-Year Comparison</p>
          <div className="grid grid-cols-2 rounded-xl overflow-hidden border border-stone-200">
            {/* Last Year Column */}
            <div className="bg-stone-100 p-5 border-r border-stone-200">
              <p className="text-xs font-semibold uppercase tracking-wider text-stone-500 mb-4">Last Year</p>
              <div className="space-y-4">
                <div>
                  <p className="font-serif text-xl font-bold text-stone-500">$855K</p>
                  <p className="text-xs text-stone-400">Median Price</p>
                </div>
                <div>
                  <p className="font-serif text-xl font-bold text-stone-500">48</p>
                  <p className="text-xs text-stone-400">Active Listings</p>
                </div>
                <div>
                  <p className="font-serif text-xl font-bold text-stone-500">28</p>
                  <p className="text-xs text-stone-400">Avg DOM</p>
                </div>
              </div>
            </div>
            
            {/* This Year Column */}
            <div className="bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-[#1B365D] mb-4">This Year</p>
              <div className="space-y-4">
                <div>
                  <p className="font-serif text-xl font-bold text-[#1B365D]">$925K</p>
                  <p className="text-xs text-stone-500">Median Price</p>
                </div>
                <div>
                  <p className="font-serif text-xl font-bold text-[#1B365D]">42</p>
                  <p className="text-xs text-stone-500">Active Listings</p>
                </div>
                <div>
                  <p className="font-serif text-xl font-bold text-[#1B365D]">24</p>
                  <p className="text-xs text-stone-500">Avg DOM</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Take Callout */}
        <div className="bg-[#B8860B]/8 border border-[#B8860B]/25 rounded-lg p-5 mb-8">
          <div className="flex items-start gap-3">
            <span className="text-[#B8860B] text-xl">$</span>
            <p className="text-sm font-medium text-stone-900 leading-relaxed">
              The data tells a clear story: prices are up, inventory is down, and homes are selling faster than last year. For sellers, this is an optimal window. For buyers, preparation and quick action are essential.
            </p>
          </div>
        </div>

        {/* CTA Button */}
        <div className="bg-[#1B365D]/5 rounded-lg p-6 text-center mb-6">
          <a
            href="#"
            className="inline-block bg-[#1B365D] text-white font-semibold text-sm px-10 py-4 rounded-lg hover:bg-[#152a4a] transition"
          >
            Get Your Free Home Valuation
          </a>
        </div>

        <EmailFooter />
      </div>
    </div>
  );
}
