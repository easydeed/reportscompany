/**
 * Shared types and constants for the Property Report Wizard
 */

import { DEFAULT_THEME_ID } from "@/lib/themes.generated";

// Property data from SiteX
export interface PropertyData {
  full_address: string;
  street: string;
  city: string;
  state: string;
  zip_code: string;
  county: string;
  apn: string;
  owner_name: string;
  legal_description?: string;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  lot_size?: string;
  year_built?: number;
  assessed_value?: number;
  tax_amount?: number;
  latitude: number;
  longitude: number;
  property_type?: string;
}

// Comparable property (normalized from API)
export interface Comparable {
  id: string;
  address: string;
  city?: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  year_built?: number;
  lat?: number;
  lng?: number;
  photo_url?: string;
  distance_miles?: number;
  status?: string;
  days_on_market?: number;
}

// Theme definitions matching the worker's property templates (apps/worker/src/worker/templates/property/)
// The ids are 2, 3 and 5 — the cut to three themes retired 1 (classic)
// and 4 (teal) and ids are never reused, so the gaps are deliberate.
// `__tests__/ThemeRegistry.test.ts` asserts this list's id set against
// lib/themes.generated.ts, which is generated from the renderer's own
// themes.json. Four lists like this one existed and no two agreed.
export const THEMES = [
  {
    id: 2,
    name: "Modern",
    description: "Bold orange accents with Montserrat",
    defaultColor: "#f2964a",
    pages: "full" as const,
    previewBg: "bg-gradient-to-br from-orange-400 to-orange-600",
  },
  {
    id: 3,
    name: "Elegant",
    description: "Sophisticated with gradient overlays",
    defaultColor: "#0d294b",
    pages: "full" as const,
    previewBg: "bg-gradient-to-br from-slate-700 to-indigo-900",
  },
  {
    id: 5,
    name: "Bold",
    description: "Navy & gold with Bebas Neue",
    defaultColor: "#d79547",
    pages: "compact" as const,
    previewBg: "bg-gradient-to-br from-slate-800 to-amber-900",
  },
] as const;

export type ThemeId = (typeof THEMES)[number]["id"];

//: The entry the helpers fall back to. Asserted non-undefined because a
//: registry default that is not in THEMES is a build-time mistake, not a
//: runtime condition to paper over.
export const DEFAULT_THEME = THEMES.find((t) => t.id === DEFAULT_THEME_ID)!;

// All available report pages
export const ALL_PAGES = [
  { id: "cover", name: "Cover", description: "Property photo, address, agent info", required: true },
  { id: "contents", name: "Table of Contents", description: "Report overview" },
  { id: "introduction", name: "Introduction", description: "Welcome message from agent" },
  { id: "aerial", name: "Aerial View", description: "Google Maps satellite view" },
  { id: "property_details", name: "Property Details", description: "Owner, APN, beds/baths, tax info", required: true },
  { id: "area_analysis", name: "Area Sales Analysis", description: "Market statistics chart" },
  { id: "comparables", name: "Sales Comparables", description: "Recently sold properties", required: true },
  { id: "range_of_sales", name: "Range of Sales", description: "Price range visualization" },
  { id: "neighborhood", name: "Neighborhood Stats", description: "Demographics and averages" },
  { id: "roadmap", name: "Selling Roadmap", description: "Process overview" },
  { id: "how_buyers_find", name: "How Buyers Find Homes", description: "Marketing channels pie chart" },
  { id: "pricing_correctly", name: "Pricing Strategy", description: "Pricing guidance" },
  { id: "avg_days_market", name: "Days on Market", description: "Market timing analysis" },
  { id: "marketing_online", name: "Digital Marketing", description: "Online marketing plan" },
  { id: "marketing_print", name: "Print Marketing", description: "Traditional marketing" },
  { id: "marketing_social", name: "Social Media", description: "Social proof and reach" },
  { id: "analyze_optimize", name: "Analyze & Optimize", description: "Ongoing strategy" },
  { id: "negotiating", name: "Negotiating Offers", description: "Offer handling process" },
  { id: "typical_transaction", name: "Transaction Timeline", description: "Escrow process flowchart" },
  { id: "promise", name: "Agent Promise", description: "Fiduciary commitment" },
  { id: "back_cover", name: "Back Cover", description: "Branded closing page", required: true },
] as const;

export type PageId = (typeof ALL_PAGES)[number]["id"];

// Compact page set (for themes 4 & 5)
export const COMPACT_PAGES: PageId[] = [
  "cover",
  "introduction",
  "aerial",
  "property_details",
  "comparables",
  "pricing_correctly",
  "marketing_online",
  "promise",
  "back_cover",
];

// Get required page IDs
export const REQUIRED_PAGES = ALL_PAGES.filter((p) => "required" in p && p.required).map((p) => p.id);

// Wizard state
export interface WizardState {
  // Step 1: Property Search
  address: string;
  cityStateZip: string;
  property: PropertyData | null;

  // Step 2: Comparables (IDs only, actual comps stored separately)
  selectedCompIds: string[];

  // Step 3: Theme & Pages
  theme: ThemeId;
  accentColor: string;
  selectedPages: string[];

  // Step 4: Generated report
  reportId: string | null;
}

export const initialWizardState: WizardState = {
  address: "",
  cityStateZip: "",
  property: null,
  selectedCompIds: [],
  // Was the literal 1 (classic). `ThemeId` is derived from THEMES, so the
  // theme cut turned this into a type error rather than a wizard that opens
  // on a theme the renderer cannot build — which is the whole argument for
  // deriving the type instead of writing `1 | 2 | 3 | 4 | 5`.
  theme: DEFAULT_THEME.id,
  accentColor: "#0d294b",
  selectedPages: ALL_PAGES.map((p) => p.id),
  reportId: null,
};

// Search params for comparables
export interface SearchParams {
  radius_miles: number;
  sqft_variance: number;
}

export const defaultSearchParams: SearchParams = {
  radius_miles: 0.5,
  sqft_variance: 0.2,
};

// Generated report result
export interface GeneratedReport {
  id: string;
  pdf_url: string;
  qr_code_url: string;
  short_code: string;
}

// Validation helpers
export const canProceedToStep = {
  2: (state: WizardState) => state.property !== null,
  3: (state: WizardState) =>
    state.selectedCompIds.length >= 4 && state.selectedCompIds.length <= 8,
  4: (state: WizardState) =>
    state.theme >= 1 &&
    state.theme <= 5 &&
    state.selectedPages.length >= REQUIRED_PAGES.length &&
    REQUIRED_PAGES.every((p) => state.selectedPages.includes(p)),
};

// Helper to get default pages for a theme
export function getDefaultPagesForTheme(themeId: ThemeId): string[] {
  const theme = THEMES.find((t) => t.id === themeId);
  if (theme?.pages === "compact") {
    return COMPACT_PAGES;
  }
  return ALL_PAGES.map((p) => p.id);
}

// Helper to get theme by ID
export function getThemeById(id: ThemeId) {
  // `|| THEMES[0]` used to mean "classic"; after the cut THEMES[0] is
  // whichever theme happens to sort first, which is not a decision anyone
  // made. Resolve through the registry instead.
  return THEMES.find((t) => t.id === id) || DEFAULT_THEME;
}

// Preset accent colors
export const PRESET_COLORS = [
  "#0d294b", // Navy
  "#1e40af", // Blue
  "#4F46E5", // Purple
  "#059669", // Green
  "#16d3ba", // Teal
  "#d97706", // Amber
  "#dc2626", // Red
  "#be185d", // Pink
  "#374151", // Gray
  "#000000", // Black
];

