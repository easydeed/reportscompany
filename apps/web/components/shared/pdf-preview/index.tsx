"use client"

import {
  PREVIEW_CONTENT,
  PDF_LAYOUT_MAP,
  PDF_SECTION_LABELS,
  type PreviewReportType,
} from "../email-preview/sample-data"
import type { PDFLayoutType } from "../email-preview/sample-data"
import { PdfHeader } from "./pdf-header"
import { PdfAgentFooter } from "./pdf-agent-footer"
import { PdfPageIndicator } from "./pdf-page-indicator"
import { GalleryLayout } from "./layouts/gallery-layout"
import { MarketNarrativeLayout } from "./layouts/market-narrative-layout"
import { ClosedInventoryLayout } from "./layouts/closed-inventory-layout"
import { AnalyticsLayout } from "./layouts/analytics-layout"
import { PricebandsLayout } from "./layouts/pricebands-layout"
import type { PdfLayoutProps } from "./layouts/types"

// Market reports lock typography to Outfit/Inter regardless of the agent's
// theme_id. Do NOT vary this per theme — the worker's PDF templates also use
// this stack.
const PDF_FONT_STACK = "'Outfit', 'Inter', system-ui, sans-serif"

// Total page counts shown by the "Page 1 of N" indicator. These are reasonable
// defaults; actual PDFs may run longer when there's more underlying data.
const TOTAL_PAGES_BY_LAYOUT: Record<PDFLayoutType, number> = {
  gallery: 3,
  market_narrative: 2,
  closed_inventory: 3,
  analytics: 3,
  pricebands: 1,
}

const REPORT_TITLES: Record<PreviewReportType, string> = {
  market_snapshot: "Market Snapshot",
  new_listings_gallery: "New Listings",
  new_listings: "New Listings Analytics",
  closed: "Closed Sales",
  inventory: "Active Inventory",
  featured_listings: "Featured Listings",
  open_houses: "Open Houses",
  price_bands: "Price Bands",
}

export interface SharedPDFPreviewProps {
  primaryColor: string
  accentColor: string
  headerLogoUrl: string | null
  displayName: string | null
  agentName: string
  agentTitle: string | null
  agentPhone: string | null
  agentEmail: string
  agentPhotoUrl: string | null
  reportType: PreviewReportType
  audienceLabel: string | null
  areaName: string
  lookbackDays: number
  scale?: number
}

// Mockup of the first page of a market-report PDF. Drop-in compatible with
// SharedEmailPreview's prop surface so the wizard can switch between the two
// based on the delivery mode without rewiring.
//
// What this component intentionally does NOT render (vs. SharedEmailPreview):
// - "View Full PDF" CTA — this *is* the PDF preview
// - "Showing X of Y" truncation note / "+ N more" callout — PDF shows everything
// - Rounded email card chrome / unsubscribe footer
//
// What it DOES render: gradient header, layout-specific page body, agent
// footer band, and a subtle "Page 1 of N" indicator.
export function SharedPDFPreview({
  primaryColor,
  accentColor,
  headerLogoUrl,
  displayName,
  agentName,
  agentTitle,
  agentPhone,
  agentEmail,
  agentPhotoUrl,
  reportType,
  audienceLabel,
  areaName,
  lookbackDays,
  scale = 1,
}: SharedPDFPreviewProps) {
  const content = PREVIEW_CONTENT[reportType]
  if (!content) return null

  const layout = PDF_LAYOUT_MAP[reportType]
  const sectionLabel = PDF_SECTION_LABELS[reportType]
  const totalPages = TOTAL_PAGES_BY_LAYOUT[layout] ?? 1
  const reportTitle = REPORT_TITLES[reportType]

  const layoutProps: PdfLayoutProps = {
    reportType,
    content,
    primaryColor,
    accentColor,
    sectionLabel,
    areaName,
    lookbackDays,
  }

  return (
    <div
      className="mx-auto origin-top"
      style={{
        maxWidth: 480,
        transform: scale < 1 ? `scale(${scale})` : undefined,
        fontFamily: PDF_FONT_STACK,
      }}
    >
      <div
        className="flex flex-col overflow-hidden border border-stone-300 bg-white shadow-lg"
        style={{ aspectRatio: "8.5 / 11" }}
      >
        <PdfHeader
          primaryColor={primaryColor}
          accentColor={accentColor}
          headerLogoUrl={headerLogoUrl}
          displayName={displayName}
          reportTitle={reportTitle}
          areaName={areaName}
          lookbackDays={lookbackDays}
          audienceLabel={audienceLabel}
        />

        {renderLayout(layout, layoutProps)}

        <PdfAgentFooter
          agentName={agentName}
          agentTitle={agentTitle}
          agentPhone={agentPhone}
          agentEmail={agentEmail}
          agentPhotoUrl={agentPhotoUrl}
          primaryColor={primaryColor}
          accentColor={accentColor}
        />

        <PdfPageIndicator totalPages={totalPages} />
      </div>
    </div>
  )
}

function renderLayout(layout: PDFLayoutType, props: PdfLayoutProps) {
  switch (layout) {
    case "gallery":
      return <GalleryLayout {...props} />
    case "market_narrative":
      return <MarketNarrativeLayout {...props} />
    case "closed_inventory":
      return <ClosedInventoryLayout {...props} />
    case "analytics":
      return <AnalyticsLayout {...props} />
    case "pricebands":
      return <PricebandsLayout {...props} />
    default:
      return null
  }
}
