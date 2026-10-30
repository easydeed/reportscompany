import { agentSentence, agentsByRep, repActions, seatLine, splitName, type Agent, type Rep } from "@/lib/company-people"

const rep = (over: Partial<Rep> = {}): Rep => ({
  id: "r1", name: "Ben Carter", email: "ben@x.test", status: "active",
  agent_count: 2, reports_this_month: 3, last_active: null, idle: false, holds_seat: true, ...over,
})

describe("the actions a rep row offers are the ones the server accepts", () => {
  it("a joined rep holding a seat can be replaced, not cancelled", () => {
    expect(repActions(rep())).toEqual(["replace"])
  })

  it("a pending rep with no agents can be resent or cancelled", () => {
    expect(repActions(rep({ status: "pending", agent_count: 0 }))).toEqual(["resend", "cancel"])
  })

  it("a pending rep with agents is replaced, because the server refuses to cancel one", () => {
    expect(repActions(rep({ status: "pending", agent_count: 1 }))).toEqual(["resend", "replace"])
  })

  it("a rep with no seat has no seat action", () => {
    expect(repActions(rep({ holds_seat: false }))).toEqual([])
    expect(repActions(rep({ status: "deactivated", holds_seat: false }))).toEqual([])
  })
})

describe("agents join their rep by id (D-276)", () => {
  it("two reps with the same name keep their own agents", () => {
    const a = (agent_id: string, rep_id: string): Agent => ({
      agent_id, agent_name: agent_id, email: "", rep_id, rep_name: "Ben Carter",
      status: "active", plan: "sponsored_free", reports_this_month: 0, last_activity: null,
    })
    const m = agentsByRep([a("x", "r1"), a("y", "r2"), a("z", "r1")])
    expect(m.r1.map((x) => x.agent_id)).toEqual(["x", "z"])
    expect(m.r2.map((x) => x.agent_id)).toEqual(["y"])
  })
})

describe("the words on the page", () => {
  it("names the seats only when the company is on seats", () => {
    expect(seatLine(null)).toBeNull()
    expect(seatLine({ total: 25, held: 8, open: 17, pending: 1, idle: 0 }))
      .toBe("8 of 25 rep seats in use · 17 open · 1 invited, not joined")
  })

  it("says an agent made a report, never that it was sent", () => {
    const text = agentSentence({ status: "active", last_activity: new Date().toISOString() })
    expect(text).toBe("Last report today")
    expect(agentSentence({ status: "pending", last_activity: null })).toBe("Hasn't joined yet")
  })

  it("takes the name the admin typed and guesses nothing from the address", () => {
    expect(splitName("  Maria  de la Cruz ")).toEqual({ name: "Maria de la Cruz", first_name: "Maria", last_name: "de la Cruz" })
    expect(splitName("Cher")).toEqual({ name: "Cher", first_name: "Cher", last_name: "" })
    expect(splitName("   ")).toBeNull()
  })
})
