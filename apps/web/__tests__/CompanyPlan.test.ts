import { agentPlanCounts, agentPlanLimits, historyDate, holderSentence, planHeadline, seatPeriodLine, seatRows, type AgentPlan, type SeatPeriod } from "@/lib/company-plan"
import type { Rep } from "@/lib/company-people"

const rep = (over: Partial<Rep> = {}): Rep => ({
  id: "r1", name: "Ben Carter", email: "ben@x.test", status: "active",
  agent_count: 2, reports_this_month: 3, last_active: null, idle: false, holds_seat: true, ...over,
})
const seats = (total: number, held: number) => ({ total, held, open: total - held, pending: 0, idle: 0 })
const plan: AgentPlan = { plan_name: "Sponsored Free", market_reports: 3, schedules: 1, property_reports: 1 }

describe("one row per seat", () => {
  it("numbers the held seats by name, then the open ones", () => {
    const rows = seatRows(seats(4, 2), [rep({ id: "z", name: "Zoe" }), rep({ id: "a", name: "Ana" }), rep({ id: "x", name: "Xan", holds_seat: false })])
    expect(rows.map((r) => [r.label, r.kind === "held" ? r.rep.name : "open"])).toEqual([
      ["Seat 1", "Ana"], ["Seat 2", "Zoe"], ["Seat 3", "open"], ["Seat 4", "open"],
    ])
  })

  it("a rep without a seat is not on the seat list", () => {
    expect(seatRows(seats(1, 0), [rep({ holds_seat: false })]).map((r) => r.kind)).toEqual(["open"])
  })

  it("off seats there is no count: no numbers, no open rows", () => {
    const rows = seatRows(null, [rep()])
    expect(rows).toHaveLength(1)
    expect(rows[0].label).toBe("")
  })
})

describe("the headline is the company's own count", () => {
  it("on seats", () => expect(planHeadline(seats(6, 5), 5)).toBe("6 rep seats, 5 in use."))
  it("one seat", () => expect(planHeadline(seats(1, 1), 1)).toBe("1 rep seat, 1 in use."))
  it("off seats says there's no cap rather than inventing one", () => {
    expect(planHeadline(null, 3)).toBe("No seat count is set for your company, so there's no cap on reps. 3 reps right now.")
  })
})

describe("a held seat's sentence", () => {
  it("pending holds the seat", () => expect(holderSentence(rep({ status: "pending" })).tone).toBe("off"))
  it("idle is a warning and says why", () => expect(holderSentence(rep({ idle: true }))).toEqual({ tone: "warn", text: "2 agents · no reports from their agents in 30 days" }))
  it("otherwise the agents", () => expect(holderSentence(rep({ agent_count: 1 }))).toEqual({ tone: "good", text: "1 agent" }))
})

describe("the agents' plan is what the table says", () => {
  it("lists every limit given", () => {
    expect(agentPlanLimits(plan)).toBe("3 market reports a month, 1 property report a month and 1 schedule that sends on its own")
  })
  it("follows the table when it changes", () => {
    expect(agentPlanLimits({ ...plan, market_reports: 10, schedules: 2, property_reports: null })).toBe("10 market reports a month and 2 schedules that send on their own")
  })
  it("says nothing when the table gives nothing", () => {
    expect(agentPlanLimits({ ...plan, market_reports: null, schedules: null, property_reports: null })).toBe("")
    expect(agentPlanLimits(null)).toBe("")
  })
  it("counts who has upgraded from the agents' own plans", () => {
    expect(agentPlanCounts([{ plan: "sponsored_free" }, { plan: "sponsored_free" }, { plan: "pro" }], plan)).toBe("Of your 3 agents, 2 are on Sponsored Free and 1 has upgraded.")
    expect(agentPlanCounts([], plan)).toBe("Your reps haven't invited any agents yet.")
  })
})

describe("seat history as sentences", () => {
  const h = (over: Partial<SeatPeriod>): SeatPeriod => ({
    rep_id: "r", rep_name: "Ben", started_at: "2026-10-01T00:00:00Z", ended_at: "2026-10-20T00:00:00Z",
    ended_reason: null, successor_rep_id: null, successor_name: null, agents_moved: null, ...over,
  })
  it("a reassignment names who it went to and what moved", () => {
    expect(seatPeriodLine(h({ ended_reason: "reassigned", successor_name: "Ana", agents_moved: 4 }))).toEqual({ text: "Ben's seat went to Ana · 4 agents moved with it", at: "2026-10-20T00:00:00Z" })
  })
  it("a cancelled invite opened the seat", () => {
    expect(seatPeriodLine(h({ ended_reason: "invite_cancelled" })).text).toBe("Ben's invite was cancelled · the seat opened")
  })
  it("an open period is dated from its start", () => {
    expect(seatPeriodLine(h({ ended_at: null }))).toEqual({ text: "Ben was given a seat", at: "2026-10-01T00:00:00Z" })
  })
})

describe("history dates carry the year when it isn't this one", () => {
  it("an earlier year", () => expect(historyDate("2025-01-01T12:00:00Z", new Date("2026-10-29T12:00:00Z"))).toBe("Jan 1, 2025"))
  it("no date, no label", () => expect(historyDate(null)).toBe(""))
})
