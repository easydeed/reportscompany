"use client"

import { PreviewHeader } from "./preview-header"
import { PreviewNarrative } from "./preview-narrative"
import { PreviewHeroStat } from "./preview-hero-stat"
import { PreviewPhotoGrid } from "./preview-photo-grid"
import { PreviewStackedStats } from "./preview-stacked-stats"
import { PreviewDataTable } from "./preview-data-table"
import { PreviewAgentFooter } from "./preview-agent-footer"
import { PreviewGalleryCount } from "./preview-gallery-count"
import { PreviewCta } from "./preview-cta"
import { PREVIEW_CONTENT, PREVIEW_CAPS, type PreviewReportType } from "./sample-data"

export type { PreviewReportType } from "./sample-data"

// Match worker defaults in apps/worker/src/worker/market_builder.py
// (DEFAULT_PRIMARY = "#18235c", DEFAULT_ACCENT = "#0d9488"). Keep in sync so the
// wizard preview matches what the actual PDF/email engine renders for unbranded
// accounts.
export const PREVIEW_DEFAULT_PRIMARY = "#18235c"
export const PREVIEW_DEFAULT_ACCENT = "#0d9488"

export interface SharedEmailPreviewProps {
  primaryColor: string
  accentColor: string
  headerLogoUrl?: string | null
  displayName?: string | null
  agentName: string
  agentTitle?: string | null
  agentPhone?: string | null
  agentEmail?: string | null
  agentPhotoUrl?: string | null
  agentLogoUrl?: string | null
  reportType: PreviewReportType
  audienceLabel?: string | null
  areaName?: string
  lookbackDays?: number
  scale?: number
}

export function SharedEmailPreview({
  primaryColor,
  accentColor,
  headerLogoUrl,
  displayName,
  agentName,
  agentTitle,
  agentPhone,
  agentEmail,
  agentPhotoUrl,
  agentLogoUrl,
  reportType,
  audienceLabel,
  areaName,
  lookbackDays = 30,
  scale = 1,
}: SharedEmailPreviewProps) {
  const content = PREVIEW_CONTENT[reportType]
  if (!content) return null

  const cap = PREVIEW_CAPS[reportType]
  const total = content.totalAvailable ?? content.listings.length
  const showing = Math.min(content.listings.length, cap)
  const isTruncated = total > showing
  const remaining = isTruncated ? total - showing : 0

  const truncationNote = isTruncated ? (
    <div className="text-center text-[10px] text-stone-500">
      Showing {showing} of {total} listings
    </div>
  ) : null

  const moreCallout = remaining > 0 ? (
    <div
      className="rounded-md border border-dashed px-3 py-2 text-center text-[11px] font-medium"
      style={{
        borderColor: `${accentColor}66`,
        color: accentColor,
        backgroundColor: `${accentColor}0F`,
      }}
    >
      + {remaining} more listings — see the full PDF
    </div>
  ) : null

  const cta = <PreviewCta primaryColor={primaryColor} />

  const agentFooter = (
    <PreviewAgentFooter
      agentName={agentName}
      agentTitle={agentTitle}
      agentPhone={agentPhone}
      agentEmail={agentEmail}
      agentPhotoUrl={agentPhotoUrl}
      agentLogoUrl={agentLogoUrl}
      primaryColor={primaryColor}
      accentColor={accentColor}
    />
  )

  const body = renderBody(
    reportType,
    content,
    primaryColor,
    accentColor,
    truncationNote,
    moreCallout,
    cta,
    agentFooter,
  )

  return (
    <div
      className="mx-auto origin-top font-sans"
      style={{ transform: scale < 1 ? `scale(${scale})` : undefined, maxWidth: 480 }}
    >
      <div className="overflow-hidden rounded-t-lg shadow-sm">
        <PreviewHeader
          primaryColor={primaryColor}
          accentColor={accentColor}
          headerLogoUrl={headerLogoUrl}
          displayName={displayName}
          reportType={reportType}
          audienceLabel={audienceLabel}
          areaName={areaName}
          lookbackDays={lookbackDays}
        />
      </div>

      <div className="space-y-3 border-x border-stone-200 bg-white px-4 py-4">
        {body}
      </div>

      <div className="rounded-b-lg border border-t-0 border-stone-200 bg-stone-50 px-4 py-2.5 text-center text-[9px] text-stone-400">
        Powered by {displayName || "TrendyReports"} &bull;{" "}
        <span className="underline">Unsubscribe</span>
      </div>
    </div>
  )
}

function renderBody(
  type: PreviewReportType,
  content: (typeof PREVIEW_CONTENT)[PreviewReportType],
  primary: string,
  accent: string,
  truncationNote: React.ReactNode,
  moreCallout: React.ReactNode,
  cta: React.ReactNode,
  agentFooter: React.ReactNode,
) {
  switch (type) {
    case "market_snapshot":
      return (
        <>
          <PreviewNarrative text={content.narrative} primaryColor={primary} accentColor={accent} />
          <PreviewHeroStat
            label={content.heroLabel}
            value={content.heroValue}
            sub={content.heroSub}
            primaryColor={primary}
          />
          {truncationNote}
          <PreviewPhotoGrid
            listings={content.listings}
            layout="2x2"
            primaryColor={primary}
            accentColor={accent}
          />
          {moreCallout}
          <PreviewStackedStats stats={content.stats} primaryColor={primary} />
          {cta}
          {agentFooter}
        </>
      )

    case "new_listings_gallery":
    case "open_houses":
      return (
        <>
          <PreviewNarrative text={content.narrative} primaryColor={primary} accentColor={accent} />
          <PreviewHeroStat
            label={content.heroLabel}
            value={content.heroValue}
            sub={content.heroSub}
            primaryColor={primary}
          />
          {content.galleryCount && (
            <PreviewGalleryCount
              count={content.galleryCount}
              label="properties found"
              accentColor={accent}
            />
          )}
          <PreviewStackedStats stats={content.stats} primaryColor={primary} />
          {truncationNote}
          <PreviewPhotoGrid
            listings={content.listings}
            layout="3x2"
            primaryColor={primary}
            accentColor={accent}
          />
          {moreCallout}
          {cta}
          {agentFooter}
        </>
      )

    case "closed":
      return (
        <>
          <PreviewNarrative text={content.narrative} primaryColor={primary} accentColor={accent} />
          <PreviewHeroStat
            label={content.heroLabel}
            value={content.heroValue}
            sub={content.heroSub}
            primaryColor={primary}
          />
          <PreviewStackedStats stats={content.stats} primaryColor={primary} />
          {truncationNote}
          <PreviewPhotoGrid
            listings={content.listings}
            layout="2x2"
            primaryColor={primary}
            accentColor={accent}
          />
          {moreCallout}
          <PreviewDataTable rows={content.tableRows} primaryColor={primary} />
          {cta}
          {agentFooter}
        </>
      )

    case "inventory":
      return (
        <>
          <PreviewNarrative text={content.narrative} primaryColor={primary} accentColor={accent} />
          <PreviewHeroStat
            label={content.heroLabel}
            value={content.heroValue}
            sub={content.heroSub}
            primaryColor={primary}
          />
          <PreviewStackedStats stats={content.stats} primaryColor={primary} />
          {truncationNote}
          <PreviewPhotoGrid
            listings={content.listings}
            layout="2x2"
            primaryColor={primary}
            accentColor={accent}
          />
          {moreCallout}
          <PreviewDataTable rows={content.tableRows} primaryColor={primary} />
          {cta}
          {agentFooter}
        </>
      )

    case "featured_listings":
      return (
        <>
          <PreviewNarrative text={content.narrative} primaryColor={primary} accentColor={accent} />
          {content.galleryCount && (
            <PreviewGalleryCount
              count={content.galleryCount}
              label="featured properties"
              accentColor={accent}
            />
          )}
          {truncationNote}
          <PreviewPhotoGrid
            listings={content.listings}
            layout="large-cards"
            primaryColor={primary}
            accentColor={accent}
          />
          {moreCallout}
          <PreviewStackedStats stats={content.stats} primaryColor={primary} />
          {cta}
          {agentFooter}
        </>
      )

    case "new_listings":
      return (
        <>
          <PreviewNarrative text={content.narrative} primaryColor={primary} accentColor={accent} />
          <PreviewHeroStat
            label={content.heroLabel}
            value={content.heroValue}
            sub={content.heroSub}
            primaryColor={primary}
          />
          <PreviewStackedStats stats={content.stats} primaryColor={primary} />
          {truncationNote}
          <PreviewPhotoGrid
            listings={content.listings}
            layout="2x2"
            primaryColor={primary}
            accentColor={accent}
          />
          {moreCallout}
          {cta}
          {agentFooter}
        </>
      )

    case "price_bands":
      return (
        <>
          <PreviewNarrative text={content.narrative} primaryColor={primary} accentColor={accent} />
          <PreviewHeroStat
            label={content.heroLabel}
            value={content.heroValue}
            sub={content.heroSub}
            primaryColor={primary}
          />
          <PreviewStackedStats stats={content.stats} primaryColor={primary} />
          {truncationNote}
          <PreviewPhotoGrid
            listings={content.listings}
            layout="2x2"
            primaryColor={primary}
            accentColor={accent}
          />
          {moreCallout}
          {cta}
          {agentFooter}
        </>
      )

    default:
      return agentFooter
  }
}
