import { aheadLabel, byWho, pdfFor, reportState, reportWhat, scheduleNext, scheduleWhen, who, zoneLabel } from "@/lib/company-activity"

describe("who made it, and where they sit", () => {
  it("a rep is a rep", () => {
    expect(who({ user_name: "Ben Carter", account_name: "Ben's office", user_type: "Rep", rep_name: "Ben's office" })).toEqual({ name: "Ben Carter", sub: "Rep" })
  })
  it("an agent is their rep's", () => {
    expect(who({ user_name: "Priya Shah", account_name: "x", user_type: "Agent", rep_name: "Ben Carter" })).toEqual({ name: "Priya Shah", sub: "Ben Carter's agent" })
  })
  it("no person's name falls back to the account's", () => {
    expect(who({ user_name: "", account_name: "Seat Rep A1", user_type: "Rep", rep_name: "Seat Rep A1" }).name).toBe("Seat Rep A1")
  })
})

describe("a report's state is the API's status, not a guess (D-317)", () => {
  it("completed is made", () => expect(reportState("completed")).toEqual({ tone: "good", text: "Made" }))
  it("failed didn't finish", () => expect(reportState("failed").text).toBe("Didn't finish"))
  it("queued and processing are being made", () => {
    expect(reportState("queued").text).toBe("Being made")
    expect(reportState("processing").text).toBe("Being made")
  })
  it("a PDF only for a finished report that has one", () => {
    expect(pdfFor({ status: "completed", pdf_url: "https://x/r.pdf" })).toBe("https://x/r.pdf")
    expect(pdfFor({ status: "failed", pdf_url: "https://x/r.pdf" })).toBeNull()
    expect(pdfFor({ status: "completed", pdf_url: null })).toBeNull()
  })
  it("the API's 'Unknown' city is left out", () => {
    expect(reportWhat({ city: "Unknown", report_type: "market_snapshot" })).toBe("market snapshot")
    expect(reportWhat({ city: "Irvine", report_type: "closed" })).toBe("Irvine · closed sales")
  })
})

describe("when a schedule sends", () => {
  const base = { send_hour: 8, send_minute: 0, timezone: "America/Los_Angeles", monthly_dom: null, weekly_dow: null }
  const oct = new Date("2026-10-29T12:00:00Z")
  it("weekly_dow is 0 = Sunday", () => {
    expect(scheduleWhen({ ...base, cadence: "weekly", weekly_dow: 1 }, oct)).toBe("Every Monday at 8:00 AM PDT")
    expect(scheduleWhen({ ...base, cadence: "weekly", weekly_dow: 0 }, oct)).toBe("Every Sunday at 8:00 AM PDT")
  })
  it("monthly by date", () => {
    expect(scheduleWhen({ ...base, cadence: "monthly", monthly_dom: 22, send_hour: 15, send_minute: 5 }, oct)).toBe("The 22nd of each month at 3:05 PM PDT")
  })
  it("a day the row doesn't carry is not guessed", () => {
    expect(scheduleWhen({ ...base, cadence: "weekly" }, oct)).toBe("Weekly at 8:00 AM PDT")
  })
  it("an unknown zone is shown as given", () => expect(zoneLabel("Not/AZone")).toBe("Not/AZone"))
  it("paused is paused, whatever the next date says", () => {
    expect(scheduleNext({ active: false, next_run_at: "2026-11-02T08:00:00Z" })).toEqual({ tone: "warn", text: "Paused" })
  })
  it("the next send looks ahead", () => {
    const now = new Date("2026-10-29T12:00:00")
    expect(aheadLabel("2026-10-30T12:00:00", now)).toBe("tomorrow")
    expect(aheadLabel("2026-11-02T12:00:00", now)).toBe("Monday")
    expect(aheadLabel("2026-11-20T12:00:00", now)).toBe("Nov 20")
    expect(scheduleNext({ active: true, next_run_at: "2026-10-30T12:00:00" }, now).text).toBe("Next send tomorrow")
  })
})

describe("the who filter", () => {
  const rows = [{ user_type: "Rep" as const }, { user_type: "Agent" as const }, { user_type: "Agent" as const }]
  it("narrows", () => {
    expect(byWho(rows, "Agent")).toHaveLength(2)
    expect(byWho(rows, "Rep")).toHaveLength(1)
    expect(byWho(rows, "everyone")).toHaveLength(3)
  })
})
