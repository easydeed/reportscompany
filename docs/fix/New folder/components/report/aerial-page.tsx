"use client"

import type { Theme } from "@/lib/themes"
import { property } from "@/lib/report-data"
import { PageWrapper, PageHeader } from "./page-wrapper"

export function AerialPage({ theme }: { theme: Theme }) {
  return (
    <PageWrapper theme={theme}>
      <PageHeader theme={theme} title="Aerial View" subtitle={property.fullAddress} />

      {/* Map container */}
      <div
        className="relative overflow-hidden"
        style={{
          borderRadius: theme.radiusLg,
          border: `1px solid ${theme.colors.border}`,
          height: "520px",
        }}
      >
        <img
          src="/images/aerial-map.jpg"
          alt="Aerial satellite view of property location"
          className="w-full h-full object-cover"
        />

        {/* Property marker overlay */}
        <div
          className="absolute flex flex-col items-center"
          style={{ top: "50%", left: "50%", transform: "translate(-50%, -100%)", zIndex: 5 }}
        >
          <div
            style={{
              backgroundColor: theme.key === "modern" ? theme.colors.primary : theme.colors.accent,
              color: theme.key === "modern" || theme.key === "bold" ? "white" : theme.colors.textOnAccent,
              fontFamily: theme.fonts.body,
              fontSize: "9px",
              fontWeight: 700,
              padding: "4px 10px",
              borderRadius: theme.radius,
              whiteSpace: "nowrap",
              letterSpacing: "0.5px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
            }}
          >
            {property.address}
          </div>
          <svg width="12" height="16" viewBox="0 0 12 16" style={{ marginTop: "-1px" }}>
            <path
              d="M6 0C2.7 0 0 2.7 0 6c0 4.5 6 10 6 10s6-5.5 6-10c0-3.3-2.7-6-6-6z"
              fill={theme.key === "modern" ? theme.colors.primary : theme.colors.accent}
            />
            <circle cx="6" cy="6" r="2.5" fill="white" />
          </svg>
        </div>
      </div>

      {/* Info bar below map */}
      <div
        className="flex items-center justify-between"
        style={{
          marginTop: "14px",
          padding: "12px 16px",
          backgroundColor: theme.key === "classic" ? theme.colors.surface : theme.key === "modern" ? "#F8FAFC" : theme.colors.surface,
          borderRadius: theme.radiusLg,
          border: `1px solid ${theme.colors.border}`,
        }}
      >
        <InfoItem theme={theme} label="Neighborhood" value={property.neighborhood} />
        <div style={{ width: "1px", height: "24px", backgroundColor: theme.colors.border }} />
        <InfoItem theme={theme} label="Coordinates" value={`${property.lat}, ${property.lng}`} />
        <div style={{ width: "1px", height: "24px", backgroundColor: theme.colors.border }} />
        <InfoItem theme={theme} label="ZIP Code" value={property.zip} />
        <div style={{ width: "1px", height: "24px", backgroundColor: theme.colors.border }} />
        <InfoItem theme={theme} label="County" value={property.county} />
      </div>
    </PageWrapper>
  )
}

function InfoItem({ theme, label, value }: { theme: Theme; label: string; value: string }) {
  return (
    <div className="flex flex-col items-center">
      <div
        style={{
          fontFamily: theme.fonts.body,
          fontSize: "8px",
          color: theme.colors.muted,
          textTransform: "uppercase",
          letterSpacing: "1px",
          marginBottom: "2px",
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: theme.fonts.display,
          fontSize: "12px",
          fontWeight: 700,
          color: theme.colors.primary,
          fontStyle: theme.key === "elegant" ? "italic" : "normal",
        }}
      >
        {value}
      </div>
    </div>
  )
}
