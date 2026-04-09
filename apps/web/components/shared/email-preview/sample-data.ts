export type PreviewReportType =
  | "market_snapshot"
  | "new_listings_gallery"
  | "new_listings"
  | "closed"
  | "inventory"
  | "featured_listings"
  | "price_bands"
  | "open_houses"

export const SAMPLE_PHOTOS = [
  "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1583608205776-bfd35f0d9f83?w=280&h=200&fit=crop",
  "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=280&h=200&fit=crop",
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
    listings: SAMPLE_PHOTOS.slice(0, 4).map((photo, i) => ({
      photo,
      price: ["$1.29M", "$875K", "$1.05M", "$925K"][i],
      address: ["142 Oak Valley Dr", "89 Maple Heights", "310 Sunset Blvd", "27 Pine Ridge Ct"][i],
      specs: ["4 bd | 3 ba | 2,450 sf", "3 bd | 2 ba | 1,800 sf", "4 bd | 3 ba | 2,200 sf", "3 bd | 2 ba | 1,950 sf"][i],
    })),
    tableRows: [],
    quickTake: "Median prices up 4.2% with 42 closed sales. Homes selling in 24 days on average at 98% of list price. A balanced market favoring prepared buyers.",
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
    listings: SAMPLE_PHOTOS.map((photo, i) => ({
      photo,
      price: ["$1.29M", "$875K", "$1.05M", "$925K", "$650K", "$1.48M"][i],
      address: ["142 Oak Valley Dr", "89 Maple Heights", "310 Sunset Blvd", "27 Pine Ridge Ct", "55 Lakeview Ln", "201 Hilltop Way"][i],
      specs: [
        "4 bd | 3 ba | 2,450 sf",
        "3 bd | 2 ba | 1,800 sf",
        "4 bd | 3 ba | 2,200 sf",
        "3 bd | 2 ba | 1,950 sf",
        "3 bd | 2 ba | 1,600 sf",
        "5 bd | 4 ba | 3,100 sf",
      ][i],
    })),
    tableRows: [],
    quickTake: "127 new listings hit the market. Median asking price at $985K with entry-level options starting at $425K. Strong selection across all segments.",
    galleryCount: 127,
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
    listings: SAMPLE_PHOTOS.slice(0, 4).map((photo, i) => ({
      photo,
      price: ["$1.29M", "$875K", "$1.05M", "$925K"][i],
      address: ["142 Oak Valley Dr", "89 Maple Heights", "310 Sunset Blvd", "27 Pine Ridge Ct"][i],
      specs: ["4 bd | 3 ba | 2,450 sf", "3 bd | 2 ba | 1,800 sf", "4 bd | 3 ba | 2,200 sf", "3 bd | 2 ba | 1,950 sf"][i],
      badge: "Sold",
    })),
    tableRows: [
      { address: "142 Oak Valley Dr", beds: 4, baths: 3, sqft: "2,450", price: "$1.29M", dom: 12 },
      { address: "89 Maple Heights", beds: 3, baths: 2, sqft: "1,800", price: "$875K", dom: 21 },
      { address: "310 Sunset Blvd", beds: 4, baths: 3, sqft: "2,200", price: "$1.05M", dom: 8 },
    ],
    quickTake: "42 homes sold at a median of $1.08M. Average DOM of 18 days with 98.2% close-to-list ratio. Sellers are getting strong offers quickly.",
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
    listings: SAMPLE_PHOTOS.slice(0, 4).map((photo, i) => ({
      photo,
      price: ["$1.35M", "$795K", "$1.12M", "$980K"][i],
      address: ["55 Lakeview Ln", "201 Hilltop Way", "78 Cedar Park", "340 Riverdale"][i],
      specs: ["5 bd | 4 ba | 3,100 sf", "3 bd | 2 ba | 1,700 sf", "4 bd | 3 ba | 2,400 sf", "3 bd | 3 ba | 2,050 sf"][i],
      badge: "Active",
    })),
    tableRows: [
      { address: "55 Lakeview Ln", beds: 5, baths: 4, sqft: "3,100", price: "$1.35M", dom: 14 },
      { address: "201 Hilltop Way", beds: 3, baths: 2, sqft: "1,700", price: "$795K", dom: 28 },
      { address: "78 Cedar Park", beds: 4, baths: 3, sqft: "2,400", price: "$1.12M", dom: 7 },
    ],
    quickTake: "186 active listings with 3.1 months of supply. Median asking price at $1.12M. Enough inventory for buyers to be selective without excessive competition.",
  },

  featured_listings: {
    heroLabel: "Featured Listings",
    heroValue: "4",
    heroSub: "hand-picked properties",
    narrative:
      "These standout properties represent the best current opportunities in the area. Each offers exceptional value, location, or features that make them worth immediate attention.",
    stats: [
      { label: "Price Range", value: "$875K – $1.5M" },
      { label: "Avg Sq Ft", value: "2,388" },
    ],
    listings: SAMPLE_PHOTOS.slice(0, 4).map((photo, i) => ({
      photo,
      price: ["$1.50M", "$1.15M", "$985K", "$875K"][i],
      address: ["8 Grandview Terrace", "142 Oak Valley Dr", "310 Sunset Blvd", "89 Maple Heights"][i],
      specs: [
        "5 bd | 4 ba | 3,200 sf",
        "4 bd | 3 ba | 2,450 sf",
        "4 bd | 3 ba | 2,200 sf",
        "3 bd | 2 ba | 1,700 sf",
      ][i],
    })),
    tableRows: [],
    quickTake: "4 featured properties ranging from $875K to $1.5M. Prime locations with above-average square footage and move-in ready condition.",
    galleryCount: 4,
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
    listings: SAMPLE_PHOTOS.slice(0, 3).map((photo, i) => ({
      photo,
      price: ["$625K", "$922K", "$1.35M"][i],
      address: ["415 Birch Ct", "142 Oak Valley Dr", "8 Grandview Terrace"][i],
      specs: ["2 bd | 2 ba | 1,200 sf", "4 bd | 3 ba | 2,450 sf", "5 bd | 4 ba | 3,200 sf"][i],
      badge: ["Low", "Median", "High"][i],
    })),
    tableRows: [],
    quickTake: "42 new listings with a median of $922K. Entry-level at $625K, luxury at $1.35M. Broad selection for every buyer segment.",
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
    listings: SAMPLE_PHOTOS.slice(0, 4).map((photo, i) => ({
      photo,
      price: ["$649K", "$895K", "$1.18M", "$1.72M"][i],
      address: ["330 Elm Way", "89 Maple Heights", "78 Cedar Park", "12 Summit Ridge"][i],
      specs: ["2 bd | 2 ba | 1,400 sf", "3 bd | 2 ba | 1,800 sf", "4 bd | 3 ba | 2,400 sf", "5 bd | 4 ba | 3,500 sf"][i],
    })),
    tableRows: [],
    quickTake: "117 active listings across 4 price bands. Heaviest activity in the $700K–$1M segment with 42 homes available.",
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
    listings: SAMPLE_PHOTOS.map((photo, i) => ({
      photo,
      price: ["$1.29M", "$875K", "$1.05M", "$925K", "$650K", "$1.48M"][i],
      address: ["142 Oak Valley Dr", "89 Maple Heights", "310 Sunset Blvd", "27 Pine Ridge Ct", "55 Lakeview Ln", "201 Hilltop Way"][i],
      specs: [
        "4 bd | 3 ba | 2,450 sf",
        "3 bd | 2 ba | 1,800 sf",
        "4 bd | 3 ba | 2,200 sf",
        "3 bd | 2 ba | 1,950 sf",
        "3 bd | 2 ba | 1,600 sf",
        "5 bd | 4 ba | 3,100 sf",
      ][i],
    })),
    tableRows: [],
    quickTake: "14 open houses this weekend. Price range from $425K to $1.48M with something for every buyer.",
    galleryCount: 14,
  },
}
