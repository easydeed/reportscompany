/**
 * Shared Report Type Definitions
 * 
 * IMPORTANT: This is the single source of truth for report types in the frontend.
 * Keep this in sync with:
 * - Backend: apps/api/src/api/routes/schedules.py (Literal[...])
 * - Email: apps/worker/src/worker/email/template.py (display map)
 * - Worker: apps/worker/src/worker/report_builders.py (builders dict)
 * 
 * Last Updated: Nov 24, 2025 (PASS W1 - Wizard Fix)
 */

export type ReportType =
  | "market_snapshot"
  | "new_listings"
  | "inventory"
  | "closed"
  | "price_bands"
  | "open_houses"
  | "new_listings_gallery"
  | "featured_listings"

export interface ReportTypeConfig {
  slug: ReportType
  label: string
  description: string
  category: "core" | "secondary"
}

export const reportTypes: ReportTypeConfig[] = [
  {
    slug: "market_snapshot",
    label: "Market Snapshot",
    description: "Complete overview of current market conditions",
    category: "core"
  },
  {
    slug: "new_listings",
    label: "New Listings",
    description: "Recently listed properties in your area",
    category: "core"
  },
  {
    slug: "new_listings_gallery",
    label: "New Listings Gallery",
    description: "Photo-rich gallery of new listings",
    category: "core"
  },
  {
    slug: "featured_listings",
    label: "Featured Listings",
    description: "Curated showcase of featured properties",
    category: "core"
  },
  {
    slug: "inventory",
    label: "Inventory Report",
    description: "Available properties and market supply",
    category: "secondary"
  },
  {
    slug: "closed",
    label: "Closed Sales",
    description: "Recently sold properties and trends",
    category: "secondary"
  },
  {
    slug: "price_bands",
    label: "Price Bands",
    description: "Market segmentation by price ranges",
    category: "secondary"
  },
  {
    slug: "open_houses",
    label: "Open Houses",
    description: "Upcoming open house schedule",
    category: "secondary"
  }
]

/**
 * Helper to get report type config by slug
 */
export function getReportType(slug: ReportType): ReportTypeConfig | undefined {
  return reportTypes.find(rt => rt.slug === slug)
}

/**
 * Helper to get all core report types (production-grade)
 */
export function getCoreReportTypes(): ReportTypeConfig[] {
  return reportTypes.filter(rt => rt.category === "core")
}

/**
 * Helper to get all secondary report types (beta/functional)
 */
export function getSecondaryReportTypes(): ReportTypeConfig[] {
  return reportTypes.filter(rt => rt.category === "secondary")
}

