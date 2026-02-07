import {
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  DollarSign,
} from "lucide-react";

const RECENT_SALES = [
  {
    address: "742 Sunset Blvd",
    zip: "90028",
    beds: 4,
    baths: 3,
    sqft: "2,800",
    listPrice: "$1,295,000",
    salePrice: "$1,250,000",
    dom: 18,
    ratio: 96.5,
    trend: "down" as const,
  },
  {
    address: "1831 Echo Park Ave",
    zip: "90026",
    beds: 2,
    baths: 2,
    sqft: "1,200",
    listPrice: "$675,000",
    salePrice: "$689,000",
    dom: 7,
    ratio: 102.1,
    trend: "up" as const,
  },
  {
    address: "4521 Franklin Ave",
    zip: "90027",
    beds: 3,
    baths: 2,
    sqft: "1,650",
    listPrice: "$949,000",
    salePrice: "$925,000",
    dom: 22,
    ratio: 97.5,
    trend: "down" as const,
  },
  {
    address: "2200 Beachwood Dr",
    zip: "90068",
    beds: 5,
    baths: 4,
    sqft: "3,200",
    listPrice: "$1,499,000",
    salePrice: "$1,475,000",
    dom: 31,
    ratio: 98.4,
    trend: "down" as const,
  },
  {
    address: "915 Hyperion Ave",
    zip: "90029",
    beds: 2,
    baths: 1,
    sqft: "950",
    listPrice: "$585,000",
    salePrice: "$599,000",
    dom: 5,
    ratio: 102.4,
    trend: "up" as const,
  },
  {
    address: "3340 Waverly Dr",
    zip: "90027",
    beds: 4,
    baths: 3,
    sqft: "2,400",
    listPrice: "$1,125,000",
    salePrice: "$1,100,000",
    dom: 14,
    ratio: 97.8,
    trend: "down" as const,
  },
  {
    address: "507 Micheltorena St",
    zip: "90026",
    beds: 3,
    baths: 2,
    sqft: "1,480",
    listPrice: "$799,000",
    salePrice: "$799,000",
    dom: 11,
    ratio: 100.0,
    trend: "neutral" as const,
  },
  {
    address: "1945 Griffith Park Blvd",
    zip: "90039",
    beds: 3,
    baths: 2,
    sqft: "1,750",
    listPrice: "$879,000",
    salePrice: "$892,000",
    dom: 9,
    ratio: 101.5,
    trend: "up" as const,
  },
];

function TrendIcon({ trend }: { trend: "up" | "down" | "neutral" }) {
  if (trend === "up")
    return <ArrowUpRight className="h-3.5 w-3.5 text-emerald-600" />;
  if (trend === "down")
    return <ArrowDownRight className="h-3.5 w-3.5 text-red-500" />;
  return <Minus className="h-3.5 w-3.5 text-muted-foreground" />;
}

function RatioBadge({ ratio }: { ratio: number }) {
  let bgColor = "bg-muted text-muted-foreground";
  if (ratio >= 100) bgColor = "bg-emerald-50 text-emerald-700";
  else if (ratio < 97) bgColor = "bg-red-50 text-red-600";

  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${bgColor}`}
    >
      {ratio.toFixed(1)}%
    </span>
  );
}

export function TableView() {
  return (
    <div className="px-6 py-8">
      {/* AI Insight */}
      <div className="mb-8 rounded-lg border-l-4 border-[#1e3a5f] bg-[#1e3a5f]/[0.04] px-5 py-4">
        <p className="text-sm leading-relaxed text-foreground/80">
          8 closed sales in the last 30 days across Los Angeles. Average
          sale-to-list ratio of 99.5% with a median of 12.5 days on
          market&mdash;homes are moving quickly in this area.
        </p>
      </div>

      {/* Summary Stats Row */}
      <div className="mb-6 grid grid-cols-4 gap-2">
        {[
          { label: "Total Sales", value: "8" },
          { label: "Avg Sale Price", value: "$966K" },
          { label: "Avg DOM", value: "14.6" },
          { label: "Avg Ratio", value: "99.5%" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-lg border border-border bg-card p-3 text-center"
          >
            <p className="font-serif text-lg font-bold text-[#1e3a5f]">
              {stat.value}
            </p>
            <p className="mt-0.5 text-[9px] font-semibold uppercase tracking-wider text-muted-foreground">
              {stat.label}
            </p>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="mb-8 overflow-hidden rounded-lg border border-border">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-[#1e3a5f]">
              <th className="px-3 py-3 text-[10px] font-semibold uppercase tracking-wider text-white">
                Address
              </th>
              <th className="px-2 py-3 text-center text-[10px] font-semibold uppercase tracking-wider text-white">
                Bd/Ba
              </th>
              <th className="px-2 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-white">
                Sale Price
              </th>
              <th className="px-2 py-3 text-center text-[10px] font-semibold uppercase tracking-wider text-white">
                DOM
              </th>
              <th className="px-3 py-3 text-center text-[10px] font-semibold uppercase tracking-wider text-white">
                Ratio
              </th>
            </tr>
          </thead>
          <tbody>
            {RECENT_SALES.map((sale, idx) => (
              <tr
                key={sale.address}
                className={`border-t border-border ${idx % 2 === 0 ? "bg-card" : "bg-muted/40"}`}
              >
                <td className="px-3 py-2.5">
                  <p className="text-xs font-semibold text-foreground">
                    {sale.address}
                  </p>
                  <p className="mt-0.5 text-[10px] text-muted-foreground">
                    {sale.zip} &middot; {sale.sqft} SF
                  </p>
                </td>
                <td className="px-2 py-2.5 text-center text-xs text-foreground">
                  {sale.beds}/{sale.baths}
                </td>
                <td className="px-2 py-2.5 text-right">
                  <p className="text-xs font-semibold text-foreground">
                    {sale.salePrice}
                  </p>
                  <p className="mt-0.5 text-[10px] text-muted-foreground line-through">
                    {sale.listPrice}
                  </p>
                </td>
                <td className="px-2 py-2.5 text-center text-xs text-foreground">
                  {sale.dom}d
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center justify-center gap-1">
                    <RatioBadge ratio={sale.ratio} />
                    <TrendIcon trend={sale.trend} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Quick Take Callout */}
      <div className="mb-8 rounded-lg border border-[#b8860b]/20 bg-[#b8860b]/[0.06] p-5">
        <div className="flex items-start gap-3">
          <DollarSign className="mt-0.5 h-5 w-5 shrink-0 text-[#b8860b]" />
          <p className="text-sm font-medium leading-relaxed text-foreground">
            Properties priced under $800K are moving fastest with an average of
            just 7 days on market and above-ask offers.
          </p>
        </div>
      </div>

      {/* CTA */}
      <div className="rounded-lg bg-[#1e3a5f]/[0.04] px-6 py-6 text-center">
        <a
          href="#"
          className="inline-block rounded-lg bg-[#1e3a5f] px-8 py-3.5 text-sm font-semibold tracking-wide text-white transition-opacity hover:opacity-90"
        >
          View All Recent Sales
        </a>
      </div>
    </div>
  );
}
