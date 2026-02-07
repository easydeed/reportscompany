"use client"

import type { Theme } from "@/lib/themes"
import { comparables, stats, property } from "@/lib/report-data"
import { PageWrapper, PageHeader } from "./page-wrapper"

export function RangePage({ theme }: { theme: Theme }) {
  const sortedComps = [...comparables].sort((a, b) => a.price - b.price)
  const low = 1975000
  const high = 2280000
  const subject = 2100000

  return (
    <PageWrapper theme={theme}>
      <PageHeader theme={theme} title="Range of Sales" subtitle="Price positioning and market insight" />

      {/* Visual Price Range Bar */}
      <div
        style={{
          padding: "20px",
          backgroundColor: theme.key === "classic" ? theme.colors.surface : theme.key === "modern" ? "#F8FAFC" : "white",
          borderRadius: theme.radiusLg,
          border: `1px solid ${theme.colors.border}`,
          marginBottom: "16px",
        }}
      >
        <div
          style={{
            fontFamily: theme.fonts.body,
            fontSize: "9px",
            color: theme.colors.muted,
            textTransform: "uppercase",
            letterSpacing: "1px",
            marginBottom: "20px",
          }}
        >
          Estimated Value Position
        </div>

        {/* Bar */}
        <div className="relative" style={{ height: "56px", marginBottom: "8px" }}>
          <div
            className="absolute"
            style={{
              top: "26px",
              left: 0,
              right: 0,
              height: "16px",
              borderRadius: theme.key === "modern" ? "8px" : theme.radius,
              background:
                theme.key === "modern"
                  ? `linear-gradient(90deg, #FFD4CF 0%, ${theme.colors.primary} 50%, #FF8A7A 100%)`
                  : theme.key === "teal"
                    ? `linear-gradient(90deg, ${theme.colors.tableStripe} 0%, ${theme.colors.primary} 50%, ${theme.colors.tableStripe2} 100%)`
                    : theme.key === "bold"
                      ? `linear-gradient(90deg, ${theme.colors.tableStripe} 0%, ${theme.colors.accent} 100%)`
                      : `linear-gradient(90deg, ${theme.colors.border} 0%, ${theme.colors.accent} 100%)`,
            }}
          />

          {/* Comp markers */}
          {sortedComps.map((comp, i) => {
            const pct = ((comp.price - low) / (high - low)) * 100
            return (
              <div
                key={comp.id}
                className="absolute"
                style={{
                  left: `${pct}%`,
                  top: "28px",
                  width: "10px",
                  height: "10px",
                  borderRadius: "50%",
                  backgroundColor: "white",
                  border: `2px solid ${theme.colors.primary}`,
                  transform: "translate(-50%, 0)",
                  zIndex: 2,
                }}
              />
            )
          })}

          {/* Subject marker */}
          <div
            className="absolute flex flex-col items-center"
            style={{
              left: `${((subject - low) / (high - low)) * 100}%`,
              top: 0,
              transform: "translateX(-50%)",
              zIndex: 3,
            }}
          >
            <div
              style={{
                fontFamily: theme.fonts.display,
                fontSize: "11px",
                fontWeight: 700,
                color: theme.key === "modern" ? theme.colors.primary : theme.colors.accent,
                whiteSpace: "nowrap",
                marginBottom: "2px",
                fontStyle: theme.key === "elegant" ? "italic" : "normal",
              }}
            >
              {property.estimatedValue}
            </div>
            <div
              style={{
                width: 0,
                height: 0,
                borderLeft: "6px solid transparent",
                borderRight: "6px solid transparent",
                borderTop: `8px solid ${theme.key === "modern" ? theme.colors.primary : theme.colors.accent}`,
              }}
            />
          </div>
        </div>

        {/* Labels */}
        <div className="flex justify-between" style={{ marginTop: "4px" }}>
          <span style={{ fontFamily: theme.fonts.body, fontSize: "9px", color: theme.colors.muted }}>
            {stats.priceRange.low}
          </span>
          <span style={{ fontFamily: theme.fonts.body, fontSize: "9px", color: theme.colors.muted }}>
            {stats.priceRange.high}
          </span>
        </div>
      </div>

      {/* Comparable Properties List */}
      <div style={{ marginBottom: "16px" }}>
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
          Comparable Sales Summary
        </div>
        <div style={{ borderRadius: theme.radiusLg, overflow: "hidden", border: theme.key === "elegant" ? "none" : `1px solid ${theme.colors.border}` }}>
          {sortedComps.map((comp, i) => {
            const pct = ((comp.price - low) / (high - low)) * 100
            let bgColor = "transparent"
            if (theme.key === "bold" || theme.key === "classic") bgColor = i % 2 === 0 ? theme.colors.tableStripe : "transparent"
            if (theme.key === "teal") bgColor = i % 2 === 0 ? (theme.colors.tableStripe ?? "transparent") : (theme.colors.tableStripe2 ?? "transparent")
            if (theme.key === "modern") bgColor = i % 2 === 0 ? "#F8FAFC" : "white"

            return (
              <div
                key={comp.id}
                className="flex items-center gap-3"
                style={{
                  padding: theme.key === "elegant" ? "8px 0" : "8px 12px",
                  backgroundColor: bgColor,
                  borderBottom: theme.key === "elegant" ? `1px solid ${theme.colors.border}` : "none",
                }}
              >
                {/* Position dot */}
                <div
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: theme.key === "modern" ? theme.colors.primary : theme.colors.accent,
                    flexShrink: 0,
                  }}
                />
                <div className="flex-1">
                  <span style={{ fontFamily: theme.fonts.body, fontSize: "10px", fontWeight: 600, color: theme.colors.primary }}>
                    {comp.address}
                  </span>
                </div>
                <div style={{ fontFamily: theme.fonts.body, fontSize: "9px", color: theme.colors.muted, minWidth: "50px", textAlign: "center" as const }}>
                  {comp.distance}
                </div>
                <div style={{ fontFamily: theme.fonts.display, fontSize: "12px", fontWeight: 700, color: theme.colors.primary, minWidth: "90px", textAlign: "right" as const, fontStyle: theme.key === "elegant" ? "italic" : "normal" }}>
                  {comp.priceFormatted}
                </div>
                {/* Mini bar showing relative position */}
                <div className="relative" style={{ width: "60px", height: "6px", backgroundColor: theme.colors.border, borderRadius: "3px", flexShrink: 0 }}>
                  <div
                    style={{
                      position: "absolute",
                      left: 0,
                      top: 0,
                      height: "100%",
                      width: `${pct}%`,
                      borderRadius: "3px",
                      backgroundColor: theme.key === "modern" ? theme.colors.primary : theme.colors.accent,
                      opacity: 0.7,
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Summary Statistics Grid */}
      <div className="grid grid-cols-4 gap-3" style={{ marginBottom: "16px" }}>
        {[
          { label: "Avg $/Sq Ft", value: stats.avgPricePerSqft },
          { label: "Avg Days on Market", value: stats.avgDaysOnMarket },
          { label: "Active Listings", value: String(stats.activeListings) },
          { label: "Comparables", value: String(stats.compCount) },
        ].map((stat, i) => (
          <div
            key={i}
            className="flex flex-col items-center justify-center"
            style={{
              padding: "10px 6px",
              backgroundColor: theme.key === "modern" ? "#F8FAFC" : theme.colors.surface,
              borderRadius: theme.radiusLg,
              border: `1px solid ${theme.colors.border}`,
            }}
          >
            <div
              style={{
                fontFamily: theme.fonts.display,
                fontSize: "16px",
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
                fontSize: "7px",
                color: theme.colors.muted,
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                marginTop: "3px",
                textAlign: "center",
              }}
            >
              {stat.label}
            </div>
          </div>
        ))}
      </div>

      {/* Market Insight */}
      <div
        style={{
          padding: "14px 16px",
          backgroundColor: theme.key === "classic" ? theme.colors.surface : theme.key === "modern" ? "#F8FAFC" : theme.key === "elegant" ? "transparent" : theme.colors.surface,
          borderRadius: theme.radiusLg,
          borderTop: `1px solid ${theme.colors.border}`,
          borderRight: `1px solid ${theme.colors.border}`,
          borderBottom: `1px solid ${theme.colors.border}`,
          borderLeft: theme.key === "elegant" ? `3px solid ${theme.colors.accent}` : `1px solid ${theme.colors.border}`,
        }}
      >
        <div
          style={{
            fontFamily: theme.fonts.display,
            fontSize: "11px",
            fontWeight: 700,
            color: theme.colors.primary,
            marginBottom: "6px",
            textTransform: theme.key === "bold" || theme.key === "teal" ? "uppercase" : undefined,
            letterSpacing: theme.key === "bold" ? "1px" : "0",
            fontStyle: theme.key === "elegant" ? "italic" : "normal",
          }}
        >
          Market Insight
        </div>
        <p
          style={{
            fontFamily: theme.fonts.body,
            fontSize: "10px",
            color: theme.colors.muted,
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          Based on 4 comparable sales within 0.6 miles, the estimated market value for this property falls between $1,975,000 and $2,280,000. The median comparable sold at $2,100,000, suggesting strong market positioning. The average price per square foot across comparables is $665, and properties in this area are selling in an average of 12 days, indicating a competitive seller&apos;s market.
        </p>
      </div>
    </PageWrapper>
  )
}
