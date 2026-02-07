import React from "react"
import {
  BarChart3,
  TrendingUp,
  Clock,
  Layers,
  Home,
  Building2,
  Warehouse,
  DollarSign,
  ArrowUpRight,
  Activity,
} from "lucide-react";

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-4 flex items-center gap-2">
      <div className="h-0.5 w-5 rounded-full bg-[#1e3a5f]" />
      <span className="text-xs font-semibold uppercase tracking-widest text-[#1e3a5f]">
        {children}
      </span>
    </div>
  );
}

export function MarketSnapshot() {
  return (
    <div className="px-8 py-8">
      {/* AI Insight */}
      <div className="mb-8 rounded-lg border-l-4 border-[#1e3a5f] bg-[#1e3a5f]/[0.04] px-5 py-4">
        <p className="text-sm leading-relaxed text-foreground/80">
          Healthy activity in Los Angeles this month&mdash;142 families found
          their new home at a median price of $875K. With homes averaging 34
          days on market, there&apos;s time to explore without missing out.
        </p>
      </div>

      {/* Hero Metric */}
      <div className="mb-8 rounded-xl border border-[#1e3a5f]/10 bg-gradient-to-br from-[#1e3a5f]/[0.06] to-transparent p-6 text-center">
        <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-[#1e3a5f]/70">
          Median Sale Price
        </p>
        <p className="font-serif text-5xl font-bold tracking-tight text-[#1e3a5f]">
          $875K
        </p>
        <div className="mx-auto mt-3 h-1 w-12 rounded-full bg-[#b8860b]" />
      </div>

      {/* Key Metrics Row */}
      <div className="mb-8 grid grid-cols-3 gap-3">
        {[
          { value: "142", label: "Closed Sales", icon: BarChart3 },
          { value: "34", label: "Avg Days on Market", icon: Clock },
          { value: "2.8", label: "Months of Inventory", icon: Layers },
        ].map((metric) => (
          <div
            key={metric.label}
            className="rounded-lg border border-border bg-card p-4 text-center"
          >
            <div className="mb-2 flex justify-center">
              <metric.icon className="h-4 w-4 text-[#b8860b]" />
            </div>
            <p className="font-serif text-2xl font-bold text-foreground">
              {metric.value}
            </p>
            <p className="mt-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              {metric.label}
            </p>
          </div>
        ))}
      </div>

      {/* Market Activity */}
      <div className="mb-8">
        <SectionLabel>Market Activity</SectionLabel>
        <div className="rounded-lg border border-border bg-card">
          <div className="grid grid-cols-3 divide-x divide-border">
            {[
              { value: "89", label: "New Listings", icon: TrendingUp },
              { value: "67", label: "Pending Sales", icon: Activity },
              { value: "96.2%", label: "Sale-to-List Ratio", icon: ArrowUpRight },
            ].map((stat) => (
              <div key={stat.label} className="px-4 py-4 text-center">
                <div className="mb-1.5 flex justify-center">
                  <stat.icon className="h-3.5 w-3.5 text-[#1e3a5f]/50" />
                </div>
                <p className="text-lg font-bold text-foreground">
                  {stat.value}
                </p>
                <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Property Type & Price Tier */}
      <div className="mb-8 grid grid-cols-2 gap-4">
        {/* Property Type Breakdown */}
        <div className="rounded-lg border border-border bg-card p-5">
          <SectionLabel>By Property Type</SectionLabel>
          <div className="flex flex-col gap-3">
            {[
              { type: "Single Family", count: 98, icon: Home },
              { type: "Condos", count: 31, icon: Building2 },
              { type: "Townhomes", count: 13, icon: Warehouse },
            ].map((item) => (
              <div
                key={item.type}
                className="flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <item.icon className="h-3.5 w-3.5 text-[#1e3a5f]/40" />
                  <span className="text-sm text-foreground">{item.type}</span>
                </div>
                <span className="text-sm font-bold text-foreground">
                  {item.count}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Price Tier Breakdown */}
        <div className="rounded-lg border border-border bg-card p-5">
          <SectionLabel>By Price Range</SectionLabel>
          <div className="flex flex-col gap-3">
            {[
              {
                tier: "Entry Level",
                count: 42,
                sub: "Under $500K",
                width: "30%",
              },
              {
                tier: "Move-Up",
                count: 67,
                sub: "$500K - $1M",
                width: "47%",
              },
              { tier: "Luxury", count: 33, sub: "$1M+", width: "23%" },
            ].map((item) => (
              <div key={item.tier}>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-foreground">{item.tier}</span>
                  <span className="text-sm font-bold text-foreground">
                    {item.count}
                  </span>
                </div>
                <div className="mt-1.5 flex items-center gap-2">
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-[#1e3a5f]"
                      style={{ width: item.width }}
                    />
                  </div>
                  <span className="text-[10px] text-muted-foreground">
                    {item.sub}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
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
          View Full Report
        </a>
      </div>
    </div>
  );
}
