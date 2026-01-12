/**
 * Shared types and constants for the Property Report Wizard
 */

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

// Theme definitions matching seller_report.jinja2
export const THEMES = [
  {
    id: 1,
    name: "Classic",
    description: "Professional navy with Bariol/Nexa fonts",
    defaultColor: "#0d294b",
    pages: "full" as const,
    previewBg: "bg-gradient-to-br from-slate-800 to-slate-900",
  },
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
    id: 4,
    name: "Teal",
    description: "Modern minimal with teal accent",
    defaultColor: "#16d3ba",
    pages: "compact" as const,
    previewBg: "bg-gradient-to-br from-teal-400 to-cyan-600",
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
export const REQUIRED_PAGES = ALL_PAGES.filter((p) => p.required).map((p) => p.id);

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
  theme: 1,
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
  return THEMES.find((t) => t.id === id) || THEMES[0];
}

// Preset accent colors
export const PRESET_COLORS = [
  "#0d294b", // Navy
  "#1e40af", // Blue
  "#7c3aed", // Purple
  "#059669", // Green
  "#16d3ba", // Teal
  "#d97706", // Amber
  "#dc2626", // Red
  "#be185d", // Pink
  "#374151", // Gray
  "#000000", // Black
];

