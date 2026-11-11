/**
 * LR-022 (D-380): the PDF button stops, and says why.
 *
 * Red on main: the viewer polled `GET …/pdf` every second with no deadline
 * and no way to stop, so a failed or missing PDF spun forever. These drive
 * the button's logic with a fake clock and a fake server.
 */
import fs from "fs"
import path from "path"
import { DEADLINE_MS, PDF_COPY, POLL_MS, requestPdf } from "@/lib/pdf-download"

const VIEWER = fs.readFileSync(path.join(__dirname, "../components/mobile-report/MobileReportViewer.tsx"), "utf8")

function server(answers: Array<Record<string, unknown> | Error>) {
  const calls: string[] = []
  const fetchFn = async (url: string, init?: RequestInit) => {
    calls.push(`${init?.method || "GET"} ${url}`)
    const next = answers.length > 1 ? answers.shift()! : answers[0]
    if (next instanceof Error) throw next
    return { json: async () => next } as unknown as Response
  }
  return { calls, fetchFn }
}

function clock() {
  let t = 0
  return { now: () => t, sleep: async (ms: number) => { t += ms } }
}

const live = () => false

describe("the PDF button", () => {
  it("opens an existing PDF straight away, with one request", async () => {
    const { calls, fetchFn } = server([{ status: "ready", pdf_url: "https://r2.test/a.pdf?sig" }])
    const out = await requestPdf("r1", { fetchFn, ...clock(), cancelled: live })
    expect(out).toEqual({ status: "ready", url: "https://r2.test/a.pdf?sig" })
    expect(calls).toEqual(["POST /api/proxy/v1/r/r1/pdf"])
  })

  it("polls a generating PDF until it is ready", async () => {
    const { calls, fetchFn } = server([
      { status: "generating" }, { status: "generating" }, { status: "ready", pdf_url: "u" },
    ])
    const out = await requestPdf("r1", { fetchFn, ...clock(), cancelled: live })
    expect(out?.status).toBe("ready")
    expect(calls.filter((c) => c.startsWith("GET"))).toHaveLength(2)
  })

  it("stops at the deadline with an actionable message", async () => {
    const { calls, fetchFn } = server([{ status: "generating" }])
    const out = await requestPdf("r1", { fetchFn, ...clock(), cancelled: live })
    expect(out).toEqual({ status: "expired", message: PDF_COPY.expired })
    expect(calls.length).toBeLessThanOrEqual(1 + DEADLINE_MS / POLL_MS)
  })

  it("shows the server's message for a failure, the rate limit or an undelivered report", async () => {
    for (const body of [
      { status: "failed", message: "We couldn't prepare your PDF." },
      { status: "rate_limited", message: "Too many PDF requests." },
      { status: "unavailable", message: "The PDF will be available once delivered." },
    ]) {
      const { fetchFn } = server([body])
      const out = await requestPdf("r1", { fetchFn, ...clock(), cancelled: live })
      expect(out).toEqual({ status: "failed", message: body.message })
    }
  })

  it("treats a lost job (missing) as a failure the person can retry", async () => {
    const { fetchFn } = server([{ status: "generating" }, { status: "missing", message: "" }])
    const out = await requestPdf("r1", { fetchFn, ...clock(), cancelled: live })
    expect(out).toEqual({ status: "failed", message: PDF_COPY.failed })
  })

  it("says so when the server cannot be reached", async () => {
    const { fetchFn } = server([new Error("network")])
    const out = await requestPdf("r1", { fetchFn, ...clock(), cancelled: live })
    expect(out).toEqual({ status: "failed", message: PDF_COPY.offline })
  })

  it("stops polling when the page goes away", async () => {
    const { calls, fetchFn } = server([{ status: "generating" }])
    let gone = false
    const c = clock()
    const sleep = async (ms: number) => { await c.sleep(ms); if (c.now() >= 3 * POLL_MS) gone = true }
    const out = await requestPdf("r1", { fetchFn, now: c.now, sleep, cancelled: () => gone })
    expect(out).toBeNull()
    expect(calls.length).toBe(3)
  })

  it("a retry is a fresh request", async () => {
    const { calls, fetchFn } = server([{ status: "failed", message: "x" }, { status: "ready", pdf_url: "u" }])
    expect((await requestPdf("r1", { fetchFn, ...clock(), cancelled: live }))?.status).toBe("failed")
    expect((await requestPdf("r1", { fetchFn, ...clock(), cancelled: live }))?.status).toBe("ready")
    expect(calls.filter((c) => c.startsWith("POST"))).toHaveLength(2)
  })

  it("is what the viewer uses, with no unbounded polling left in it", () => {
    expect(VIEWER).toMatch(/requestPdf\(/)
    expect(VIEWER).not.toMatch(/setTimeout\(checkPdf/)
  })
})
