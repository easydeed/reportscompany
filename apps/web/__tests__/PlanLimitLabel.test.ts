/**
 * D-293 — the admin plan picker typed its limits ("Free (5 reports/month)",
 * "Trial (10 reports/month)") from the legacy column; the gate enforces 3.
 * The label is now built from `plans.market_reports_limit`.
 */
import fs from "fs"
import path from "path"
import { planLimitLabel } from "@/lib/plan-limit-label"

const PAGE = fs.readFileSync(
  path.join(__dirname, "../app/admin/(dashboard)/accounts/[id]/page.tsx"), "utf8")

describe("admin plan picker", () => {
  it("labels a limit from the number it is given", () => {
    expect(planLimitLabel(3)).toBe("3 market reports/month")
    expect(planLimitLabel(5000)).toBe("5,000 market reports/month")
    expect(planLimitLabel(99999)).toBe("unlimited market reports")
    expect(planLimitLabel(null)).toBe("no market-report limit set")
  })

  it("types no plan number into the page", () => {
    expect(PAGE).not.toMatch(/\d[\d,]*\s+reports\/month/)
    expect(PAGE).toMatch(/planLimitLabel\(p\.market_reports_limit\)/)
  })

  it("reads the enforced limit, not the legacy column", () => {
    expect(PAGE).not.toMatch(/plan\.monthly_report_limit\b/)
  })
})
