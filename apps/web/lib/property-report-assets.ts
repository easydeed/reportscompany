/**
 * Property Report Assets Manifest
 * 
 * Maps themes and pages to their preview images hosted on R2.
 * Used by ThemeSelector to show real page previews instead of placeholders.
 */

import { DEFAULT_THEME_ID, themeName } from "@/lib/themes.generated";

// Base URL for R2-hosted assets
// Update this to your actual R2 public URL or custom domain
export const R2_BASE_URL = process.env.NEXT_PUBLIC_ASSETS_URL || "https://assets.trendyreports.com";

// Property reports assets path
export const PROPERTY_ASSETS_PATH = `${R2_BASE_URL}/property-reports`;

// ============================================
// THEME CONFIGURATION
// ============================================

export interface ThemeConfig {
  id: number;
  key: string;  // Theme name for API: "classic", "modern", "elegant", "teal", "bold"
  name: string;
  description: string;
  defaultColor: string;
  secondaryColor: string;
  pageCount: number;
  previewBg: string; // Fallback gradient class
  fontStyle: string;
  targetAudience: string;
  pages: PageConfig[];
}

export interface PageConfig {
  id: string;
  name: string;
  description: string;
  required?: boolean;
  previewNumber: number; // Maps to preview image file number (1.jpg, 2.jpg, etc.)
}

// ============================================
// UNIFIED PAGE STRUCTURE
// All themes now use the same 7-page layout
// ============================================

const UNIFIED_PAGES: PageConfig[] = [
  { id: "cover", name: "Cover", description: "Property photo, address, agent info", required: true, previewNumber: 1 },
  { id: "contents", name: "Table of Contents", description: "Report overview", previewNumber: 2 },
  { id: "aerial", name: "Aerial View", description: "Google Maps satellite view", previewNumber: 3 },
  { id: "property", name: "Property Details", description: "Owner, APN, beds/baths, tax info", required: true, previewNumber: 4 },
  { id: "analysis", name: "Area Sales Analysis", description: "Market statistics chart", previewNumber: 5 },
  { id: "comparables", name: "Sales Comparables", description: "Recently sold properties", required: true, previewNumber: 6 },
  { id: "range", name: "Range of Sales", description: "Price range visualization", previewNumber: 7 },
];

// Five aliases for UNIFIED_PAGES existed here, one per theme, all five
// identical and four of them unreferenced. Removed with the theme cut; the
// entries below point at UNIFIED_PAGES directly.

// ============================================
// THEME DEFINITIONS
// ============================================

export const THEMES: ThemeConfig[] = [
  {
    id: 2,
    key: "modern",
    name: "Modern",
    description: "Fresh & contemporary",
    defaultColor: "#FF6B5B",
    secondaryColor: "#1A1F36",
    pageCount: 7,
    previewBg: "bg-gradient-to-br from-red-400 to-slate-900",
    fontStyle: "font-sans",
    targetAudience: "Urban/young",
    pages: UNIFIED_PAGES,
  },
  {
    id: 3,
    key: "elegant",
    name: "Elegant",
    description: "Luxury & sophisticated",
    defaultColor: "#722F37",
    secondaryColor: "#C9A962",
    pageCount: 7,
    previewBg: "bg-gradient-to-br from-rose-900 to-amber-800",
    fontStyle: "font-serif",
    targetAudience: "High-end luxury",
    pages: UNIFIED_PAGES,
  },
  {
    id: 5,
    key: "bold",
    name: "Bold",
    description: "Strong & confident",
    defaultColor: "#15216E",
    secondaryColor: "#D69649",
    pageCount: 7,
    previewBg: "bg-gradient-to-br from-indigo-900 to-amber-700",
    fontStyle: "font-sans",
    targetAudience: "Luxury/confident",
    pages: UNIFIED_PAGES,
  },
];

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Get the URL for a theme's cover/thumbnail image
 * Used in the theme selection grid
 */
export function getThemeCoverUrl(themeId: number): string {
  return `${PROPERTY_ASSETS_PATH}/previews/${themeId}.jpg`;
}

/**
 * Get the URL for a specific page preview within a theme
 * Used in the page selection grid and preview modal
 */
export function getPagePreviewUrl(themeId: number, previewNumber: number): string {
  return `${PROPERTY_ASSETS_PATH}/previews/${themeId}/${previewNumber}.jpg`;
}

/**
 * Get theme configuration by ID or key
 */
export function getTheme(themeIdOrKey: number | string): ThemeConfig | undefined {
  if (typeof themeIdOrKey === "string") {
    return THEMES.find(t => t.key === themeIdOrKey);
  }
  return THEMES.find(t => t.id === themeIdOrKey);
}

/**
 * Get theme key by ID
 */
export function getThemeKey(themeId: number): string {
  // Fell back to the literal "teal", a name the renderer no longer has a
  // template for — a retired id would have produced a request the worker
  // could only default, with nothing saying so.
  return getTheme(themeId)?.key || themeName(DEFAULT_THEME_ID);
}

/**
 * Get theme ID by key
 */
export function getThemeId(themeKey: string): number {
  return getTheme(themeKey)?.id || DEFAULT_THEME_ID;
}

/**
 * Get pages for a specific theme
 */
export function getThemePages(themeId: number): PageConfig[] {
  return getTheme(themeId)?.pages || UNIFIED_PAGES;
}

/**
 * Get page config by ID within a theme
 */
export function getPageConfig(themeId: number, pageId: string): PageConfig | undefined {
  return getThemePages(themeId).find(p => p.id === pageId);
}

/**
 * Check if theme is compact (fewer pages)
 *
 * D-165. This is an ORDERING ASSUMPTION ON IDS standing in for a per-theme
 * fact, and the fact no longer has a producer: `PropertyReportBuilder` uses
 * one `page_set` for every theme, so no theme renders fewer pages than
 * another. `pageCount` says 7 in this file and 9 in
 * `components/property-wizard/types.ts`; both are guesses.
 *
 * Left behaving as it did, because changing what the picker shows was not
 * part of the theme cut and the Design rewire replaces this metadata. It is
 * still an ordering assumption: the cut left ids 2, 3 and 5, so `>= 4` means
 * bold alone — which happens to match the old table, and would not have if
 * the surviving ids had been different.
 */
export function isCompactTheme(themeId: number): boolean {
  return themeId >= 4;
}

// ============================================
// ASSET URLS
// ============================================

export const FONTS = {
  bariol: {
    light: {
      woff2: `${PROPERTY_ASSETS_PATH}/fonts/bariol_light-webfont.woff2`,
      woff: `${PROPERTY_ASSETS_PATH}/fonts/bariol_light-webfont.woff`,
    },
    bold: {
      woff2: `${PROPERTY_ASSETS_PATH}/fonts/bariol_bold-webfont.woff2`,
      woff: `${PROPERTY_ASSETS_PATH}/fonts/bariol_bold-webfont.woff`,
    },
    thin: {
      woff2: `${PROPERTY_ASSETS_PATH}/fonts/bariol_thin-webfont.woff2`,
      woff: `${PROPERTY_ASSETS_PATH}/fonts/bariol_thin-webfont.woff`,
    },
  },
  nexa: {
    light: {
      woff: `${PROPERTY_ASSETS_PATH}/fonts/NexaLight.woff`,
    },
    bold: {
      woff: `${PROPERTY_ASSETS_PATH}/fonts/NexaBold.woff`,
    },
  },
  montserrat: {
    regular: `${PROPERTY_ASSETS_PATH}/fonts/Montserrat-Regular.otf`,
    bold: `${PROPERTY_ASSETS_PATH}/fonts/Montserrat-Bold.otf`,
    semibold: `${PROPERTY_ASSETS_PATH}/fonts/Montserrat-SemiBold.otf`,
  },
};

export const ICONS = {
  bed: `${PROPERTY_ASSETS_PATH}/images/6/bed.png`,
  sqft: `${PROPERTY_ASSETS_PATH}/images/6/sqr_feet.png`,
  home: `${PROPERTY_ASSETS_PATH}/images/6/home.png`,
  cup: `${PROPERTY_ASSETS_PATH}/images/6/cup.png`,
  chat: `${PROPERTY_ASSETS_PATH}/images/chat.png`,
  check: `${PROPERTY_ASSETS_PATH}/images/check.png`,
  contract: `${PROPERTY_ASSETS_PATH}/images/contract.png`,
  secure: `${PROPERTY_ASSETS_PATH}/images/secure.png`,
};

// Default export for convenience
export default {
  THEMES,
  getThemeCoverUrl,
  getPagePreviewUrl,
  getTheme,
  getThemeKey,
  getThemeId,
  getThemePages,
  getPageConfig,
  isCompactTheme,
  FONTS,
  ICONS,
  R2_BASE_URL,
  PROPERTY_ASSETS_PATH,
};

