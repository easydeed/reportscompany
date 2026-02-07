"use client";

import React from "react"

import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Activity,
  DollarSign,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  Cell,
} from "recharts";

const PRICE_TREND_DATA = [
  { month: "Mar", median: 810, avg: 845 },
  { month: "Apr", median: 825, avg: 860 },
  { month: "May", median: 840, avg: 870 },
  { month: "Jun", median: 855, avg: 885 },
  { month: "Jul", median: 862, avg: 890 },
  { month: "Aug", median: 870, avg: 900 },
  { month: "Sep", median: 858, avg: 892 },
  { month: "Oct", median: 845, avg: 878 },
  { month: "Nov", median: 850, avg: 882 },
  { month: "Dec", median: 860, avg: 895 },
  { month: "Jan", median: 868, avg: 905 },
  { month: "Feb", median: 875, avg: 912 },
];

const INVENTORY_DATA = [
  { month: "Mar", listings: 320, sold: 128 },
  { month: "Apr", listings: 345, sold: 135 },
  { month: "May", listings: 380, sold: 152 },
  { month: "Jun", listings: 410, sold: 168 },
  { month: "Jul", listings: 395, sold: 155 },
  { month: "Aug", listings: 370, sold: 148 },
  { month: "Sep", listings: 340, sold: 138 },
  { month: "Oct", listings: 310, sold: 125 },
  { month: "Nov", listings: 285, sold: 112 },
  { month: "Dec", listings: 260, sold: 98 },
  { month: "Jan", listings: 290, sold: 118 },
  { month: "Feb", listings: 315, sold: 142 },
];

const DOM_DATA = [
  { month: "Mar", dom: 38 },
  { month: "Apr", dom: 36 },
  { month: "May", dom: 33 },
  { month: "Jun", dom: 30 },
  { month: "Jul", dom: 28 },
  { month: "Aug", dom: 31 },
  { month: "Sep", dom: 33 },
  { month: "Oct", dom: 35 },
  { month: "Nov", dom: 37 },
  { month: "Dec", dom: 39 },
  { month: "Jan", dom: 36 },
  { month: "Feb", dom: 34 },
];

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

function StatCard({
  label,
  value,
  change,
  positive,
}: {
  label: string;
  value: string;
  change: string;
  positive: boolean;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <p className="mt-1.5 font-serif text-2xl font-bold text-foreground">
        {value}
      </p>
      <div className="mt-2 flex items-center gap-1">
        {positive ? (
          <TrendingUp className="h-3 w-3 text-emerald-600" />
        ) : (
          <TrendingDown className="h-3 w-3 text-red-500" />
        )}
        <span
          className={`text-[11px] font-semibold ${positive ? "text-emerald-600" : "text-red-500"}`}
        >
          {change}
        </span>
        <span className="text-[10px] text-muted-foreground">vs last yr</span>
      </div>
    </div>
  );
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-lg">
      <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2">
          <div
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-xs text-foreground">
            {entry.name}: <span className="font-semibold">{entry.value}</span>
          </span>
        </div>
      ))}
    </div>
  );
}

export function MarketAnalytics() {
  const NAVY = "#1e3a5f";
  const GOLD = "#b8860b";

  return (
    <div className="px-6 py-8">
      {/* AI Insight */}
      <div className="mb-8 rounded-lg border-l-4 border-[#1e3a5f] bg-[#1e3a5f]/[0.04] px-5 py-4">
        <p className="text-sm leading-relaxed text-foreground/80">
          Los Angeles home prices have risen 8% year-over-year, with median
          prices reaching $875K in February. Inventory remains tight at 2.8
          months, keeping upward pressure on values.
        </p>
      </div>

      {/* KPI Row */}
      <div className="mb-8 grid grid-cols-2 gap-3">
        <StatCard
          label="Median Price"
          value="$875K"
          change="+8.0%"
          positive={true}
        />
        <StatCard
          label="Avg Price"
          value="$912K"
          change="+7.9%"
          positive={true}
        />
        <StatCard
          label="Days on Market"
          value="34"
          change="-10.5%"
          positive={true}
        />
        <StatCard
          label="Active Listings"
          value="315"
          change="-1.6%"
          positive={false}
        />
      </div>

      {/* Price Trend Chart */}
      <div className="mb-8">
        <SectionLabel>Price Trends (12 Months)</SectionLabel>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="mb-3 flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <div
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: NAVY }}
              />
              <span className="text-[10px] font-medium text-muted-foreground">
                Median ($K)
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <div
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: GOLD }}
              />
              <span className="text-[10px] font-medium text-muted-foreground">
                Average ($K)
              </span>
            </div>
          </div>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={PRICE_TREND_DATA}
                margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient
                    id="medianGrad"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="5%" stopColor={NAVY} stopOpacity={0.15} />
                    <stop offset="95%" stopColor={NAVY} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="avgGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={GOLD} stopOpacity={0.15} />
                    <stop offset="95%" stopColor={GOLD} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e5e5e5"
                  vertical={false}
                />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 10, fill: "#888" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  domain={[780, 940]}
                  tick={{ fontSize: 10, fill: "#888" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="median"
                  name="Median"
                  stroke={NAVY}
                  strokeWidth={2}
                  fill="url(#medianGrad)"
                />
                <Area
                  type="monotone"
                  dataKey="avg"
                  name="Average"
                  stroke={GOLD}
                  strokeWidth={2}
                  fill="url(#avgGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Inventory vs Sold Chart */}
      <div className="mb-8">
        <SectionLabel>Inventory vs. Sold (12 Months)</SectionLabel>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="mb-3 flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <div
                className="h-2.5 w-2.5 rounded"
                style={{ backgroundColor: `${NAVY}40` }}
              />
              <span className="text-[10px] font-medium text-muted-foreground">
                New Listings
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <div
                className="h-2.5 w-2.5 rounded"
                style={{ backgroundColor: NAVY }}
              />
              <span className="text-[10px] font-medium text-muted-foreground">
                Sold
              </span>
            </div>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={INVENTORY_DATA}
                margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
                barGap={2}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e5e5e5"
                  vertical={false}
                />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 10, fill: "#888" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: "#888" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="listings"
                  name="Listings"
                  fill={`${NAVY}40`}
                  radius={[3, 3, 0, 0]}
                />
                <Bar
                  dataKey="sold"
                  name="Sold"
                  fill={NAVY}
                  radius={[3, 3, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Days on Market Chart */}
      <div className="mb-8">
        <SectionLabel>Avg. Days on Market (12 Months)</SectionLabel>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={DOM_DATA}
                margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e5e5e5"
                  vertical={false}
                />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 10, fill: "#888" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: "#888" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="dom" name="Days" radius={[3, 3, 0, 0]}>
                  {DOM_DATA.map((entry) => (
                    <Cell
                      key={entry.month}
                      fill={entry.dom <= 32 ? GOLD : NAVY}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-center text-[10px] text-muted-foreground">
            Gold bars indicate months with fastest absorption (under 32 days)
          </p>
        </div>
      </div>

      {/* Year-over-Year Comparison */}
      <div className="mb-8">
        <SectionLabel>Year-over-Year Comparison</SectionLabel>
        <div className="rounded-lg border border-border bg-card">
          <div className="grid grid-cols-4 border-b border-border bg-[#1e3a5f] text-center">
            <div className="px-2 py-2.5">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-white">
                Metric
              </span>
            </div>
            <div className="px-2 py-2.5">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-white">
                Last Year
              </span>
            </div>
            <div className="px-2 py-2.5">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-white">
                This Year
              </span>
            </div>
            <div className="px-2 py-2.5">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-white">
                Change
              </span>
            </div>
          </div>
          {[
            {
              metric: "Median Price",
              last: "$810K",
              current: "$875K",
              change: "+8.0%",
              positive: true,
            },
            {
              metric: "Closed Sales",
              last: "128",
              current: "142",
              change: "+10.9%",
              positive: true,
            },
            {
              metric: "Avg DOM",
              last: "38",
              current: "34",
              change: "-10.5%",
              positive: true,
            },
            {
              metric: "Sale/List Ratio",
              last: "95.1%",
              current: "96.2%",
              change: "+1.2%",
              positive: true,
            },
            {
              metric: "Inventory",
              last: "3.1 mo",
              current: "2.8 mo",
              change: "-9.7%",
              positive: false,
            },
          ].map((row, idx) => (
            <div
              key={row.metric}
              className={`grid grid-cols-4 border-b border-border text-center last:border-b-0 ${
                idx % 2 === 0 ? "bg-card" : "bg-muted/40"
              }`}
            >
              <div className="px-2 py-2.5 text-left">
                <span className="text-xs font-semibold text-foreground">
                  {row.metric}
                </span>
              </div>
              <div className="px-2 py-2.5">
                <span className="text-xs text-muted-foreground">
                  {row.last}
                </span>
              </div>
              <div className="px-2 py-2.5">
                <span className="text-xs font-semibold text-foreground">
                  {row.current}
                </span>
              </div>
              <div className="px-2 py-2.5">
                <div className="flex items-center justify-center gap-1">
                  {row.positive ? (
                    <TrendingUp className="h-3 w-3 text-emerald-600" />
                  ) : (
                    <TrendingDown className="h-3 w-3 text-red-500" />
                  )}
                  <span
                    className={`text-xs font-semibold ${
                      row.positive ? "text-emerald-600" : "text-red-500"
                    }`}
                  >
                    {row.change}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Take Callout */}
      <div className="mb-8 rounded-lg border border-[#b8860b]/20 bg-[#b8860b]/[0.06] p-5">
        <div className="flex items-start gap-3">
          <Activity className="mt-0.5 h-5 w-5 shrink-0 text-[#b8860b]" />
          <p className="text-sm font-medium leading-relaxed text-foreground">
            Strong seller&apos;s market: rising prices, shrinking DOM, and tight
            inventory all point to continued upward momentum in Los Angeles.
          </p>
        </div>
      </div>

      {/* CTA */}
      <div className="rounded-lg bg-[#1e3a5f]/[0.04] px-6 py-6 text-center">
        <a
          href="#"
          className="inline-block rounded-lg bg-[#1e3a5f] px-8 py-3.5 text-sm font-semibold tracking-wide text-white transition-opacity hover:opacity-90"
        >
          View Full Analytics Report
        </a>
      </div>
    </div>
  );
}
