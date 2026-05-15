import type { PreviewReportType } from "../../email-preview/sample-data"

// Shared content shape consumed by every PDF layout. Mirrors the runtime shape
// of PREVIEW_CONTENT[type] so that layouts can stay type-safe.
export interface PdfLayoutContent {
  heroLabel: string
  heroValue: string
  heroSub?: string
  narrative: string
  stats: { label: string; value: string; sub?: string }[]
  listings: { photo: string; price: string; address: string; specs: string; badge?: string }[]
  tableRows: {
    address: string
    beds: number
    baths: number
    sqft: string
    price: string
    dom: number
  }[]
  galleryCount?: number
  totalAvailable?: number
}

export interface PdfLayoutProps {
  reportType: PreviewReportType
  content: PdfLayoutContent
  primaryColor: string
  accentColor: string
  sectionLabel: string
  areaName: string
  lookbackDays: number
}
