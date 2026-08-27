/**
 * Single source of truth for every fabricated number, city, date, person and
 * brokerage shown anywhere in the UI.
 *
 * WHY THIS FILE EXISTS
 * --------------------
 * The homepage used to price Irvine at $485,000 in the hero and $1.2M in the
 * "Live Preview" section — same city, same page, two different medians. For a
 * product whose only promise is accurate MLS data, contradicting itself about
 * Irvine is disqualifying in a way a broken link is not.
 *
 * RULES
 * -----
 * 1. Nothing here is real. Every figure is illustrative.
 * 2. No demo value is written inline in a component. Import from here.
 * 3. Dates are DERIVED FROM `now`, never hardcoded. A demo report dated
 *    "January 2026" read as eight months stale by August.
 * 4. Brokerage names must be fictional AND verified not to belong to a real
 *    firm — see BROKERAGES below before adding one.
 * 5. Avatar initials must not collide with DEMO_CONTACTS — see AVATAR_INITIALS.
 */

// ─── Market ──────────────────────────────────────────────────────────────────

/**
 * ONE set of Irvine figures, used everywhere Irvine is shown.
 *
 * The hero and the "Live Preview" previously disagreed ($485,000 / 1,247 active
 * vs $1.2M / 847 active). These are the reconciled values: the $1.2M median is
 * the plausible one for Irvine, and the active count is scaled to match.
 */
export const DEMO_MARKET = {
  city: "Irvine",
  state: "CA",
  postalCode: "92602",
  get cityState() {
    return `${this.city}, ${this.state}`;
  },
  medianPrice: "$1.2M",
  medianPriceFull: "$1,185,000",
  activeListings: "847",
  activeListingsLabel: "847 listings",
  daysOnMarket: "24",
  trends: {
    medianPrice: "+3.2%",
    inventory: "-8.1%",
    daysOnMarket: "-12%",
  },
} as const;

/** Secondary demo markets. All SoCal / CRMLS, matching DEMO_MARKET. */
export const DEMO_MARKETS = [
  { name: "Irvine", count: DEMO_MARKET.activeListingsLabel, active: true },
  { name: "Newport Beach", count: "412 listings", active: false },
  { name: "Pasadena", count: "689 listings", active: false },
  { name: "Laguna Beach", count: "203 listings", active: false },
] as const;

/** Price bands for report previews. Consistent with DEMO_MARKET.medianPrice. */
export const DEMO_PRICE_BANDS = [
  { label: "Entry", range: "$450K - $750K", count: 37, pct: 29 },
  { label: "Move-Up", range: "$750K - $1.1M", count: 52, pct: 41 },
  { label: "Premium", range: "$1.1M - $2M", count: 38, pct: 30 },
] as const;

/** A single illustrative listing, for email and theme previews. */
export const DEMO_LISTING = {
  address: "1420 Sycamore Terrace",
  beds: 4,
  baths: 3,
  price: "$1,185,000",
  priceShort: "$1.19M",
  sqft: "2,340",
} as const;

// ─── Brokerages ──────────────────────────────────────────────────────────────

/**
 * Fictional brokerages. NEVER use a real firm here.
 *
 * The site previously credited the invented agent "Sarah Johnson" to "Compass
 * Real Estate" in one card and "Compass Realty" in another — a fake person
 * attached to a real, instantly recognisable brokerage, named two ways.
 *
 * BEFORE ADDING A NAME, SEARCH FOR IT. Plausible-sounding realty names are
 * almost all taken; five of the seven candidates checked while writing this
 * file turned out to be real, active brokerages — including both names the
 * remediation plan itself suggested ("Harbor Point Realty" is a real firm in
 * Panacea FL; "Tidewell Properties" is a real firm in San Diego, the same
 * market as this demo data). The two below were searched and returned no
 * matching brokerage.
 */
export const BROKERAGES = {
  primary: "Marisol Ridge Realty",
  secondary: "Sablecrest Properties",
} as const;

// ─── People ──────────────────────────────────────────────────────────────────

export const DEMO_AGENT = {
  name: "Sarah Johnson",
  initials: "SJ",
  title: "Agent",
  brokerage: BROKERAGES.primary,
  get location() {
    return `${DEMO_AGENT.title}, ${DEMO_MARKET.city}`;
  },
} as const;

/** Contacts shown in the contact-management and lead-capture previews. */
export const DEMO_CONTACTS = [
  { name: "Sarah Johnson", initials: "SJ" },
  { name: "Michael Chen", initials: "MC" },
  { name: "Lisa Patel", initials: "LP" },
  { name: "David Rodriguez", initials: "DR" },
  { name: "Amanda Wilson", initials: "AW" },
] as const;

/**
 * Avatar initials for the /register social-proof row.
 *
 * These MUST NOT overlap with DEMO_CONTACTS. The row previously read
 * "SJ, MC, LP, DR, AW" — the exact initials of the five fake homepage contacts,
 * so the "social proof" was visibly the seed data to anyone who had scrolled
 * the landing page.
 *
 * `assertNoInitialCollision()` below is the guard; call it from a test or a
 * dev-time assertion if these are ever edited.
 */
export const AVATAR_INITIALS = ["RT", "KB", "NF", "OG", "EH"] as const;

/** Returns the colliding initials, or an empty array when the sets are disjoint. */
export function assertNoInitialCollision(): string[] {
  // Set<string>, not the inferred literal union: `as const` narrows both arrays
  // to disjoint literal types, so `.has()` on the narrow set is a compile error
  // rather than a runtime check. Widening keeps the guard meaningful if either
  // list is edited later.
  const contacts: Set<string> = new Set(DEMO_CONTACTS.map((c) => c.initials));
  return AVATAR_INITIALS.filter((i) => contacts.has(i));
}

// ─── Dates ───────────────────────────────────────────────────────────────────

/**
 * All demo dates are relative to `now`. Nothing here is a literal month-year:
 * a hardcoded "January 2026 Report" is correct for about four weeks and stale
 * forever after.
 *
 * These are functions rather than constants so they are evaluated at render,
 * not at module load — a long-lived server process would otherwise freeze the
 * date at boot.
 */
export function currentReportPeriod(now: Date = new Date()): string {
  return now.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

export function lastMonthPeriod(now: Date = new Date()): string {
  const d = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  return d.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

/** "3 weeks ago", "last month" — for "last sent" style labels. */
export function relativeDaysAgo(days: number, now: Date = new Date()): string {
  const then = new Date(now.getTime() - days * 86_400_000);
  const elapsed = Math.round((now.getTime() - then.getTime()) / 86_400_000);
  if (elapsed <= 1) return "yesterday";
  if (elapsed < 7) return `${elapsed} days ago`;
  if (elapsed < 14) return "last week";
  if (elapsed < 31) return `${Math.round(elapsed / 7)} weeks ago`;
  if (elapsed < 60) return "last month";
  return `${Math.round(elapsed / 30)} months ago`;
}
