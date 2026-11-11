/**
 * @jest-environment node
 *
 * LR-024: the wizard's Idempotency-Key reaches the API through both proxies.
 *
 * Each proxy builds a fresh header set (cookie or Bearer token, Content-Type).
 * Before this change the key was dropped there silently, so the API could never
 * tell a retry from a new request.
 */
import { NextRequest } from "next/server"
import { POST as postReport } from "@/app/api/proxy/v1/reports/route"
import { POST as postSchedule } from "@/app/api/proxy/v1/schedules/route"

function api(status: number, body: unknown, headers: Record<string, string> = {}) {
  const spy = jest.fn().mockResolvedValue(new Response(JSON.stringify(body), { status, headers }))
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
])("POST /api/proxy/v1/%s", (_, POST, url, created) => {
  it("forwards the key to the API", async () => {
    const spy = api(created, { id: "x" })
    await POST(request(url, "key-123456"))
    const headers = new Headers(spy.mock.calls[0][1].headers)
    expect(headers.get("idempotency-key")).toBe("key-123456")
  })

  it("sends no key when the page sent none", async () => {
    const spy = api(created, { id: "x" })
    await POST(request(url))
    expect(new Headers(spy.mock.calls[0][1].headers).has("idempotency-key")).toBe(false)
  })

  it("passes the API's replay marker back", async () => {
    api(created, { id: "x" }, { "Idempotent-Replayed": "true" })
    const res = await POST(request(url, "key-123456"))
    expect(res.status).toBe(created)
    expect(res.headers.get("idempotent-replayed")).toBe("true")
  })
})
