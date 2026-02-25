// ============================================
// Property Report Wizard — Types & Constants
// ============================================

export interface PropertyData {
  street_address: string;
  city: string;
  state: string;
  zip_code: string;
  full_address: string;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  lot_size: number;
  year_built: number;
  owner_name: string;
  apn: string;
  assessed_value: number;
  tax_amount: number;
  latitude: number;
  longitude: number;
  property_type?: string;
  county?: string;
  legal_description?: string;
}

export interface Comparable {
  id: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  sale_price: number;
  sold_date: string;
  list_price: number;
  list_date: string;
  sqft: number;
  bedrooms: number;
  bathrooms: number;
  year_built: number;
  distance_miles: number;
  price_per_sqft: number;
  status: string;
  dom: number;
  photo_url: string | null;
  lat?: number;
  lng?: number;
}

export interface Theme {
  id: number;
  name: string;
  style: string;
  displayFont: string;
  gradient: string;
  accentDefault: string;
  pageCount: number;
  compact: boolean;
}

export interface ReportPage {
  id: string;
  name: string;
  required: boolean;
}

export interface PropertyReportResponse {
  id: string;
  status: "pending" | "processing" | "complete" | "completed" | "failed";
  pdf_url: string | null;
  short_code: string | null;
  qr_code_url: string | null;
  error_message: string | null;
  created_at?: string;
}

// ============================================
// Theme Definitions (match backend Jinja2 templates)
// ============================================

export const THEMES: Theme[] = [
  {
    id: 1,
    name: "Classic",
    style: "Timeless & Professional",
    displayFont: "'Merriweather', serif",
    gradient: "linear-gradient(135deg, #1B365D 0%, #2D5F8A 100%)",
    accentDefault: "#4A90A4",
    pageCount: 8,
    compact: false,
  },
  {
    id: 2,
    name: "Modern",
    style: "Clean & Contemporary",
    displayFont: "'Space Grotesk', sans-serif",
    gradient: "linear-gradient(135deg, #1A1F36 0%, #FF6B5B 100%)",
    accentDefault: "#FF6B5B",
    pageCount: 8,
    compact: false,
  },
  {
    id: 3,
    name: "Elegant",
    style: "Sophisticated & Refined",
    displayFont: "'Playfair Display', serif",
    gradient: "linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #C9A962 100%)",
    accentDefault: "#C9A962",
    pageCount: 8,
    compact: false,
  },
  {
    id: 4,
    name: "Teal",
    style: "Vibrant & Modern",
    displayFont: "'Montserrat', sans-serif",
    gradient: "linear-gradient(135deg, #18235c 0%, #34d1c3 100%)",
    accentDefault: "#34d1c3",
    pageCount: 8,
    compact: true,
  },
  {
    id: 5,
    name: "Bold",
    style: "Impactful & Striking",
    displayFont: "'Oswald', sans-serif",
    gradient: "linear-gradient(135deg, #15216E 0%, #1a3a7a 50%, #D69649 100%)",
    accentDefault: "#D69649",
    pageCount: 8,
    compact: true,
  },
];

// ============================================
// Page Definitions
// ============================================

// -----------------------------------------------------------------------------
// PAGE ID CONTRACT — must match the keys used in base.jinja2 page_set checks.
// Template page order: cover → contents → aerial → property → analysis →
//                      market_trends → comparables → range
// -----------------------------------------------------------------------------

// NOTE: FULL_PAGES and COMPACT_PAGES currently map to the same 8 Jinja2 template
// pages supported by base.jinja2. Extended "seller education" pages (roadmap,
// pricing strategy, etc.) will be added here when their templates are built.
export const FULL_PAGES: ReportPage[] = [
  { id: "cover",         name: "Cover",               required: false },
  { id: "contents",      name: "Table of Contents",   required: false },
  { id: "aerial",        name: "Aerial View",         required: false },
  { id: "property",      name: "Property Details",    required: true  },
  { id: "analysis",      name: "Area Sales Analysis", required: false },
  { id: "market_trends", name: "Market Trends",       required: false },
  { id: "comparables",   name: "Sales Comparables",   required: true  },
  { id: "range",         name: "Range of Sales",      required: false },
];

export const COMPACT_PAGES: ReportPage[] = [
  { id: "cover",         name: "Cover",               required: false },
  { id: "contents",      name: "Table of Contents",   required: false },
  { id: "aerial",        name: "Aerial View",         required: false },
  { id: "property",      name: "Property Details",    required: true  },
  { id: "analysis",      name: "Area Sales Analysis", required: false },
  { id: "market_trends", name: "Market Trends",       required: false },
  { id: "comparables",   name: "Sales Comparables",   required: true  },
  { id: "range",         name: "Range of Sales",      required: false },
];

// ============================================
// Accent Presets & Steps
// ============================================

export const ACCENT_PRESETS = [
  "#4A90A4",
  "#FF6B5B",
  "#C9A962",
  "#34d1c3",
  "#D69649",
  "#6366F1",
  "#10B981",
  "#F43F5E",
  "#8B5CF6",
  "#0EA5E9",
];

export const STEPS = [
  { label: "Property", iconName: "Home" as const },
  { label: "Comparables", iconName: "BarChart3" as const },
  { label: "Theme & Pages", iconName: "Palette" as const },
  { label: "Generate", iconName: "Sparkles" as const },
];

// ============================================
// Auto-select scoring
// ============================================

export function autoSelectComps(
  comps: Comparable[],
  subject: PropertyData
): string[] {
  return comps
    .map((c) => ({
      id: c.id,
      score:
        (1 / (c.distance_miles + 0.1)) * 10 +
        (1 / (Math.abs(c.sqft - subject.sqft) + 100)) * 1000 +
        (c.bedrooms === subject.bedrooms ? 5 : 0) +
        (c.bathrooms === subject.bathrooms ? 3 : 0),
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 6)
    .map((c) => c.id);
}
