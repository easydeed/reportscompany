/**
 * LR-024 (D-382, D-330, D-329): what the report wizard does with each answer.
 *
 * Red on main: the status poll ran every 3 s forever, ignoring non-OK answers
 * and exceptions; a failed schedule create showed nothing; and the limit card
 * read used/limit from the top level while the API puts them in `detail`.
 */
import {
  IdempotencyKeys, MAX_STATUS_ERRORS, PROBLEMS, SLOW_AFTER_MS, STATUS_INTERVAL_MS,
  classifySubmit, limitMessage, sendCreate, watchReport,
} from "@/lib/wizard-requests"

const json = (status: number, body: unknown) =>
  ({ status, ok: status >= 200 && status < 300, json: async () => body }) as unknown as Response
/** A response whose body never arrives whole: json() throws, as on a cut connection. */
const unreadable = (status: number) =>
  ({ status, ok: status >= 200 && status < 300, json: async () => { throw new SyntaxError("Unexpected end of JSON input") } }) as unknown as Response
const R1 = "6f1c2b9e-1d2a-4c3b-9e8f-0a1b2c3d4e5f"
const S1 = "0b5d7a2c-3e4f-4a6b-8c9d-1e2f3a4b5c6d"

describe("a submit's answer", () => {
  it("a create is created, with the id it made", async () => {
    expect(await classifySubmit(json(202, { report_id: R1, status: "pending" }), "market_reports"))
      .toEqual({ kind: "created", resourceId: R1 })
    expect(await classifySubmit(json(201, { id: S1, name: "Weekly" }), "schedules"))
      .toEqual({ kind: "created", resourceId: S1 })
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

describe("rev 2/3: a safe retry is promised only when it is safe", () => {
  const DAY = 24 * 60 * 60 * 1000
  function keysAt(start: number) {
    let now = start
    const keys = new IdempotencyKeys(() => "k", () => now)
    return { keys, set: (t: number) => { now = t } }
  }

  it.each([
    ["just sent", 0, true],
    ["5 days 23 hours later", 6 * DAY - 60 * 60 * 1000, true],
    ["exactly 6 days later", 6 * DAY, true],
    ["6 days and a second later", 6 * DAY + 1000, false],
    ["the clock moved back", -1000, false],
    ["a tab asleep for 25 days", 25 * DAY, false],
  ])("%s: %s", (_, age, safe) => {
    const { keys, set } = keysAt(1_000_000_000_000)
    keys.keyFor("payload")
    set(1_000_000_000_000 + (age as number))
    expect(keys.retryIsSafe()).toBe(safe)
  })

  it("never before any key was sent", () => {
    expect(new IdempotencyKeys().retryIsSafe()).toBe(false)
  })

  it("the age is the key's FIRST send: retrying does not reset it", () => {
    const { keys, set } = keysAt(0)
    keys.keyFor("payload")
    set(5 * DAY)
    keys.keyFor("payload")
    set(6 * DAY + 1000)
    expect(keys.retryIsSafe()).toBe(false)
  })

  it("rev 3: an API without the key contract (the proxy's 503) created nothing, and says so", async () => {
    expect(await classifySubmit(json(503, { error: "idempotent_create_unavailable" }), "market_reports"))
      .toEqual({ kind: "unavailable" })
    expect((await classifySubmit(json(503, { detail: "upstream" }), "market_reports")).kind).toBe("server_error")
    expect(PROBLEMS.unavailable.actions).toEqual(["edit", "retry_submit"])
    expect(PROBLEMS.unavailable.sub).toMatch(/Nothing was created/)
  })

  it("the server's 410s: an expired key and a deleted resource create nothing and say so", async () => {
    expect(await classifySubmit(json(410, { detail: { error: "idempotency_key_expired" } }), "market_reports"))
      .toEqual({ kind: "key_expired" })
    expect(await classifySubmit(json(410, { detail: { error: "idempotent_resource_gone", resource_id: "s1" } }), "schedules"))
      .toEqual({ kind: "gone" })
    expect((await classifySubmit(json(410, {}), "schedules")).kind).toBe("invalid")
  })

  it("can't-tell and gone offer the list and an explicit new request, never a blind retry", () => {
    for (const kind of ["unknown", "gone"] as const) {
      expect(PROBLEMS[kind].actions).toEqual(["go_list", "send_new"])
      expect(PROBLEMS[kind].actions).not.toContain("retry_submit")
    }
    expect(PROBLEMS.unknown.sub).not.toMatch(/won't create a second/)
  })
})

describe("an unavailable answer proves only that THIS attempt created nothing (Codex, design PASS)", () => {
  it("an earlier unknown answer for the key is remembered until the key is released", () => {
    const keys = new IdempotencyKeys(() => "k")
    keys.keyFor("payload")
    expect(keys.uncertain).toBe(false)
    keys.markUncertain()
    keys.keyFor("payload")
    expect(keys.uncertain).toBe(true)
    keys.release()
    keys.keyFor("payload")
    expect(keys.uncertain).toBe(false)
  })

  it("an edit (a new key) starts certain", () => {
    const keys = new IdempotencyKeys()
    keys.keyFor("a")
    keys.markUncertain()
    keys.keyFor("b")
    expect(keys.uncertain).toBe(false)
  })

  it("after an unknown answer the message never claims nothing was created", () => {
    expect(PROBLEMS.unavailable.sub).toMatch(/Nothing was created/)
    expect(PROBLEMS.unavailable_after_unknown.sub).not.toMatch(/Nothing was created/)
    expect(PROBLEMS.unavailable_after_unknown.sub).toMatch(/earlier attempt may have gone through/)
    expect(PROBLEMS.unavailable_after_unknown.actions).toEqual(["edit", "retry_submit"])
  })
})

describe("Codex code review: a 2xx the page can't read is an unknown outcome, not a create", () => {
  const PRODUCTS = [
    ["market_reports", { report_id: R1, status: "pending" }, R1, "/api/proxy/v1/reports"],
    ["schedules", { id: S1, name: "Weekly" }, S1, "/api/proxy/v1/schedules"],
  ] as const

  describe.each(PRODUCTS)("%s", (product, good, id) => {
    it.each([
      ["a body cut off mid-read", unreadable(product === "schedules" ? 201 : 202)],
      ["an empty body", unreadable(200)],
      ["a JSON null", json(202, null)],
      ["a JSON array", json(202, [id])],
      ["no id at all", json(202, { status: "pending" })],
      ["an id that isn't one", json(202, product === "schedules" ? { id: "undefined" } : { report_id: "undefined" })],
      ["a number for an id", json(202, product === "schedules" ? { id: 42 } : { report_id: 42 })],
      ["the other product's id field", json(202, product === "schedules" ? { report_id: id } : { schedule_id: id })],
    ])("%s", async (_, res) => {
      expect(await classifySubmit(res, product)).toEqual({ kind: "unreadable" })
    })

    it("a well-formed success is still created", async () => {
      expect(await classifySubmit(json(202, good), product)).toEqual({ kind: "created", resourceId: id })
    })
  })

  it("its problem promises a safe retry and offers it", () => {
    expect(PROBLEMS.unreadable.actions).toContain("retry_submit")
    expect(PROBLEMS.unreadable.sub).toMatch(/may have gone through/)
    expect(PROBLEMS.unreadable.sub).toMatch(/won't create a second one/)
  })

  describe.each(PRODUCTS)("%s: the retry is the same request", (product, good, id, url) => {
    const counter = () => { let n = 0; return () => `key-${++n}-abcdef` }

    it("an unreadable success keeps the key; the retry sends it again and gets the ORIGINAL id", async () => {
      const keys = new IdempotencyKeys(counter())
      const api = jest.fn()
        .mockResolvedValueOnce(unreadable(202))
        .mockResolvedValueOnce(json(202, good))
      const payload = JSON.stringify({ report_type: "market_snapshot" })

      const first = await sendCreate(keys, product, payload, api)
      expect(first).toEqual({ kind: "unreadable" })
      expect(keys.uncertain).toBe(true)
      expect(keys.retryIsSafe()).toBe(true)

      const retry = await sendCreate(keys, product, payload, api)
      expect(retry).toEqual({ kind: "created", resourceId: id })
      const sent = api.mock.calls.map(([to, init]) => [to, new Headers(init.headers).get("Idempotency-Key")])
      expect(sent).toEqual([[url, "key-1-abcdef"], [url, "key-1-abcdef"]])
    })

    it("a genuine success releases the key: the same payload sent again is a new request", async () => {
      const keys = new IdempotencyKeys(counter())
      const api = jest.fn().mockResolvedValue(json(202, good))
      const payload = JSON.stringify({ report_type: "market_snapshot" })
      await sendCreate(keys, product, payload, api)
      await sendCreate(keys, product, payload, api)
      const used = api.mock.calls.map(([, init]) => new Headers(init.headers).get("Idempotency-Key"))
      expect(used).toEqual(["key-1-abcdef", "key-2-abcdef"])
      expect(keys.uncertain).toBe(false)
    })

    it.each([
      ["no answer", () => Promise.reject(new TypeError("Failed to fetch"))],
      ["a 502", () => Promise.resolve(json(502, {}))],
      ["a 401", () => Promise.resolve(json(401, {}))],
      ["an unreadable 2xx", () => Promise.resolve(unreadable(202))],
    ])("%s marks the key uncertain and keeps it", async (_, answer) => {
      const keys = new IdempotencyKeys(counter())
      const api = jest.fn().mockImplementationOnce(answer).mockResolvedValueOnce(json(202, good))
      const payload = "{}"
      await sendCreate(keys, product, payload, api)
      expect(keys.uncertain).toBe(true)
      await sendCreate(keys, product, payload, api)
      const used = api.mock.calls.map(([, init]) => new Headers(init.headers).get("Idempotency-Key"))
      expect(used).toEqual(["key-1-abcdef", "key-1-abcdef"])
    })
  })

  it("a replayed report is watched by its original id, never /reports/undefined", async () => {
    const keys = new IdempotencyKeys(() => "key-only-abcdef")
    const api = jest.fn().mockResolvedValueOnce(unreadable(202)).mockResolvedValueOnce(json(202, { report_id: R1, status: "pending" }))
    expect((await sendCreate(keys, "market_reports", "{}", api)).kind).toBe("unreadable")
    const retry = await sendCreate(keys, "market_reports", "{}", api)
    if (retry.kind !== "created") throw new Error(`expected created, got ${retry.kind}`)
    const status = jest.fn().mockResolvedValue(json(200, { status: "completed", pdf_url: "https://x/r.pdf" }))
    expect(await watchReport(retry.resourceId, { fetchFn: status, intervalMs: 1 })).toEqual({ kind: "complete", pdfUrl: "https://x/r.pdf" })
    expect(status.mock.calls.map(([u]) => u)).toEqual([`/api/proxy/v1/reports/${R1}`])
  })
})
