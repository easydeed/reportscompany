/**
 * @jest-environment node
 *
 * LR-024 (design rev 3): the wizard's keyed creates reach only routes that
 * honour the key.
 *
 * Each proxy builds a fresh header set, which dropped the key before this
 * change. A keyed request now goes to /v1/idempotent/{reports,schedules},
 * which only an API with the key contract has: an older API answers 404
 * there without running anything, and the proxy turns that into 503
 * idempotent_create_unavailable, so a keyed request can never create an
 * unkeyed duplicate on a mixed-version rollout or after a rollback.
 */
import { NextRequest } from "next/server"
import { POST as postReport } from "@/app/api/proxy/v1/reports/route"
import { POST as postSchedule } from "@/app/api/proxy/v1/schedules/route"

process.env.NEXT_PUBLIC_API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://api.test"

function api(...answers: Array<{ status: number; body?: unknown; headers?: Record<string, string> }>) {
  const spy = jest.fn()
  for (const a of answers) spy.mockResolvedValueOnce(new Response(JSON.stringify(a.body ?? {}), { status: a.status, headers: a.headers }))
  global.fetch = spy as unknown as typeof fetch
  return spy
}

function request(url: string, key?: string) {
  return new NextRequest(url, {
    method: "POST",
    body: JSON.stringify({ report_type: "market_snapshot" }),
    headers: {
      "Content-Type": "application/json",
      cookie: "mr_token=t0k",
      ...(key ? { "Idempotency-Key": key } : {}),
    },
  })
}

describe.each([
  ["reports", postReport, "https://trendyreports.io/api/proxy/v1/reports", 202],
  ["schedules", postSchedule, "https://trendyreports.io/api/proxy/v1/schedules", 201],
])("POST /api/proxy/v1/%s", (name, POST, url, created) => {
  it("sends a keyed create, with its key, only to the keyed route", async () => {
    const spy = api({ status: created, body: { id: "x" } })
    await POST(request(url, "key-123456"))
    const [to, init] = spy.mock.calls[0]
    expect(String(to)).toMatch(new RegExp(`/v1/idempotent/${name}$`))
    expect(new Headers(init.headers).get("idempotency-key")).toBe("key-123456")
  })

  it("sends an unkeyed create to the existing route, as before", async () => {
    const spy = api({ status: created, body: { id: "x" } })
    await POST(request(url))
    const [to, init] = spy.mock.calls[0]
    expect(String(to)).toMatch(new RegExp(`/v1/${name}$`))
    expect(new Headers(init.headers).has("idempotency-key")).toBe(false)
  })

  it("an API without the contract (404 on the keyed route) is 503 unavailable: nothing was created", async () => {
    api({ status: 404, body: { detail: "Not Found" } })
    const res = await POST(request(url, "key-123456"))
    expect(res.status).toBe(503)
    expect((await res.json()).error).toBe("idempotent_create_unavailable")
  })

  it("passes the API's replay marker back", async () => {
    api({ status: created, body: { id: "x" }, headers: { "Idempotent-Replayed": "true" } })
    const res = await POST(request(url, "key-123456"))
    expect(res.status).toBe(created)
    expect(res.headers.get("idempotent-replayed")).toBe("true")
  })

  it("mixed versions: first send to an old API, the retry to a new one: one create, same key", async () => {
    const spy = api({ status: 404 }, { status: created, body: { id: "x" } })
    const first = await POST(request(url, "key-123456"))
    const retry = await POST(request(url, "key-123456"))
    expect(first.status).toBe(503)
    expect(retry.status).toBe(created)
    expect(spy.mock.calls.map(([, init]) => new Headers(init.headers).get("idempotency-key"))).toEqual(["key-123456", "key-123456"])
  })
})
