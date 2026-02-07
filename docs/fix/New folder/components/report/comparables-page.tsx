"use client"

import type { Theme } from "@/lib/themes"
import { comparables } from "@/lib/report-data"
import { PageWrapper, PageHeader } from "./page-wrapper"

export function ComparablesPage({ theme }: { theme: Theme }) {
  return (
    <PageWrapper theme={theme}>
      <PageHeader theme={theme} title="Sales Comparables" subtitle="Recently sold comparable properties" />

      <div className="grid grid-cols-2 gap-4">
        {comparables.map((comp) => (
          <CompCard key={comp.id} theme={theme} comp={comp} />
        ))}
      </div>
    </PageWrapper>
  )
}

function CompCard({
  theme,
  comp,
}: {
  theme: Theme
  comp: (typeof comparables)[0]
}) {
  if (theme.key === "bold") {
    return (
      <div style={{ borderRadius: theme.radiusLg, overflow: "hidden", border: `2px solid ${theme.colors.primary}` }}>
        <img src={comp.photo || "/placeholder.svg"} alt={comp.address} className="w-full object-cover" style={{ height: "150px" }} />
        <div style={{ backgroundColor: theme.colors.primary, padding: "6px 10px" }} className="flex items-center justify-between">
          <span style={{ fontFamily: theme.fonts.display, fontSize: "10px", color: theme.colors.accent, fontWeight: 700, textTransform: "uppercase", letterSpacing: "1px" }}>Comp #{comp.id}</span>
          <span style={{ fontFamily: theme.fonts.display, fontSize: "16px", color: theme.colors.accent, fontWeight: 700 }}>{comp.priceFormatted}</span>
        </div>
        <div style={{ padding: "8px 10px" }}>
          <div style={{ fontFamily: theme.fonts.body, fontSize: "11px", fontWeight: 700, color: theme.colors.primary }}>{comp.address}</div>
          <div style={{ fontFamily: theme.fonts.body, fontSize: "10px", color: theme.colors.muted, marginTop: "2px" }}>
            {comp.beds} bd &middot; {comp.baths} ba &middot; {comp.sqft.toLocaleString()} sqft
          </div>
          <div className="flex items-center justify-between" style={{ marginTop: "6px", paddingTop: "6px", borderTop: `1px solid ${theme.colors.border}`, fontSize: "9px" }}>
            <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>{comp.pricePerSqft}/sqft</span>
            <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>Sold {comp.soldDate}</span>
            <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>{comp.distance}</span>
          </div>
        </div>
      </div>
    )
  }

  if (theme.key === "classic") {
    return (
      <div style={{ borderRadius: theme.radiusLg, overflow: "hidden", border: `1px solid ${theme.colors.border}`, backgroundColor: theme.colors.surface, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
        <img src={comp.photo || "/placeholder.svg"} alt={comp.address} className="w-full object-cover" style={{ height: "150px" }} />
        <div style={{ padding: "8px 10px", borderBottom: `2px solid ${theme.colors.accent}` }} className="flex items-center justify-between">
          <span style={{ fontFamily: theme.fonts.display, fontSize: "10px", color: theme.colors.accent, fontWeight: 400 }}>Comparable {comp.id}</span>
          <span style={{ fontFamily: theme.fonts.display, fontSize: "16px", color: theme.colors.primary, fontWeight: 600 }}>{comp.priceFormatted}</span>
        </div>
        <div style={{ padding: "8px 10px" }}>
          <div style={{ fontFamily: theme.fonts.display, fontSize: "12px", fontWeight: 600, color: theme.colors.primary }}>{comp.address}</div>
          <div style={{ fontFamily: theme.fonts.body, fontSize: "10px", color: theme.colors.muted, marginTop: "2px" }}>
            {comp.beds} bd &middot; {comp.baths} ba &middot; {comp.sqft.toLocaleString()} sqft
          </div>
          <div className="flex items-center justify-between" style={{ marginTop: "6px", paddingTop: "6px", borderTop: `1px dotted ${theme.colors.border}`, fontSize: "9px" }}>
            <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>{comp.pricePerSqft}/sqft</span>
            <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>Sold {comp.soldDate}</span>
            <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>{comp.distance}</span>
          </div>
        </div>
      </div>
    )
  }

  if (theme.key === "elegant") {
    return (
      <div style={{ overflow: "hidden" }}>
        <img src={comp.photo || "/placeholder.svg"} alt={comp.address} className="w-full object-cover" style={{ height: "150px" }} />
        <div style={{ padding: "8px 0", borderBottom: `1px solid ${theme.colors.border}` }} className="flex items-center justify-between">
          <span style={{ fontFamily: theme.fonts.display, fontSize: "10px", color: theme.colors.accent, fontStyle: "italic" }}>No. {comp.id}</span>
          <span style={{ fontFamily: theme.fonts.display, fontSize: "17px", color: theme.colors.primary, fontWeight: 500, fontStyle: "italic" }}>{comp.priceFormatted}</span>
        </div>
        <div style={{ padding: "8px 0" }}>
          <div style={{ fontFamily: theme.fonts.display, fontSize: "12px", fontWeight: 500, fontStyle: "italic", color: theme.colors.primary }}>{comp.address}</div>
          <div style={{ fontFamily: theme.fonts.body, fontSize: "10px", color: theme.colors.muted, marginTop: "2px" }}>
            {comp.beds} bd &middot; {comp.baths} ba &middot; {comp.sqft.toLocaleString()} sqft
          </div>
          <div className="flex items-center justify-between" style={{ marginTop: "6px", fontSize: "9px" }}>
            <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>{comp.pricePerSqft}/sqft</span>
            <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>Sold {comp.soldDate}</span>
            <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>{comp.distance}</span>
          </div>
        </div>
      </div>
    )
  }

  if (theme.key === "modern") {
    return (
      <div style={{ borderRadius: theme.radiusLg, overflow: "hidden", border: `1px solid ${theme.colors.border}`, backgroundColor: "white" }}>
        <img src={comp.photo || "/placeholder.svg"} alt={comp.address} className="w-full object-cover" style={{ height: "150px" }} />
        <div
          className="flex items-center justify-between"
          style={{
            padding: "8px 12px",
            background: `linear-gradient(135deg, ${theme.colors.primary} 0%, #FF8A7A 100%)`,
          }}
        >
          <span
            style={{
              fontFamily: theme.fonts.body,
              fontSize: "9px",
              color: "white",
              fontWeight: 600,
              padding: "2px 10px",
              backgroundColor: "rgba(255,255,255,0.2)",
              borderRadius: "100px",
            }}
          >
            Comp #{comp.id}
          </span>
          <span style={{ fontFamily: theme.fonts.display, fontSize: "16px", color: "white", fontWeight: 700 }}>{comp.priceFormatted}</span>
        </div>
        <div style={{ padding: "8px 12px" }}>
          <div style={{ fontFamily: theme.fonts.display, fontSize: "12px", fontWeight: 600, color: theme.colors.accent }}>{comp.address}</div>
          <div style={{ fontFamily: theme.fonts.body, fontSize: "10px", color: theme.colors.muted, marginTop: "2px" }}>
            {comp.beds} bd &middot; {comp.baths} ba &middot; {comp.sqft.toLocaleString()} sqft
          </div>
          <div className="flex items-center justify-between" style={{ marginTop: "6px", paddingTop: "6px", borderTop: `1px solid ${theme.colors.border}`, fontSize: "9px" }}>
            <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>{comp.pricePerSqft}/sqft</span>
            <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>Sold {comp.soldDate}</span>
            <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>{comp.distance}</span>
          </div>
        </div>
      </div>
    )
  }

  // Teal
  return (
    <div style={{ borderRadius: theme.radiusLg, overflow: "hidden", border: `1px solid ${theme.colors.border}` }}>
      <img src={comp.photo || "/placeholder.svg"} alt={comp.address} className="w-full object-cover" style={{ height: "150px" }} />
      <div style={{ backgroundColor: theme.colors.accent, padding: "6px 10px" }} className="flex items-center justify-between">
        <span
          style={{
            fontFamily: theme.fonts.display,
            fontSize: "10px",
            color: theme.colors.primary,
            fontWeight: 900,
            backgroundColor: theme.colors.primary,
            padding: "2px 8px",
            borderRadius: theme.radiusSm,
          }}
        >
          #{comp.id}
        </span>
        <span style={{ fontFamily: theme.fonts.display, fontSize: "16px", color: theme.colors.primary, fontWeight: 900 }}>{comp.priceFormatted}</span>
      </div>
      <div style={{ padding: "8px 10px" }}>
        <div style={{ fontFamily: theme.fonts.display, fontSize: "11px", fontWeight: 800, color: theme.colors.accent }}>{comp.address}</div>
        <div style={{ fontFamily: theme.fonts.body, fontSize: "10px", color: theme.colors.muted, marginTop: "2px" }}>
          {comp.beds} bd &middot; {comp.baths} ba &middot; {comp.sqft.toLocaleString()} sqft
        </div>
        <div className="flex items-center justify-between" style={{ marginTop: "6px", paddingTop: "6px", borderTop: `1px solid ${theme.colors.border}`, fontSize: "9px" }}>
          <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>{comp.pricePerSqft}/sqft</span>
          <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>Sold {comp.soldDate}</span>
          <span style={{ fontFamily: theme.fonts.body, color: theme.colors.muted }}>{comp.distance}</span>
        </div>
      </div>
    </div>
  )
}
