/**
 * D-350, D-351 — the /r page says what the PDF says.
 *
 * It led with an "Estimated Value Range … Most likely: $554,130 · medium
 * confidence" the PDF never prints, and its market tab said "Homes Sold
 * (6 mo)" over "within 2 miles … in the last 12 months". The page now shows
 * the comps' range with the PDF's method line, and states only the window and
 * radius the comps cover.
 */
import fs from "fs"
import path from "path"
import { NO_RANGE, RANGE_HEADING, compsSentence, homesSoldLabel, rangeBasis } from "@/lib/consumer-report"

const VIEWER = fs.readFileSync(path.join(__dirname, "../components/mobile-report/MobileReportViewer.tsx"), "utf8")

describe("the consumer report's range", () => {
  it("is headed as the PDF heads it, with the method beside it", () => {
    expect(RANGE_HEADING).toBe("What the comparable sales support")
    expect(VIEWER).toMatch(/\{report\.comps_range\.method\}/)
    expect(rangeBasis({ low: 470000, high: 635000, count: 4, method: "x" })).toBe("Based on 4 closed sales")
    expect(rangeBasis({ low: 1, high: 1, count: 1, method: "x" })).toBe("Based on 1 closed sale")
  })

  it("has no point estimate and no confidence grade", () => {
    expect(VIEWER).not.toMatch(/Most likely|confidence|value_estimate|Estimated Value/)
  })

  it("says so when there is no range rather than printing $0 – $0", () => {
    expect(VIEWER).toMatch(/\{NO_RANGE\}/)
    expect(NO_RANGE).toMatch(/does not give a range/)
  })
})

describe("the consumer report's market tab", () => {
  const stats = { homes_sold: 4, window_months: 6, radius_miles: 0.6, median_price_per_sqft: 696 }

  it("states the window and radius the comps cover", () => {
    expect(homesSoldLabel(stats)).toBe("Homes sold (last 6 months)")
    expect(compsSentence(stats)).toBe(
      "Based on 4 closed comparable sales within 0.6 mi of your home in the last 6 months.")
  })

  it("leaves out what it does not know instead of guessing", () => {
    expect(homesSoldLabel({ homes_sold: 1 })).toBe("Homes sold")
    expect(compsSentence({ homes_sold: 1 })).toBe("Based on 1 closed comparable sale.")
  })

  it("prints no window or radius of its own", () => {
    expect(VIEWER).not.toMatch(/2 miles|12 months|6 mo\)/)
    expect(VIEWER).toMatch(/Median Price per Sqft/)
    expect(VIEWER).not.toMatch(/avg_price_per_sqft|total_sold_last_6mo/)
  })
})
