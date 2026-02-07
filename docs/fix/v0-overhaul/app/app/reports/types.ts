export type ReportType =
  | "market_snapshot"
  | "new_listings_gallery"
  | "closed"
  | "inventory"
  | "price_bands"
  | "open_houses"
  | "featured_listings"
  | "new_listings";

export type AudienceFilter =
  | "all"
  | "first_time"
  | "luxury"
  | "families"
  | "condo"
  | "investors";

export interface ReportBuilderState {
  areaType: "city" | "zip";
  city: string | null;
  zipCodes: string[];
  reportType: ReportType | null;
  audienceFilter: AudienceFilter | null;
  audienceFilterName: string | null;
  lookbackDays: 7 | 14 | 30 | 60 | 90 | null;
  viewInBrowser: boolean;
  downloadPdf: boolean;
  downloadSocialImage: boolean;
  sendViaEmail: boolean;
  recipientEmails: string[];
}

export const INITIAL_STATE: ReportBuilderState = {
  areaType: "city",
  city: null,
  zipCodes: [],
  reportType: null,
  audienceFilter: null,
  audienceFilterName: null,
  lookbackDays: 30,
  viewInBrowser: true,
  downloadPdf: true,
  downloadSocialImage: false,
  sendViaEmail: false,
  recipientEmails: [],
};

export interface ReportTypeInfo {
  id: ReportType;
  name: string;
  icon: string;
  description: string;
  tag: string;
}

export const PRIMARY_REPORT_TYPES: ReportTypeInfo[] = [
  {
    id: "market_snapshot",
    name: "Market Snapshot",
    icon: "BarChart3",
    description:
      "Complete market overview including active, pending, and closed listings with stats & trends",
    tag: "Monthly market updates",
  },
  {
    id: "new_listings_gallery",
    name: "New Listings",
    icon: "Images",
    description:
      "Photo-rich gallery of recently listed properties in your area",
    tag: "Buyer alerts & prospecting",
  },
  {
    id: "closed",
    name: "Closed Sales",
    icon: "DollarSign",
    description:
      "Recently sold properties with price trends and comparative data",
    tag: "Comparative market analysis",
  },
  {
    id: "inventory",
    name: "Inventory Report",
    icon: "Layers",
    description: "Available properties and current market supply analysis",
    tag: "Market trend tracking",
  },
];

export const SECONDARY_REPORT_TYPES: ReportTypeInfo[] = [
  {
    id: "price_bands",
    name: "Price Bands",
    icon: "BarChart",
    description: "Market segmentation broken down by price ranges",
    tag: "Buyer/seller positioning",
  },
  {
    id: "open_houses",
    name: "Open Houses",
    icon: "Calendar",
    description: "Upcoming open house schedule for your area",
    tag: "Weekend marketing",
  },
  {
    id: "featured_listings",
    name: "Featured Listings",
    icon: "Star",
    description: "Curated showcase of standout properties",
    tag: "Agent listing promotion",
  },
  {
    id: "new_listings",
    name: "New Listings (Table)",
    icon: "Table",
    description: "List-format view of recently listed properties",
    tag: "Weekly prospecting",
  },
];

export interface AudiencePreset {
  id: AudienceFilter;
  name: string;
  description: string;
}

export const AUDIENCE_PRESETS: AudiencePreset[] = [
  { id: "all", name: "All Listings", description: "No filters applied" },
  {
    id: "first_time",
    name: "First-Time Buyers",
    description: "2+ beds, 2+ baths, SFR, \u226470% median",
  },
  {
    id: "luxury",
    name: "Luxury Clients",
    description: "SFR, \u2265150% median price",
  },
  {
    id: "families",
    name: "Families",
    description: "3+ beds, 2+ baths, SFR",
  },
  { id: "condo", name: "Condo Buyers", description: "Condos only" },
  {
    id: "investors",
    name: "Investors",
    description: "\u226450% median price",
  },
];

export const SIMULATED_CITIES = [
  "Los Angeles, CA",
  "Beverly Hills, CA",
  "Austin, TX",
  "Miami, FL",
  "Denver, CO",
  "Seattle, WA",
  "San Francisco, CA",
  "Portland, OR",
  "Nashville, TN",
  "Scottsdale, AZ",
];

export const RECENT_AREAS = ["Los Angeles, CA", "Beverly Hills, CA", "Austin, TX"];

export const ALL_REPORT_TYPES = [...PRIMARY_REPORT_TYPES, ...SECONDARY_REPORT_TYPES];

export function getReportTypeInfo(id: ReportType): ReportTypeInfo | undefined {
  return ALL_REPORT_TYPES.find((r) => r.id === id);
}
