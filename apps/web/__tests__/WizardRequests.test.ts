/**
 * LR-024 (D-382, D-330, D-329): what the report wizard does with each answer.
 *
 * Red on main: the status poll ran every 3 s forever, ignoring non-OK answers
 * and exceptions; a failed schedule create showed nothing; and the limit card
 * read used/limit from the top level while the API puts them in `detail`.
 */
import {
  IdempotencyKeys, MAX_STATUS_ERRORS, PROBLEMS, SLOW_AFTER_MS, STATUS_INTERVAL_MS, UNKNOWN_OUTCOME,
  classifySubmit, limitMessage, watchReport,
} from "@/lib/wizard-requests"

const json = (status: number, body: unknown) =>
  ({ status, ok: status >= 200 && status < 300, json: async () => body }) as unknown as Response

describe("a submit's answer", () => {
  it("a create is created", async () => {
    expect(await classifySubmit(json(202, { report_id: "r1", status: "pending" }), "market_reports"))
      .toEqual({ kind: "created", body: { report_id: "r1", status: "pending" } })
  })

  it("no answer at all is offline", async () => {
    expect(await classifySubmit(null, "schedules")).toEqual({ kind: "offline" })
  })

  it.each([500, 502, 503, 504])("a %i is a server error", async (code) => {
    expect((await classifySubmit(json(code, {}), "market_reports")).kind).toBe("server_error")
  })

  it("a 401 is an expired session, not an invalid request", async () => {
    expect((await classifySubmit(json(401, { detail: "Unauthorized" }), "schedules")).kind).toBe("session_expired")
  })

  it("a 403 email-not-verified keeps its own remedy", async () => {
    const out = await classifySubmit(json(403, { detail: { error: "email_not_verified", action: "send", message: "Confirm first." } }), "market_reports")
    expect(out.kind).toBe("verification")
  })

  it("D-329: a 429 reads its numbers from detail, where the API puts them", async () => {
    const body = { detail: { error: "schedule_limit_reached", product: "schedules", used: 3, limit: 3, message: "x" } }
    expect(await classifySubmit(json(429, body), "schedules"))
      .toEqual({ kind: "limit", title: "Schedule limit reached", detail: "You've used 3 of 3 schedules." })
    expect(limitMessage({ detail: { product: "market_reports", used: 10, limit: 10 } }, "market_reports").detail)
      .toBe("You've used 10 of 10 market reports this month.")
    expect(limitMessage({}, "schedules").detail).toBe("You've reached your schedule limit.")
  })

  it("a validation error shows the server's own words", async () => {
    expect(await classifySubmit(json(422, { detail: "'Atlantis' is not a recognized CRMLS city." }), "market_reports"))
      .toEqual({ kind: "invalid", message: "'Atlantis' is not a recognized CRMLS city." })
    const fastapi = { detail: [{ loc: ["body", "name"], msg: "Field required" }] }
    expect(await classifySubmit(json(422, fastapi), "schedules")).toEqual({ kind: "invalid", message: "Field required" })
  })

  it("only outcomes that may have landed keep the key", () => {
    expect([...UNKNOWN_OUTCOME].sort()).toEqual(["offline", "server_error", "session_expired"])
  })
})

describe("one Idempotency-Key per payload", () => {
  const counter = () => { let n = 0; return () => `k${++n}` }

  it("a retry of the same payload reuses its key", () => {
    const keys = new IdempotencyKeys(counter())
    expect(keys.keyFor("a")).toBe("k1")
    expect(keys.keyFor("a")).toBe("k1")
  })

  it("an edit gets a new key, and going back to the old payload does not revive the old one", () => {
    const keys = new IdempotencyKeys(counter())
    keys.keyFor("a")
    expect(keys.keyFor("b")).toBe("k2")
    expect(keys.keyFor("a")).toBe("k3")
  })

  it("after a success the same payload is a new request", () => {
    const keys = new IdempotencyKeys(counter())
    keys.keyFor("a")
    keys.release()
    expect(keys.keyFor("a")).toBe("k2")
  })

  it("the default key is a random UUID", () => {
    expect(new IdempotencyKeys().keyFor("a")).toMatch(/^[0-9a-f-]{32,36}$/)
  })
})

describe("the report-status wait is bounded (D-382)", () => {
  beforeEach(() => jest.useFakeTimers())
  afterEach(() => jest.useRealTimers())

  function server(answers: Array<Response | Error | "hang">) {
    const calls: string[] = []
    const fetchFn = async (url: string) => {
      calls.push(url)
      const next = answers.length > 1 ? answers.shift()! : answers[0]
      if (next === "hang") return new Promise<Response>(() => {})
      if (next instanceof Error) throw next
      return next
    }
    return { calls, fetchFn }
  }
  function track<T>(p: Promise<T>) {
    const out: { done: boolean; value?: T } = { done: false }
    p.then((v) => { out.done = true; out.value = v })
    return out
  }

  it("ends ready with the PDF link", async () => {
    const { fetchFn } = server([json(200, { status: "pending" }), json(200, { status: "completed", pdf_url: "u" })])
    const run = track(watchReport("r1", { fetchFn }))
    await jest.advanceTimersByTimeAsync(2 * STATUS_INTERVAL_MS)
    expect(run.value).toEqual({ kind: "complete", pdfUrl: "u" })
  })

  it("ends on a terminal failure", async () => {
    const { fetchFn } = server([json(200, { status: "failed" })])
    const run = track(watchReport("r1", { fetchFn }))
    await jest.advanceTimersByTimeAsync(STATUS_INTERVAL_MS)
    expect(run.value).toEqual({ kind: "failed" })
  })

  it("a slow legitimate job ends as slow at the deadline, and stops asking", async () => {
    const { calls, fetchFn } = server([json(200, { status: "processing" })])
    const run = track(watchReport("r1", { fetchFn }))
    await jest.advanceTimersByTimeAsync(SLOW_AFTER_MS - 1)
    expect(run.done).toBe(false)
    await jest.advanceTimersByTimeAsync(1)
    expect(run.value).toEqual({ kind: "slow" })
    const made = calls.length
    await jest.advanceTimersByTimeAsync(10 * STATUS_INTERVAL_MS)
    expect(calls).toHaveLength(made)
  })

  it("a check that never answers still ends at the deadline", async () => {
    const { fetchFn } = server(["hang"])
    const run = track(watchReport("r1", { fetchFn }))
    await jest.advanceTimersByTimeAsync(SLOW_AFTER_MS)
    expect(run.value).toEqual({ kind: "slow" })
  })

  it.each([
    ["network errors", new Error("offline")],
    ["5xx answers", json(503, {})],
  ])("%s in a row end as can't-check", async (_, failure) => {
    const { calls, fetchFn } = server([failure])
    const run = track(watchReport("r1", { fetchFn }))
    await jest.advanceTimersByTimeAsync(MAX_STATUS_ERRORS * STATUS_INTERVAL_MS)
    expect(run.value).toEqual({ kind: "unreachable" })
    expect(calls).toHaveLength(MAX_STATUS_ERRORS)
  })

  it("a good answer resets the count: errors must be consecutive", async () => {
    const pending = json(200, { status: "pending" })
    const { fetchFn } = server([new Error("x"), new Error("x"), pending, new Error("x"), new Error("x"), json(200, { status: "completed" })])
    const run = track(watchReport("r1", { fetchFn }))
    await jest.advanceTimersByTimeAsync(6 * STATUS_INTERVAL_MS)
    expect(run.value).toEqual({ kind: "complete", pdfUrl: null })
  })

  it("a 401 ends as an expired session, a 404 as not found", async () => {
    for (const [code, kind] of [[401, "session_expired"], [404, "not_found"]] as const) {
      const { fetchFn } = server([json(code, {})])
      const run = track(watchReport("r1", { fetchFn }))
      await jest.advanceTimersByTimeAsync(STATUS_INTERVAL_MS)
      expect(run.value).toEqual({ kind })
    }
  })

  it("leaving the page (or a retry) stops it at once and cancels the check in flight", async () => {
    const signals: AbortSignal[] = []
    const fetchFn = (_: string, init?: RequestInit) => {
      if (init?.signal) signals.push(init.signal)
      return new Promise<Response>(() => {})
    }
    const page = new AbortController()
    const run = track(watchReport("r1", { fetchFn, signal: page.signal }))
    await jest.advanceTimersByTimeAsync(STATUS_INTERVAL_MS)
    page.abort()
    await jest.advanceTimersByTimeAsync(0)
    expect(run.done).toBe(true)
    expect(run.value).toBeNull()
    expect(signals[0].aborted).toBe(true)
  })
})

describe("every problem says what to do", () => {
  it("each has a title and at least one action; only refusals send the person back to edit alone", () => {
    for (const [kind, p] of Object.entries(PROBLEMS)) {
      expect(p.title).toBeTruthy()
      expect(p.actions.length).toBeGreaterThan(0)
      if (kind !== "invalid" && kind !== "not_found") expect(p.actions.length).toBeGreaterThan(1)
    }
    expect(PROBLEMS.slow.actions).toContain("keep_waiting")
    expect(PROBLEMS.unreachable.actions).toContain("check_again")
    expect(PROBLEMS.session_expired.actions).toEqual(["sign_in", "retry_submit"])
  })
})
