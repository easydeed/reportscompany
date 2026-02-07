"use client"

import type { Theme } from "@/lib/themes"
import { property, stats } from "@/lib/report-data"
import { PageWrapper, PageHeader } from "./page-wrapper"

export function AnalysisPage({ theme }: { theme: Theme }) {
  const comparisonRows = [
    { metric: "Price", subject: "$2,100,000", comp: "$2,113,750", diff: "-$13,750", positive: false },
    { metric: "Sq Ft", subject: "3,240", comp: "3,183", diff: "+57", positive: true },
    { metric: "Beds", subject: "4", comp: "4.25", diff: "-0.25", positive: false },
    { metric: "Baths", subject: "3.5", comp: "3.38", diff: "+0.12", positive: true },
    { metric: "$/Sq Ft", subject: "$648", comp: "$665", diff: "-$17", positive: false },
  ]

  return (
    <PageWrapper theme={theme}>
      <PageHeader theme={theme} title="Area Sales Analysis" subtitle="Comparable market statistics and pricing" />

      {/* Price Range Hero */}
      <PriceRangeDisplay theme={theme} />

      {/* Market Stats Grid */}
      <div
        className="grid grid-cols-4 gap-3"
        style={{ marginTop: "16px", marginBottom: "16px" }}
      >
        {[
          { value: String(stats.compCount), label: "Comparables" },
          { value: stats.avgSqft, label: "Avg Sq Ft" },
          { value: stats.avgBeds, label: "Avg Beds" },
          { value: stats.avgBaths, label: "Avg Baths" },
        ].map((stat, i) => (
          <div
            key={i}
            className="flex flex-col items-center justify-center"
            style={{
              padding: "12px 8px",
              backgroundColor: theme.key === "modern" ? "#F8FAFC" : theme.colors.surface,
              borderRadius: theme.radiusLg,
              border: `1px solid ${theme.colors.border}`,
            }}
          >
            <div
              style={{
                fontFamily: theme.fonts.display,
                fontSize: "22px",
                fontWeight: 700,
                color: theme.colors.primary,
                lineHeight: 1,
                fontStyle: theme.key === "elegant" ? "italic" : "normal",
              }}
            >
              {stat.value}
            </div>
            <div
              style={{
                fontFamily: theme.fonts.body,
                fontSize: "8px",
                color: theme.colors.muted,
                textTransform: "uppercase",
                letterSpacing: "1px",
                marginTop: "4px",
              }}
            >
              {stat.label}
            </div>
          </div>
        ))}
      </div>

      {/* Subject vs Comp Average Price Position Bar */}
      <PricePositionBar theme={theme} />

      {/* Comparison Table */}
      <div style={{ marginTop: "16px" }}>
        <div
          style={{
            fontFamily: theme.fonts.display,
            fontSize: "13px",
            fontWeight: 700,
            color: theme.colors.primary,
            marginBottom: "8px",
            textTransform: theme.key === "bold" || theme.key === "teal" ? "uppercase" : undefined,
            letterSpacing: theme.key === "bold" ? "1.5px" : theme.key === "teal" ? "1px" : "0",
            fontStyle: theme.key === "elegant" ? "italic" : "normal",
          }}
        >
          Subject Property vs. Comparable Averages
        </div>
        <div
          style={{
            borderRadius: theme.radiusLg,
            overflow: "hidden",
            border: theme.key === "elegant" ? "none" : `1px solid ${theme.colors.border}`,
          }}
        >
          {/* Table header */}
          <div
            className="grid grid-cols-4"
            style={{
              backgroundColor: theme.key === "elegant" ? "transparent" : theme.colors.primary,
              padding: "8px 12px",
              borderBottom: theme.key === "elegant" ? `2px solid ${theme.colors.accent}` : "none",
            }}
          >
            {["Metric", "Subject Property", "Comp Average", "Difference"].map((h) => (
              <div
                key={h}
                style={{
                  fontFamily: theme.fonts.body,
                  fontSize: "9px",
                  fontWeight: 700,
                  color: theme.key === "elegant" ? theme.colors.primary : theme.key === "teal" ? theme.colors.textOnAccent : theme.colors.textOnPrimary,
                  textTransform: "uppercase",
                  letterSpacing: "1px",
                }}
              >
                {h}
              </div>
            ))}
          </div>

          {/* Rows */}
          {comparisonRows.map((row, i) => {
            let bgColor = "transparent"
            if (theme.key === "bold" || theme.key === "classic") {
              bgColor = i % 2 === 0 ? theme.colors.tableStripe : "transparent"
            }
            if (theme.key === "teal") {
              bgColor = i % 2 === 0 ? (theme.colors.tableStripe ?? "transparent") : (theme.colors.tableStripe2 ?? "transparent")
            }
            if (theme.key === "modern") {
              bgColor = i % 2 === 0 ? "#F8FAFC" : "white"
            }

            return (
              <div
                key={i}
                className="grid grid-cols-4"
                style={{
                  padding: theme.key === "elegant" ? "7px 0" : "7px 12px",
                  backgroundColor: bgColor,
                  borderBottom: theme.key === "elegant" ? `1px solid ${theme.colors.border}` : "none",
                  fontSize: "10px",
                }}
              >
                <span style={{ fontFamily: theme.fonts.body, fontWeight: 600, color: theme.colors.primary }}>
                  {row.metric}
                </span>
                <span style={{ fontFamily: theme.fonts.body, color: theme.colors.primary }}>
                  {row.subject}
                </span>
                <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>
                  {row.comp}
                </span>
                <span
                  style={{
                    fontFamily: theme.fonts.body,
                    fontWeight: 700,
                    color: row.positive ? "#16A34A" : "#DC2626",
                  }}
                >
                  {row.diff}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </PageWrapper>
  )
}

function PriceRangeDisplay({ theme }: { theme: Theme }) {
  if (theme.key === "bold") {
    return (
      <div
        className="flex"
        style={{ borderRadius: theme.radiusLg, overflow: "hidden", border: `2px solid ${theme.colors.primary}` }}
      >
        <div className="flex-1 flex flex-col items-center justify-center" style={{ padding: "16px", backgroundColor: theme.colors.tableStripe }}>
          <div style={{ fontFamily: theme.fonts.body, fontSize: "8px", color: theme.colors.muted, textTransform: "uppercase", letterSpacing: "2px", marginBottom: "4px" }}>Low</div>
          <div style={{ fontFamily: theme.fonts.display, fontSize: "20px", fontWeight: 700, color: theme.colors.primary }}>$1,975,000</div>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center" style={{ padding: "16px", backgroundColor: theme.colors.primary }}>
          <div style={{ fontFamily: theme.fonts.body, fontSize: "8px", color: theme.colors.accent, textTransform: "uppercase", letterSpacing: "2px", marginBottom: "4px" }}>Median</div>
          <div style={{ fontFamily: theme.fonts.display, fontSize: "26px", fontWeight: 700, color: theme.colors.accent }}>$2,100,000</div>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center" style={{ padding: "16px", backgroundColor: theme.colors.tableStripe }}>
          <div style={{ fontFamily: theme.fonts.body, fontSize: "8px", color: theme.colors.muted, textTransform: "uppercase", letterSpacing: "2px", marginBottom: "4px" }}>High</div>
          <div style={{ fontFamily: theme.fonts.display, fontSize: "20px", fontWeight: 700, color: theme.colors.primary }}>$2,280,000</div>
        </div>
      </div>
    )
  }

  if (theme.key === "classic") {
    return (
      <div
        style={{ padding: "20px", backgroundColor: theme.colors.surface, borderRadius: theme.radiusLg, border: `1px solid ${theme.colors.border}` }}
      >
        <div className="flex items-end justify-between">
          <div className="flex flex-col items-center">
            <div style={{ fontFamily: theme.fonts.body, fontSize: "9px", color: theme.colors.muted, textTransform: "uppercase", letterSpacing: "1px", marginBottom: "4px" }}>Low</div>
            <div style={{ fontFamily: theme.fonts.display, fontSize: "18px", fontWeight: 400, color: theme.colors.primary }}>$1,975,000</div>
          </div>
          <div className="flex-1 mx-6" style={{ height: "2px", borderBottom: `2px dotted ${theme.colors.border}`, position: "relative", top: "-10px" }} />
          <div className="flex flex-col items-center">
            <div style={{ fontFamily: theme.fonts.body, fontSize: "9px", color: theme.colors.accent, textTransform: "uppercase", letterSpacing: "1px", marginBottom: "4px" }}>Median</div>
            <div style={{ fontFamily: theme.fonts.display, fontSize: "26px", fontWeight: 700, color: theme.colors.accent }}>$2,100,000</div>
          </div>
          <div className="flex-1 mx-6" style={{ height: "2px", borderBottom: `2px dotted ${theme.colors.border}`, position: "relative", top: "-10px" }} />
          <div className="flex flex-col items-center">
            <div style={{ fontFamily: theme.fonts.body, fontSize: "9px", color: theme.colors.muted, textTransform: "uppercase", letterSpacing: "1px", marginBottom: "4px" }}>High</div>
            <div style={{ fontFamily: theme.fonts.display, fontSize: "18px", fontWeight: 400, color: theme.colors.primary }}>$2,280,000</div>
          </div>
        </div>
      </div>
    )
  }

  if (theme.key === "elegant") {
    return (
      <div className="flex items-end justify-between" style={{ padding: "20px 0", borderBottom: `1px solid ${theme.colors.border}` }}>
        <div className="flex flex-col">
          <div style={{ fontFamily: theme.fonts.body, fontSize: "8px", color: theme.colors.muted, textTransform: "uppercase", letterSpacing: "2px", marginBottom: "4px" }}>Low</div>
          <div style={{ fontFamily: theme.fonts.display, fontSize: "18px", fontWeight: 400, fontStyle: "italic", color: theme.colors.primary }}>$1,975,000</div>
        </div>
        <div className="flex flex-col items-center">
          <div style={{ fontFamily: theme.fonts.body, fontSize: "8px", color: theme.colors.accent, textTransform: "uppercase", letterSpacing: "2px", marginBottom: "4px" }}>Median</div>
          <div style={{ fontFamily: theme.fonts.display, fontSize: "30px", fontWeight: 600, fontStyle: "italic", color: theme.colors.accent }}>$2,100,000</div>
        </div>
        <div className="flex flex-col items-end">
          <div style={{ fontFamily: theme.fonts.body, fontSize: "8px", color: theme.colors.muted, textTransform: "uppercase", letterSpacing: "2px", marginBottom: "4px" }}>High</div>
          <div style={{ fontFamily: theme.fonts.display, fontSize: "18px", fontWeight: 400, fontStyle: "italic", color: theme.colors.primary }}>$2,280,000</div>
        </div>
      </div>
    )
  }

  if (theme.key === "modern") {
    return (
      <div className="flex gap-3">
        {[
          { label: "Low", value: "$1,975,000", highlight: false },
          { label: "Median", value: "$2,100,000", highlight: true },
          { label: "High", value: "$2,280,000", highlight: false },
        ].map((item) => (
          <div
            key={item.label}
            className="flex-1 flex flex-col items-center justify-center"
            style={{
              padding: "16px",
              backgroundColor: item.highlight ? theme.colors.primary : "#F8FAFC",
              borderRadius: theme.radiusLg,
              border: item.highlight ? "none" : `1px solid ${theme.colors.border}`,
            }}
          >
            <div style={{ fontFamily: theme.fonts.body, fontSize: "9px", color: item.highlight ? "rgba(255,255,255,0.7)" : theme.colors.muted, textTransform: "uppercase", letterSpacing: "1px", marginBottom: "4px" }}>{item.label}</div>
            <div style={{ fontFamily: theme.fonts.display, fontSize: item.highlight ? "24px" : "18px", fontWeight: 700, color: item.highlight ? "white" : theme.colors.accent }}>{item.value}</div>
          </div>
        ))}
      </div>
    )
  }

  // Teal
  return (
    <div className="flex" style={{ borderRadius: theme.radiusLg, overflow: "hidden" }}>
      <div className="flex-1 flex flex-col items-center justify-center" style={{ padding: "16px", backgroundColor: theme.colors.tableStripe }}>
        <div style={{ fontFamily: theme.fonts.display, fontSize: "8px", color: theme.colors.muted, textTransform: "uppercase", letterSpacing: "2px", marginBottom: "4px", fontWeight: 700 }}>Low</div>
        <div style={{ fontFamily: theme.fonts.display, fontSize: "18px", fontWeight: 900, color: theme.colors.accent }}>$1,975,000</div>
      </div>
      <div className="flex-1 flex flex-col items-center justify-center" style={{ padding: "16px", backgroundColor: theme.colors.accent }}>
        <div style={{ fontFamily: theme.fonts.display, fontSize: "8px", color: theme.colors.primary, textTransform: "uppercase", letterSpacing: "2px", marginBottom: "4px", fontWeight: 700 }}>Median</div>
        <div style={{ fontFamily: theme.fonts.display, fontSize: "24px", fontWeight: 900, color: theme.colors.primary }}>$2,100,000</div>
      </div>
      <div className="flex-1 flex flex-col items-center justify-center" style={{ padding: "16px", backgroundColor: theme.colors.tableStripe2 }}>
        <div style={{ fontFamily: theme.fonts.display, fontSize: "8px", color: theme.colors.muted, textTransform: "uppercase", letterSpacing: "2px", marginBottom: "4px", fontWeight: 700 }}>High</div>
        <div style={{ fontFamily: theme.fonts.display, fontSize: "18px", fontWeight: 900, color: theme.colors.accent }}>$2,280,000</div>
      </div>
    </div>
  )
}

function PricePositionBar({ theme }: { theme: Theme }) {
  // Subject: $2,100,000 in range $1,975,000 - $2,280,000
  const low = 1975000
  const high = 2280000
  const subject = 2100000
  const pct = ((subject - low) / (high - low)) * 100

  return (
    <div style={{ marginTop: "4px" }}>
      <div
        style={{
          fontFamily: theme.fonts.body,
          fontSize: "9px",
          color: theme.colors.muted,
          marginBottom: "6px",
          textTransform: "uppercase",
          letterSpacing: "1px",
        }}
      >
        Subject property position in price range
      </div>
      <div className="relative" style={{ height: "36px" }}>
        {/* Bar background */}
        <div
          className="absolute"
          style={{
            top: "12px",
            left: 0,
            right: 0,
            height: "12px",
            borderRadius: theme.key === "modern" ? "6px" : theme.radius,
            background: theme.key === "modern"
              ? `linear-gradient(90deg, ${theme.colors.border} 0%, ${theme.colors.primary} 100%)`
              : theme.key === "teal"
                ? `linear-gradient(90deg, ${theme.colors.tableStripe} 0%, ${theme.colors.primary} 100%)`
                : `linear-gradient(90deg, ${theme.colors.border} 0%, ${theme.colors.accent} 100%)`,
          }}
        />
        {/* Subject marker */}
        <div
          className="absolute flex flex-col items-center"
          style={{ left: `${pct}%`, top: 0, transform: "translateX(-50%)" }}
        >
          <div
            style={{
              fontFamily: theme.fonts.body,
              fontSize: "8px",
              fontWeight: 700,
              color: theme.colors.primary,
              whiteSpace: "nowrap",
              marginBottom: "1px",
            }}
          >
            $2,100,000
          </div>
          <div
            style={{
              width: "3px",
              height: "24px",
              backgroundColor: theme.colors.primary,
              borderRadius: "2px",
            }}
          />
        </div>
        {/* Labels */}
        <div
          className="absolute flex justify-between"
          style={{ bottom: "-14px", left: 0, right: 0 }}
        >
          <span style={{ fontFamily: theme.fonts.body, fontSize: "8px", color: theme.colors.muted }}>$1,975,000</span>
          <span style={{ fontFamily: theme.fonts.body, fontSize: "8px", color: theme.colors.muted }}>$2,280,000</span>
        </div>
      </div>
    </div>
  )
}
