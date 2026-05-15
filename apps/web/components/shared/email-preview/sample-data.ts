export type PreviewReportType =
  | "market_snapshot"
  | "new_listings_gallery"
  | "new_listings"
  | "closed"
  | "inventory"
  | "featured_listings"
  | "price_bands"
  | "open_houses"

// Per-type listing caps mirroring PDF_CONFIG in
// apps/worker/src/worker/market_builder.py. Keep in sync.
export const PREVIEW_CAPS: Record<PreviewReportType, number> = {
  market_snapshot: 8,
  new_listings_gallery: 24,
  new_listings: 24,
  closed: 20,
  inventory: 20,
  featured_listings: 12,
  open_houses: 20,
  price_bands: 8,
}

// Section labels mirror PDF_CONFIG[type].section_label in
// apps/worker/src/worker/market_builder.py. Keep in sync.
export const PDF_SECTION_LABELS: Record<PreviewReportType, string> = {
  market_snapshot: "Recent Activity",
  new_listings_gallery: "New Listings",
  new_listings: "New Listings",
  closed: "Recent Closed Sales",
  inventory: "Active Inventory Sample",
  featured_listings: "Hand-Picked Highlights",
  open_houses: "Open Houses This Week",
  price_bands: "Example Listings by Price Band",
}

// Layout grouping for PDF preview rendering.
// Mirrors LAYOUT_MAP in apps/worker/src/worker/market_builder.py.
export type PDFLayoutType =
  | "gallery"
  | "market_narrative"
  | "closed_inventory"
  | "analytics"
  | "pricebands"

export const PDF_LAYOUT_MAP: Record<PreviewReportType, PDFLayoutType> = {
  new_listings_gallery: "gallery",
  featured_listings: "gallery",
  open_houses: "gallery",
  market_snapshot: "market_narrative",
  closed: "closed_inventory",
  inventory: "closed_inventory",
  price_bands: "pricebands",
  new_listings: "analytics",
}

export const SAMPLE_PHOTOS = [
  "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1583608205776-bfd35f0d9f83?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1598228723793-52759bba239c?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1572120360610-d971b9d7767c?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1576941089067-2de3c901e126?w=280&h=200&fit=crop",
]

export interface SampleListing {
  photo: string
  price: string
  address: string
  specs: string
  badge?: string
}

export interface SampleStat {
  label: string
  value: string
  sub?: string
}

export interface SampleTableRow {
  address: string
  beds: number
  baths: number
  sqft: string
  price: string
  dom: number
}

interface PreviewContent {
  heroLabel: string
  heroValue: string
  heroSub?: string
  narrative: string
  stats: SampleStat[]
  listings: SampleListing[]
  tableRows: SampleTableRow[]
  quickTake: string
  galleryCount?: number
  // Total available before truncation. When totalAvailable > listings.length,
  // the preview shows "Showing X of Y" + "+ N more …" callouts to mirror PDF.
  totalAvailable?: number
}

// Pool of distinct sample listings — large enough to populate every report type
// up to its PREVIEW_CAPS limit while still leaving room for a "+ N more" callout.
const LISTING_POOL: SampleListing[] = [
  { photo: SAMPLE_PHOTOS[0], price: "$1.29M", address: "142 Oak Valley Dr", specs: "4 bd | 3 ba | 2,450 sf" },
  { photo: SAMPLE_PHOTOS[1], price: "$875K", address: "89 Maple Heights", specs: "3 bd | 2 ba | 1,800 sf" },
  { photo: SAMPLE_PHOTOS[2], price: "$1.05M", address: "310 Sunset Blvd", specs: "4 bd | 3 ba | 2,200 sf" },
  { photo: SAMPLE_PHOTOS[3], price: "$925K", address: "27 Pine Ridge Ct", specs: "3 bd | 2 ba | 1,950 sf" },
  { photo: SAMPLE_PHOTOS[4], price: "$650K", address: "55 Lakeview Ln", specs: "3 bd | 2 ba | 1,600 sf" },
  { photo: SAMPLE_PHOTOS[5], price: "$1.48M", address: "201 Hilltop Way", specs: "5 bd | 4 ba | 3,100 sf" },
  { photo: SAMPLE_PHOTOS[6], price: "$1.12M", address: "78 Cedar Park", specs: "4 bd | 3 ba | 2,400 sf" },
  { photo: SAMPLE_PHOTOS[7], price: "$795K", address: "340 Riverdale", specs: "3 bd | 3 ba | 2,050 sf" },
  { photo: SAMPLE_PHOTOS[8], price: "$1.50M", address: "8 Grandview Terrace", specs: "5 bd | 4 ba | 3,200 sf" },
  { photo: SAMPLE_PHOTOS[9], price: "$619K", address: "415 Birch Ct", specs: "2 bd | 2 ba | 1,200 sf" },
  { photo: SAMPLE_PHOTOS[10], price: "$1.18M", address: "92 Highland Dr", specs: "4 bd | 3 ba | 2,350 sf" },
  { photo: SAMPLE_PHOTOS[11], price: "$849K", address: "73 Brookside Ave", specs: "3 bd | 2 ba | 1,750 sf" },
  { photo: SAMPLE_PHOTOS[0], price: "$1.05M", address: "612 Linden St", specs: "4 bd | 2 ba | 2,100 sf" },
  { photo: SAMPLE_PHOTOS[1], price: "$729K", address: "148 Aspen Way", specs: "3 bd | 2 ba | 1,650 sf" },
  { photo: SAMPLE_PHOTOS[2], price: "$1.62M", address: "44 Summit Pl", specs: "5 bd | 4 ba | 3,400 sf" },
  { photo: SAMPLE_PHOTOS[3], price: "$899K", address: "256 Willow Bend", specs: "3 bd | 3 ba | 1,950 sf" },
  { photo: SAMPLE_PHOTOS[4], price: "$1.10M", address: "37 Stonebridge Rd", specs: "4 bd | 3 ba | 2,300 sf" },
  { photo: SAMPLE_PHOTOS[5], price: "$555K", address: "509 Cottage Ln", specs: "2 bd | 1 ba | 1,100 sf" },
  { photo: SAMPLE_PHOTOS[6], price: "$1.34M", address: "8 Vista Park", specs: "4 bd | 3 ba | 2,600 sf" },
  { photo: SAMPLE_PHOTOS[7], price: "$945K", address: "123 Garden Cir", specs: "3 bd | 2 ba | 1,850 sf" },
  { photo: SAMPLE_PHOTOS[8], price: "$1.78M", address: "16 Crestwood Dr", specs: "5 bd | 4 ba | 3,650 sf" },
  { photo: SAMPLE_PHOTOS[9], price: "$685K", address: "302 Magnolia Ct", specs: "2 bd | 2 ba | 1,400 sf" },
  { photo: SAMPLE_PHOTOS[10], price: "$1.22M", address: "411 Sycamore Ln", specs: "4 bd | 3 ba | 2,500 sf" },
  { photo: SAMPLE_PHOTOS[11], price: "$815K", address: "67 Harbor View", specs: "3 bd | 2 ba | 1,720 sf" },
]

function takeListings(count: number, badge?: string): SampleListing[] {
  return LISTING_POOL.slice(0, count).map((l) => (badge ? { ...l, badge } : l))
}

export const PREVIEW_CONTENT: Record<PreviewReportType, PreviewContent> = {
  market_snapshot: {
    heroLabel: "Median Sale Price",
    heroValue: "$925,000",
    heroSub: "+4.2% vs prior period",
    narrative:
      "The market showed balanced activity this period with stable pricing and moderate inventory. Buyer demand remains consistent as homes continue to sell near asking price with reasonable days on market.",
    stats: [
      { label: "Closed Sales", value: "42", sub: "+8%" },
      { label: "Avg DOM", value: "24", sub: "-3 days" },
      { label: "Months of Inventory", value: "2.4", sub: "Seller's market" },
      { label: "List-to-Sale", value: "98.2%", sub: "Near asking" },
    ],
    listings: takeListings(PREVIEW_CAPS.market_snapshot),
    tableRows: [],
    quickTake: "Median prices up 4.2% with 42 closed sales. Homes selling in 24 days on average at 98% of list price. A balanced market favoring prepared buyers.",
    totalAvailable: 50,
  },

  new_listings_gallery: {
    heroLabel: "New Listings",
    heroValue: "127",
    heroSub: "in the last 14 days",
    narrative:
      "Fresh inventory continues to hit the market at a healthy pace. This period saw strong activity across all price segments with several standout properties worth immediate attention.",
    stats: [
      { label: "Median List Price", value: "$985K" },
      { label: "Starting From", value: "$425K" },
    ],
    // Gallery shows up to its full cap (24); sample data is also 24 → no truncation.
    listings: takeListings(PREVIEW_CAPS.new_listings_gallery),
    tableRows: [],
    quickTake: "127 new listings hit the market. Median asking price at $985K with entry-level options starting at $425K. Strong selection across all segments.",
    galleryCount: 127,
    totalAvailable: 24,
  },

  closed: {
    heroLabel: "Total Closed",
    heroValue: "42",
    heroSub: "in the last 30 days",
    narrative:
      "Closed sales remained strong this period. Properties sold at near-asking prices with competitive days on market. The data confirms sustained buyer demand across most price tiers.",
    stats: [
      { label: "Median Sold", value: "$1.08M", sub: "+2.1%" },
      { label: "Avg DOM", value: "18", sub: "-5 days" },
      { label: "Close-to-List", value: "98.2%" },
    ],
    listings: takeListings(PREVIEW_CAPS.closed, "Sold"),
    tableRows: [
      { address: "142 Oak Valley Dr", beds: 4, baths: 3, sqft: "2,450", price: "$1.29M", dom: 12 },
      { address: "89 Maple Heights", beds: 3, baths: 2, sqft: "1,800", price: "$875K", dom: 21 },
      { address: "310 Sunset Blvd", beds: 4, baths: 3, sqft: "2,200", price: "$1.05M", dom: 8 },
    ],
    quickTake: "42 homes sold at a median of $1.08M. Average DOM of 18 days with 98.2% close-to-list ratio. Sellers are getting strong offers quickly.",
    totalAvailable: 42,
  },

  inventory: {
    heroLabel: "Active Listings",
    heroValue: "186",
    heroSub: "currently on market",
    narrative:
      "Current inventory levels indicate a balanced market with healthy options for buyers. Supply has increased modestly, providing more choices without tipping into oversupply.",
    stats: [
      { label: "Median Active", value: "$1.12M" },
      { label: "Avg DOM", value: "31", sub: "Active" },
      { label: "Months Supply", value: "3.1" },
    ],
    listings: takeListings(PREVIEW_CAPS.inventory, "Active"),
    tableRows: [
      { address: "55 Lakeview Ln", beds: 5, baths: 4, sqft: "3,100", price: "$1.35M", dom: 14 },
      { address: "201 Hilltop Way", beds: 3, baths: 2, sqft: "1,700", price: "$795K", dom: 28 },
      { address: "78 Cedar Park", beds: 4, baths: 3, sqft: "2,400", price: "$1.12M", dom: 7 },
    ],
    quickTake: "186 active listings with 3.1 months of supply. Median asking price at $1.12M. Enough inventory for buyers to be selective without excessive competition.",
    totalAvailable: 186,
  },

  featured_listings: {
    heroLabel: "Featured Listings",
    heroValue: "12",
    heroSub: "hand-picked properties",
    narrative:
      "These standout properties represent the best current opportunities in the area. Each offers exceptional value, location, or features that make them worth immediate attention.",
    stats: [
      { label: "Price Range", value: "$555K – $1.78M" },
      { label: "Avg Sq Ft", value: "2,388" },
    ],
    listings: takeListings(PREVIEW_CAPS.featured_listings),
    tableRows: [],
    quickTake: "12 featured properties ranging from $555K to $1.78M. Prime locations with above-average square footage and move-in ready condition.",
    galleryCount: 12,
    totalAvailable: 12,
  },

  new_listings: {
    heroLabel: "New This Month",
    heroValue: "42",
    heroSub: "new listings entered the market",
    narrative:
      "Forty-two new listings entered the market this month, keeping the flow of fresh inventory consistent. The median list price sits at $922K with options spanning from starter condos to luxury estates.",
    stats: [
      { label: "Median Price", value: "$922K" },
      { label: "Avg DOM", value: "11", sub: "New" },
      { label: "Price / Sq Ft", value: "$520" },
      { label: "Months Supply", value: "2.1" },
    ],
    listings: takeListings(PREVIEW_CAPS.new_listings),
    tableRows: [],
    quickTake: "42 new listings with a median of $922K. Entry-level at $625K, luxury at $1.35M. Broad selection for every buyer segment.",
    totalAvailable: 42,
  },

  price_bands: {
    heroLabel: "Active Listings",
    heroValue: "117",
    heroSub: "across all price bands",
    narrative:
      "Activity is concentrated in the $780K–$1.1M band where the majority of recent listings are clustered. Move-up buyers and investors will find distinct opportunities at both ends of the spectrum.",
    stats: [
      { label: "Under $700K", value: "18" },
      { label: "$700K – $1M", value: "42" },
      { label: "$1M – $1.5M", value: "38" },
      { label: "Over $1.5M", value: "19" },
    ],
    listings: takeListings(PREVIEW_CAPS.price_bands),
    tableRows: [],
    quickTake: "117 active listings across 4 price bands. Heaviest activity in the $700K–$1M segment with 42 homes available.",
    totalAvailable: 117,
  },

  open_houses: {
    heroLabel: "Open Houses",
    heroValue: "14",
    heroSub: "this weekend",
    narrative:
      "Fourteen open houses are scheduled this weekend across a wide range of price points. Several newly listed properties will be showing for the first time — a great opportunity for serious buyers.",
    stats: [
      { label: "Median List Price", value: "$985K" },
      { label: "Starting From", value: "$425K" },
    ],
    listings: takeListings(PREVIEW_CAPS.open_houses),
    tableRows: [],
    quickTake: "14 open houses this weekend. Price range from $425K to $1.48M with something for every buyer.",
    galleryCount: 14,
    totalAvailable: 14,
  },
}
