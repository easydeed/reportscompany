import { agentSentence, bySource, cameFrom, leadLine, leadsHeadline, madeLine, reportsOfPlan } from "@/lib/rep-book"

describe("where a lead came from", () => {
  it("the property page covers the QR code and the link alike (D-325)", () => expect(cameFrom("property_page")).toBe("from their property report page"))
  it("the home-value page", () => expect(cameFrom("home_value_page")).toBe("from their home-value page"))
  it("anything else is not guessed", () => expect(cameFrom("other")).toBe("from somewhere else"))
  it("a feed line names the agent, never the homeowner", () => {
    expect(leadLine({ agent_name: "Priya Shah", came_from: "home_value_page" })).toBe("Priya Shah got a homeowner lead from their home-value page")
  })
})

describe("the leads headline", () => {
  const oct = new Date("2026-10-29T12:00:00")
  it("this month, with last month's", () => expect(leadsHeadline({ this_month: 3, last_month: 1 }, "Your agents", oct)).toBe("Your agents brought in 3 homeowner leads this month — 1 in September."))
  it("one", () => expect(leadsHeadline({ this_month: 1, last_month: 0 }, "Your agents", oct)).toBe("Your agents brought in 1 homeowner lead this month."))
  it("none yet", () => expect(leadsHeadline({ this_month: 0, last_month: 2 }, "Your agents", oct)).toBe("No homeowner leads from your agents yet this month — 2 in September."))
})

describe("an agent's standing", () => {
  it("pending", () => expect(agentSentence({ status: "pending", last_report_at: null, joined_at: null }).text).toBe("Invited, hasn't joined yet"))
  it("switched off says what that means", () => expect(agentSentence({ status: "deactivated", last_report_at: null, joined_at: null }).text).toContain("can't sign in"))
  it("joined, nothing made", () => expect(agentSentence({ status: "active", last_report_at: null, joined_at: "2026-10-01T00:00:00Z" }).tone).toBe("warn"))
  it("quiet past a month", () => expect(agentSentence({ status: "active", last_report_at: new Date(Date.now() - 40 * 86_400_000).toISOString(), joined_at: null }).tone).toBe("warn"))
  it("active", () => expect(agentSentence({ status: "active", last_report_at: new Date().toISOString(), joined_at: null }).text).toBe("Active — last report today"))
})

describe("reports against the plan, read from the plan", () => {
  it("under", () => expect(reportsOfPlan({ market_reports_used: 2, market_reports_limit: 3, plan_name: "Sponsored Free" })).toBe("of 3 on the Sponsored Free plan"))
  it("over, inside the grace, says so instead of '4 of 3'", () => expect(reportsOfPlan({ market_reports_used: 4, market_reports_limit: 3, plan_name: "Sponsored Free" })).toBe("1 over the Sponsored Free plan's 3"))
  it("unlimited names no number", () => expect(reportsOfPlan({ market_reports_used: 40, market_reports_limit: 99999, plan_name: "Pro" })).toBe("on the Pro plan"))
})

describe("report lines and filters", () => {
  it("made, with the city", () => expect(madeLine({ report_type: "market_snapshot", city: "Irvine", is_scheduled: false })).toBe("Made a market snapshot for Irvine"))
  it("their schedule, 'an', no unknown city", () => expect(madeLine({ report_type: "inventory", city: "Unknown", is_scheduled: true })).toBe("Their schedule made an inventory"))
  it("agents' / mine / everything", () => {
    const rows = [{ source: "You" as const }, { source: "Agent" as const }, { source: "Agent" as const }]
    expect(bySource(rows, "agents")).toHaveLength(2)
    expect(bySource(rows, "mine")).toHaveLength(1)
    expect(bySource(rows, "all")).toHaveLength(3)
  })
})
