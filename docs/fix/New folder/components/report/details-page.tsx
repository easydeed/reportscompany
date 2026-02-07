"use client"

import React from "react"

import type { Theme } from "@/lib/themes"
import { property } from "@/lib/report-data"
import { PageWrapper, PageHeader } from "./page-wrapper"

export function DetailsPage({ theme }: { theme: Theme }) {
  const propertyDetails = [
    { label: "Property Type", value: property.type },
    { label: "Bedrooms", value: String(property.beds) },
    { label: "Bathrooms", value: String(property.baths) },
    { label: "Living Area", value: `${property.sqft.toLocaleString()} sq ft` },
    { label: "Lot Size", value: `${property.lotSize} sq ft` },
    { label: "Year Built", value: String(property.yearBuilt) },
    { label: "Garage", value: property.garage },
    { label: "Pool", value: property.pool },
    { label: "Zoning", value: property.zoning },
  ]

  const taxInfo = [
    { label: "APN", value: property.apn },
    { label: "Assessed Value", value: property.assessedValue },
    { label: "Land Value", value: property.landValue },
    { label: "Improvement Value", value: property.improvementValue },
    { label: "Annual Taxes", value: property.annualTaxes },
    { label: "Tax Year", value: property.taxYear },
  ]

  const locationInfo = [
    { label: "Address", value: property.address },
    { label: "City", value: property.city },
    { label: "State", value: property.state },
    { label: "ZIP Code", value: property.zip },
    { label: "County", value: property.county },
  ]

  return (
    <PageWrapper theme={theme}>
      <PageHeader theme={theme} title="Property Details" subtitle={property.fullAddress} />

      {/* Key Stats Bar */}
      <div
        className="flex items-center justify-between"
        style={{
          padding: "12px 20px",
          marginBottom: "18px",
          backgroundColor: theme.colors.primary,
          borderRadius: theme.radiusLg,
        }}
      >
        {[
          { icon: "bed", label: "Beds", value: String(property.beds) },
          { icon: "bath", label: "Baths", value: String(property.baths) },
          { icon: "area", label: "Sq Ft", value: property.sqft.toLocaleString() },
          { icon: "year", label: "Year Built", value: String(property.yearBuilt) },
        ].map((stat, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="flex flex-col items-center">
              <div
                style={{
                  fontFamily: theme.fonts.display,
                  fontSize: "22px",
                  fontWeight: 700,
                  color: theme.key === "teal" ? theme.colors.primary : theme.colors.textOnPrimary,
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
                  color: theme.key === "teal" ? "rgba(52,209,195,0.7)" : "rgba(255,255,255,0.6)",
                  textTransform: "uppercase",
                  letterSpacing: "1px",
                  marginTop: "2px",
                }}
              >
                {stat.label}
              </div>
            </div>
            {i < 3 && (
              <div
                style={{
                  width: "1px",
                  height: "28px",
                  backgroundColor: "rgba(255,255,255,0.15)",
                  marginLeft: "24px",
                }}
              />
            )}
          </div>
        ))}
      </div>

      {/* Two-column layout */}
      <div className="flex gap-5">
        {/* Left column: Property Details */}
        <div className="flex-1">
          <DataTable theme={theme} title="Property Information" rows={propertyDetails} />
        </div>

        {/* Right column: Tax + Location */}
        <div className="flex-1 flex flex-col gap-5">
          <DataTable theme={theme} title="Tax Information" rows={taxInfo} />
          <DataTable theme={theme} title="Location" rows={locationInfo} />
        </div>
      </div>
    </PageWrapper>
  )
}

function DataTable({
  theme,
  title,
  rows,
}: {
  theme: Theme
  title: string
  rows: { label: string; value: string }[]
}) {
  const containerStyle: React.CSSProperties = {
    borderRadius: theme.radiusLg,
    overflow: "hidden",
    border: theme.key === "elegant" ? "none" : `1px solid ${theme.colors.border}`,
  }

  const headerStyle: React.CSSProperties = (() => {
    if (theme.key === "bold") {
      return {
        backgroundColor: theme.colors.primary,
        color: theme.colors.textOnPrimary,
        padding: "8px 12px",
        fontFamily: theme.fonts.display,
        fontSize: "11px",
        fontWeight: 700,
        textTransform: "uppercase" as const,
        letterSpacing: "2px",
      }
    }
    if (theme.key === "classic") {
      return {
        backgroundColor: theme.colors.surface,
        color: theme.colors.primary,
        padding: "8px 12px",
        fontFamily: theme.fonts.display,
        fontSize: "13px",
        fontWeight: 600,
        borderBottom: `2px solid ${theme.colors.accent}`,
      }
    }
    if (theme.key === "elegant") {
      return {
        color: theme.colors.primary,
        padding: "6px 0",
        fontFamily: theme.fonts.display,
        fontSize: "16px",
        fontWeight: 500,
        fontStyle: "italic" as const,
        borderBottom: `2px solid ${theme.colors.accent}`,
        marginBottom: "4px",
      }
    }
    if (theme.key === "modern") {
      return {
        backgroundColor: theme.colors.primary,
        color: "white",
        padding: "8px 14px",
        fontFamily: theme.fonts.display,
        fontSize: "12px",
        fontWeight: 600,
        borderRadius: `${theme.radiusLg} ${theme.radiusLg} 0 0`,
      }
    }
    // teal
    return {
      backgroundColor: theme.colors.accent,
      color: "white",
      padding: "8px 12px",
      fontFamily: theme.fonts.display,
      fontSize: "11px",
      fontWeight: 800,
      textTransform: "uppercase" as const,
      letterSpacing: "1px",
    }
  })()

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>{title}</div>
      <div>
        {rows.map((row, i) => {
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
              className="flex items-center justify-between"
              style={{
                padding: theme.key === "elegant" ? "6px 0" : "6px 12px",
                backgroundColor: bgColor,
                borderBottom: theme.key === "elegant" ? `1px solid ${theme.colors.border}` : "none",
                fontSize: "10px",
              }}
            >
              <span
                style={{
                  fontFamily: theme.fonts.body,
                  color: theme.colors.muted,
                  fontWeight: 500,
                }}
              >
                {row.label}
              </span>
              <span
                style={{
                  fontFamily: theme.fonts.body,
                  color: theme.colors.primary,
                  fontWeight: 600,
                }}
              >
                {row.value}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
