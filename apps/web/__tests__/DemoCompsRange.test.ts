/**
 * LR-025 (D-383): the landing page's property-report card shows the range of
 * the comparable sales it lists, as the report does (D-134), never an
 * "estimated value". Its figures are computed from its own list, so they
 * cannot disagree with it the way the old $1.05M–$1.32M bar did.
 */
import { DEMO_COMPS, DEMO_COMPS_RANGE } from "@/lib/demo-data"

const dollars = (s: string) => Number(s.replace(/[$,]/g, ""))
const millions = (s: string) => Number(s.replace(/[$M]/g, "")) * 1_000_000

describe("the property-report card's range", () => {
  it("is the lowest and highest comparable sale it lists", () => {
    const prices = DEMO_COMPS.map((c) => dollars(c.price))
    expect(Math.abs(millions(DEMO_COMPS_RANGE.low) - Math.min(...prices))).toBeLessThanOrEqual(5_000)
    expect(Math.abs(millions(DEMO_COMPS_RANGE.high) - Math.max(...prices))).toBeLessThanOrEqual(5_000)
  })

  it("prints the figures a person would round to, including the half-way one", () => {
    // 1,095,000 is 1.0949999… in binary; toFixed(2) alone would print $1.09M.
    expect(DEMO_COMPS_RANGE).toEqual({ low: "$1.10M", high: "$1.27M", median: "$1.18M" })
  })
})
