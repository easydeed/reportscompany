// The /r/{id} consumer report's figures, worded as the PDF words them.
//
// Owner decision, 2026-11-04: the page shows the PDF's range — lowest to
// highest closed comparable sale, with "Range of the comparable sales shown."
// beside it — and no "most likely" price or size-based estimate. The market
// tab states the window and radius the comps actually cover, computed by the
// API with the PDF's rules (api/services/comp_summary.py).

export type CompsRange = { low: number; high: number; count: number; method: string }

export type ConsumerMarketStats = {
  median_price?: number | null
  median_price_per_sqft?: number | null
  avg_days_on_market?: number | null
  homes_sold: number
  window_months?: number | null
  radius_miles?: number | null
}

export const RANGE_HEADING = "What the comparable sales support"
export const NO_RANGE =
  "No closed comparable sales were found near this home, so this report does not give a range."

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

export function rangeBasis(range: CompsRange): string {
  return `Based on ${plural(range.count, "closed sale", "closed sales")}`
}

export function homesSoldLabel(stats: ConsumerMarketStats): string {
  return stats.window_months ? `Homes sold (last ${stats.window_months} months)` : "Homes sold"
}

/** "Based on 4 closed comparable sales within 0.6 mi of your home in the last 6 months." */
export function compsSentence(stats: ConsumerMarketStats): string {
  const parts = [`Based on ${plural(stats.homes_sold, "closed comparable sale", "closed comparable sales")}`]
  if (stats.radius_miles) parts.push(`within ${stats.radius_miles} mi of your home`)
  if (stats.window_months) parts.push(`in the last ${stats.window_months} months`)
  return parts.join(" ") + "."
}
