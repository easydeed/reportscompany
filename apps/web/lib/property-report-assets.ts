/**
 * Property Report Assets Manifest
 * 
 * Maps themes and pages to their preview images hosted on R2.
 * Used by ThemeSelector to show real page previews instead of placeholders.
 */

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
  name: string;
  description: string;
  defaultColor: string;
  pageCount: number;
  previewBg: string; // Fallback gradient class
  fontStyle: string;
  pages: PageConfig[];
}

export interface PageConfig {
  id: string;
  name: string;
  description: string;
  required?: boolean;
  previewNumber: number; // Maps to preview image file number (1.jpg, 2.jpg, etc.)
}

// Theme 1 (Classic) - 20 pages
const THEME_1_PAGES: PageConfig[] = [
  { id: "cover", name: "Cover", description: "Property photo, address, agent info", required: true, previewNumber: 1 },
  { id: "contents", name: "Table of Contents", description: "Report overview", previewNumber: 2 },
  { id: "introduction", name: "Introduction", description: "Welcome message from agent", previewNumber: 3 },
  { id: "aerial", name: "Aerial View", description: "Google Maps satellite view", previewNumber: 4 },
  { id: "property_details", name: "Property Details", description: "Owner, APN, beds/baths, tax info", required: true, previewNumber: 5 },
  { id: "area_analysis", name: "Area Sales Analysis", description: "Market statistics chart", previewNumber: 6 },
  { id: "comparables", name: "Sales Comparables", description: "Recently sold properties", required: true, previewNumber: 7 },
  { id: "range_of_sales", name: "Range of Sales", description: "Price range visualization", previewNumber: 8 },
  { id: "home_buying_process", name: "Home Buying Process", description: "Step-by-step guide", previewNumber: 9 },
  { id: "how_buyers_find", name: "How Buyers Find Homes", description: "Marketing channels pie chart", previewNumber: 10 },
  { id: "pricing_correctly", name: "Pricing Strategy", description: "Pricing guidance", previewNumber: 11 },
  { id: "avg_days_market", name: "Days on Market", description: "Market timing analysis", previewNumber: 12 },
  { id: "marketing_online", name: "Digital Marketing", description: "Online marketing plan", previewNumber: 13 },
  { id: "marketing_print", name: "Print Marketing", description: "Traditional marketing", previewNumber: 14 },
  { id: "marketing_social", name: "Social Media", description: "Social proof and reach", previewNumber: 15 },
  { id: "roadmap_1", name: "Seller Roadmap (Part 1)", description: "Process overview", previewNumber: 16 },
  { id: "roadmap_2", name: "Seller Roadmap (Part 2)", description: "Continued process", previewNumber: 17 },
  { id: "analyze_optimize", name: "Analyze & Optimize", description: "Ongoing strategy", previewNumber: 18 },
  { id: "promise", name: "Agent Promise", description: "Fiduciary commitment", previewNumber: 19 },
  { id: "back_cover", name: "Back Cover", description: "Branded closing page", required: true, previewNumber: 20 },
];

// Theme 2 (Modern) - 21 pages
const THEME_2_PAGES: PageConfig[] = [
  { id: "cover", name: "Cover", description: "Property photo, address, agent info", required: true, previewNumber: 1 },
  { id: "contents", name: "Table of Contents", description: "Report overview", previewNumber: 2 },
  { id: "introduction", name: "Introduction", description: "Welcome message from agent", previewNumber: 3 },
  { id: "aerial", name: "Aerial View", description: "Google Maps satellite view", previewNumber: 4 },
  { id: "property_details", name: "Property Details", description: "Owner, APN, beds/baths, tax info", required: true, previewNumber: 5 },
  { id: "area_analysis", name: "Area Sales Analysis", description: "Market statistics chart", previewNumber: 6 },
  { id: "comparables", name: "Sales Comparables", description: "Recently sold properties", required: true, previewNumber: 7 },
  { id: "range_of_sales", name: "Range of Sales", description: "Price range visualization", previewNumber: 8 },
  { id: "neighborhood", name: "Neighborhood Stats", description: "Demographics and averages", previewNumber: 9 },
  { id: "roadmap", name: "Selling Roadmap", description: "Process overview", previewNumber: 10 },
  { id: "how_buyers_find", name: "How Buyers Find Homes", description: "Marketing channels pie chart", previewNumber: 11 },
  { id: "pricing_correctly", name: "Pricing Strategy", description: "Pricing guidance", previewNumber: 12 },
  { id: "avg_days_market", name: "Days on Market", description: "Market timing analysis", previewNumber: 13 },
  { id: "marketing_online", name: "Digital Marketing", description: "Online marketing plan", previewNumber: 14 },
  { id: "marketing_print", name: "Print Marketing", description: "Traditional marketing", previewNumber: 15 },
  { id: "marketing_social", name: "Social Media", description: "Social proof and reach", previewNumber: 16 },
  { id: "analyze_optimize", name: "Analyze & Optimize", description: "Ongoing strategy", previewNumber: 17 },
  { id: "negotiating", name: "Negotiating Offers", description: "Offer handling process", previewNumber: 18 },
  { id: "typical_transaction", name: "Transaction Timeline", description: "Escrow process flowchart", previewNumber: 19 },
  { id: "promise", name: "Agent Promise", description: "Fiduciary commitment", previewNumber: 20 },
  { id: "back_cover", name: "Back Cover", description: "Branded closing page", required: true, previewNumber: 21 },
];

// Theme 3 (Elegant) - 18 pages
const THEME_3_PAGES: PageConfig[] = [
  { id: "cover", name: "Cover", description: "Property photo, address, agent info", required: true, previewNumber: 1 },
  { id: "contents", name: "Table of Contents", description: "Report overview", previewNumber: 2 },
  { id: "introduction", name: "Introduction", description: "Welcome message from agent", previewNumber: 3 },
  { id: "aerial", name: "Aerial View", description: "Google Maps satellite view", previewNumber: 4 },
  { id: "property_details", name: "Property Details", description: "Owner, APN, beds/baths, tax info", required: true, previewNumber: 5 },
  { id: "area_analysis", name: "Area Sales Analysis", description: "Market statistics chart", previewNumber: 6 },
  { id: "comparables", name: "Sales Comparables", description: "Recently sold properties", required: true, previewNumber: 7 },
  { id: "range_of_sales", name: "Range of Sales", description: "Price range visualization", previewNumber: 8 },
  { id: "how_buyers_find", name: "How Buyers Find Homes", description: "Marketing channels pie chart", previewNumber: 9 },
  { id: "pricing_correctly", name: "Pricing Strategy", description: "Pricing guidance", previewNumber: 10 },
  { id: "avg_days_market", name: "Days on Market", description: "Market timing analysis", previewNumber: 11 },
  { id: "marketing_online", name: "Digital Marketing", description: "Online marketing plan", previewNumber: 12 },
  { id: "marketing_print", name: "Print Marketing", description: "Traditional marketing", previewNumber: 13 },
  { id: "marketing_social", name: "Social Media", description: "Social proof and reach", previewNumber: 14 },
  { id: "analyze_optimize", name: "Analyze & Optimize", description: "Ongoing strategy", previewNumber: 15 },
  { id: "negotiating", name: "Negotiating Offers", description: "Offer handling process", previewNumber: 16 },
  { id: "promise", name: "Agent Promise", description: "Fiduciary commitment", previewNumber: 17 },
  { id: "back_cover", name: "Back Cover", description: "Branded closing page", required: true, previewNumber: 18 },
];

// Theme 4 (Teal) - 7 pages (compact)
const THEME_4_PAGES: PageConfig[] = [
  { id: "cover", name: "Cover", description: "Property photo, address, agent info", required: true, previewNumber: 1 },
  { id: "introduction", name: "Introduction", description: "Welcome message from agent", previewNumber: 2 },
  { id: "property_details", name: "Property Details", description: "Owner, APN, beds/baths, tax info", required: true, previewNumber: 3 },
  { id: "comparables", name: "Sales Comparables", description: "Recently sold properties", required: true, previewNumber: 4 },
  { id: "pricing_correctly", name: "Pricing Strategy", description: "Pricing guidance", previewNumber: 5 },
  { id: "promise", name: "Agent Promise", description: "Fiduciary commitment", previewNumber: 6 },
  { id: "back_cover", name: "Back Cover", description: "Branded closing page", required: true, previewNumber: 7 },
];

// Theme 5 (Bold) - 8 pages (compact)
const THEME_5_PAGES: PageConfig[] = [
  { id: "cover", name: "Cover", description: "Property photo, address, agent info", required: true, previewNumber: 1 },
  { id: "introduction", name: "Introduction", description: "Welcome message from agent", previewNumber: 2 },
  { id: "aerial", name: "Aerial View", description: "Google Maps satellite view", previewNumber: 3 },
  { id: "property_details", name: "Property Details", description: "Owner, APN, beds/baths, tax info", required: true, previewNumber: 4 },
  { id: "comparables", name: "Sales Comparables", description: "Recently sold properties", required: true, previewNumber: 5 },
  { id: "pricing_correctly", name: "Pricing Strategy", description: "Pricing guidance", previewNumber: 6 },
  { id: "promise", name: "Agent Promise", description: "Fiduciary commitment", previewNumber: 7 },
  { id: "back_cover", name: "Back Cover", description: "Branded closing page", required: true, previewNumber: 8 },
];

// ============================================
// THEME DEFINITIONS
// ============================================

export const THEMES: ThemeConfig[] = [
  {
    id: 1,
    name: "Classic",
    description: "Professional navy with elegant fonts",
    defaultColor: "#0d294b",
    pageCount: 20,
    previewBg: "bg-gradient-to-br from-slate-800 to-slate-900",
    fontStyle: "font-serif",
    pages: THEME_1_PAGES,
  },
  {
    id: 2,
    name: "Modern",
    description: "Bold orange accents, clean lines",
    defaultColor: "#f2964a",
    pageCount: 21,
    previewBg: "bg-gradient-to-br from-orange-400 to-orange-600",
    fontStyle: "font-sans",
    pages: THEME_2_PAGES,
  },
  {
    id: 3,
    name: "Elegant",
    description: "Sophisticated gradient overlays",
    defaultColor: "#0d294b",
    pageCount: 18,
    previewBg: "bg-gradient-to-br from-slate-700 to-indigo-900",
    fontStyle: "font-serif",
    pages: THEME_3_PAGES,
  },
  {
    id: 4,
    name: "Teal",
    description: "Modern minimal with teal accent",
    defaultColor: "#16d3ba",
    pageCount: 7,
    previewBg: "bg-gradient-to-br from-teal-400 to-cyan-600",
    fontStyle: "font-sans",
    pages: THEME_4_PAGES,
  },
  {
    id: 5,
    name: "Bold",
    description: "Navy & gold, strong typography",
    defaultColor: "#d79547",
    pageCount: 8,
    previewBg: "bg-gradient-to-br from-slate-800 to-amber-900",
    fontStyle: "font-bold",
    pages: THEME_5_PAGES,
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
 * Get theme configuration by ID
 */
export function getTheme(themeId: number): ThemeConfig | undefined {
  return THEMES.find(t => t.id === themeId);
}

/**
 * Get pages for a specific theme
 */
export function getThemePages(themeId: number): PageConfig[] {
  return getTheme(themeId)?.pages || THEMES[0].pages;
}

/**
 * Get page config by ID within a theme
 */
export function getPageConfig(themeId: number, pageId: string): PageConfig | undefined {
  return getThemePages(themeId).find(p => p.id === pageId);
}

/**
 * Check if theme is compact (fewer pages)
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
  getThemePages,
  getPageConfig,
  isCompactTheme,
  FONTS,
  ICONS,
  R2_BASE_URL,
  PROPERTY_ASSETS_PATH,
};

