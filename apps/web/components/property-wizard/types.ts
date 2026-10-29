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
  unit_number?: string;
  unit_type?: string;
  // Last recorded sale, from SiteX's SaleLoanInfo (D-118). Optional because
  // a property that has never transferred has none, and because reports
  // created before the parser read it will not carry them.
  last_sale_price?: number;
  last_sale_date?: string;            // ISO YYYY-MM-DD
  last_sale_price_per_sqft?: number;
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
  /** Suggested accent colors that pair well with this theme */
  suggestedColors: string[];
  pageCount: number;
  /** Preview image path (JPG) — used in theme gallery */
  previewImage?: string;
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
    id: 2,
    name: "Harbor",
    style: "Clean & Contemporary",
    displayFont: "'Manrope', sans-serif",
    gradient: "linear-gradient(135deg, #1A1F36 0%, #FF6B5B 100%)",
    accentDefault: "#FF6B5B",
    suggestedColors: ["#FF6B5B", "#6366F1", "#10B981", "#F59E0B", "#EC4899"],
    pageCount: 6,
    previewImage: "/previews/2.jpg",
  },
  {
    id: 3,
    name: "Linen",
    style: "Sophisticated & Refined",
    displayFont: "'Cormorant Garamond', serif",
    gradient: "linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #C9A962 100%)",
    accentDefault: "#C9A962",
    suggestedColors: ["#C9A962", "#7B8EA8", "#9B6B5E", "#A080B0", "#6B8E6B"],
    pageCount: 6,
    previewImage: "/previews/3.jpg",
  },
  {
    id: 5,
    name: "Atlas",
    style: "Impactful & Striking",
    displayFont: "'Barlow Condensed', sans-serif",
    gradient: "linear-gradient(135deg, #15216E 0%, #1a3a7a 50%, #D69649 100%)",
    accentDefault: "#D69649",
    suggestedColors: ["#D69649", "#4F9BDA", "#E05A47", "#6BBF59", "#C77DBA"],
    pageCount: 6,
    previewImage: "/previews/5.jpg",
  },
];

// ============================================
// Page Definitions
// ============================================

// -----------------------------------------------------------------------------
// PAGE ID CONTRACT — the six pages of the shared property architecture,
// in document order: `PropertyReportBuilder.V2_PAGE_ORDER` in
// apps/worker/src/worker/property_builder.py. Every theme renders these and
// only these. `required` mirrors the builder's `REQUIRED_PAGES`: the builder
// adds a required page even if it is not sent, so the lock here is the truth
// about the document, not a UI preference.
//
// This replaced FULL_PAGES and COMPACT_PAGES, two copies of the retired
// nine-page set. Neither listed `notes`, so every atlas report from the wizard
// rendered without its notes page (agent panel and explainers).
// `tests/test_wizard_pages_match_the_builder.py` asserts this list against
// the builder by parsing both files.
// -----------------------------------------------------------------------------
export const REPORT_PAGES: ReportPage[] = [
  { id: "cover",         name: "Cover & summary",   required: true  },
  { id: "property",      name: "Your home",         required: true  },
  { id: "comparables",   name: "Comparable sales",  required: true  },
  { id: "range",         name: "Range of value",    required: false },
  { id: "market_trends", name: "Market trends",     required: false },
  { id: "notes",         name: "Agent & notes",     required: true  },
];

// ============================================
// Accent Presets & Steps
// ============================================

export const ACCENT_PRESETS = [
  // Blues & Teals
  "#4A90A4", "#0EA5E9", "#34d1c3", "#2563EB",
  // Purples & Pinks
  "#6366F1", "#8B5CF6", "#A855F7", "#EC4899",
  // Reds & Oranges
  "#F43F5E", "#FF6B5B", "#F59E0B", "#D69649",
  // Greens & Earth
  "#10B981", "#22C55E", "#C9A962", "#9B6B5E",
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
