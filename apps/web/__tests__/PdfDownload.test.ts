/**
 * LR-022 (D-380): the PDF button stops, and says why.
 *
 * Red on main: the viewer polled `GET …/pdf` every second with no deadline
 * and no way to stop, so a failed or missing PDF spun forever.
 *
 * Codex, #283: the first fix checked its clock only between requests, so a
 * request or a response body that never arrived left "Preparing your PDF"
 * up forever, deadline or not, and leaving the page could not cancel it.
 * These run the real helper on Jest's fake timers with a fake server,
 * including requests that never answer.
 */
import { DEADLINE_MS, PDF_COPY, POLL_MS, requestPdf } from "@/lib/pdf-download"

type Answer = Record<string, unknown> | Error | "hang" | "hang-body"

const never = <T,>() => new Promise<T>(() => {})

function server(answers: Answer[]) {
  const calls: string[] = []
  const signals: AbortSignal[] = []
  const fetchFn = async (url: string, init?: RequestInit) => {
    calls.push(`${init?.method || "GET"} ${url}`)
    if (init?.signal) signals.push(init.signal)
    const next = answers.length > 1 ? answers.shift()! : answers[0]
    if (next === "hang") return never<Response>()
    if (next === "hang-body") return { json: () => never() } as unknown as Response
    if (next instanceof Error) throw next
    return { json: async () => next } as unknown as Response
  }
  return { calls, signals, fetchFn }
}

/** Run the helper while advancing fake time; report whether it had settled at each step. */
function track<T>(p: Promise<T>) {
  const out: { done: boolean; value?: T } = { done: false }
  p.then((v) => { out.done = true; out.value = v })
  return out
}

beforeEach(() => jest.useFakeTimers())
afterEach(() => jest.useRealTimers())

describe("the PDF request", () => {
  it("opens an existing PDF straight away, with one request", async () => {
    const { calls, fetchFn } = server([{ status: "ready", pdf_url: "https://r2.test/a.pdf?sig" }])
    expect(await requestPdf("r1", { fetchFn })).toEqual({ status: "ready", url: "https://r2.test/a.pdf?sig" })
    expect(calls).toEqual(["POST /api/proxy/v1/r/r1/pdf"])
  })

  it("polls a generating PDF until it is ready", async () => {
    const { calls, fetchFn } = server([{ status: "generating" }, { status: "generating" }, { status: "ready", pdf_url: "u" }])
    const run = track(requestPdf("r1", { fetchFn }))
    await jest.advanceTimersByTimeAsync(2 * POLL_MS)
    expect(run.value).toEqual({ status: "ready", url: "u" })
    expect(calls.filter((c) => c.startsWith("GET"))).toHaveLength(2)
  })

  it("stops at the deadline with an actionable message", async () => {
    const { calls, fetchFn } = server([{ status: "generating" }])
    const run = track(requestPdf("r1", { fetchFn }))
    await jest.advanceTimersByTimeAsync(DEADLINE_MS)
    expect(run.value).toEqual({ status: "expired", message: PDF_COPY.expired })
    expect(calls.length).toBeLessThanOrEqual(1 + DEADLINE_MS / POLL_MS)
  })

  it("shows the server's message for a failure, the rate limit or an undelivered report", async () => {
    for (const body of [
      { status: "failed", message: "We couldn't prepare your PDF." },
      { status: "rate_limited", message: "Too many PDF requests." },
      { status: "unavailable", message: "The PDF will be available once delivered." },
    ]) {
      const { fetchFn } = server([body])
      expect(await requestPdf("r1", { fetchFn })).toEqual({ status: "failed", message: body.message })
    }
  })

  it("treats a lost job (missing) as a failure the person can retry", async () => {
    const { fetchFn } = server([{ status: "generating" }, { status: "missing", message: "" }])
    const run = track(requestPdf("r1", { fetchFn }))
    await jest.advanceTimersByTimeAsync(POLL_MS)
    expect(run.value).toEqual({ status: "failed", message: PDF_COPY.failed })
  })

  it("says so when the server cannot be reached", async () => {
    const { fetchFn } = server([new Error("network")])
    expect(await requestPdf("r1", { fetchFn })).toEqual({ status: "failed", message: PDF_COPY.offline })
  })

  it("a retry is a fresh request", async () => {
    const { calls, fetchFn } = server([{ status: "failed", message: "x" }, { status: "ready", pdf_url: "u" }])
    expect((await requestPdf("r1", { fetchFn }))?.status).toBe("failed")
    expect((await requestPdf("r1", { fetchFn }))?.status).toBe("ready")
    expect(calls.filter((c) => c.startsWith("POST"))).toHaveLength(2)
  })
})

describe("the deadline bounds requests that never answer (Codex, #283)", () => {
  it.each([
    ["the first request hangs", ["hang"] as Answer[]],
    ["the first response body hangs", ["hang-body"] as Answer[]],
    ["a status poll hangs", [{ status: "generating" }, "hang"] as Answer[]],
    ["a status poll's body hangs", [{ status: "generating" }, "hang-body"] as Answer[]],
  ])("%s: it ends at the deadline and cancels the request", async (_, answers) => {
    const { signals, fetchFn } = server(answers)
    const run = track(requestPdf("r1", { fetchFn }))
    await jest.advanceTimersByTimeAsync(DEADLINE_MS - 1)
    expect(run.done).toBe(false)
    await jest.advanceTimersByTimeAsync(1)
    expect(run.value).toEqual({ status: "expired", message: PDF_COPY.expired })
    expect(signals.at(-1)?.aborted).toBe(true)
  })
})

describe("leaving the page stops it (Codex, #283)", () => {
  it("cancels a request in flight and settles at once", async () => {
    const { signals, fetchFn } = server(["hang"])
    const page = new AbortController()
    const run = track(requestPdf("r1", { fetchFn, signal: page.signal }))
    await jest.advanceTimersByTimeAsync(5_000)
    expect(run.done).toBe(false)
    page.abort()
    await jest.advanceTimersByTimeAsync(0)
    expect(run.done).toBe(true)
    expect(run.value).toBeNull()
    expect(signals[0].aborted).toBe(true)
  })

  it("stops polling between requests", async () => {
    const { calls, fetchFn } = server([{ status: "generating" }])
    const page = new AbortController()
    const run = track(requestPdf("r1", { fetchFn, signal: page.signal }))
    await jest.advanceTimersByTimeAsync(2 * POLL_MS)
    const made = calls.length
    page.abort()
    await jest.advanceTimersByTimeAsync(DEADLINE_MS)
    expect(run.value).toBeNull()
    expect(calls).toHaveLength(made)
  })

  it("a page already gone asks nothing", async () => {
    const { calls, fetchFn } = server([{ status: "ready", pdf_url: "u" }])
    const page = new AbortController()
    page.abort()
    expect(await requestPdf("r1", { fetchFn, signal: page.signal })).toBeNull()
    expect(calls).toEqual([])
  })
})
