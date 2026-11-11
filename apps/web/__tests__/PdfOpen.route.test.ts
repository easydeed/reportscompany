/**
 * @jest-environment node
 *
 * LR-022 (Codex, #283): "Open your PDF report" signs a new link on every open.
 *
 * The first fix put the signed URL from the first request in the link's href;
 * with the page left open past the signature's hour it opened a dead link and
 * offered no way out. The link now points at this route, which asks the API's
 * status route (signs a new link to the SAME stored PDF; never queues or
 * renders) and redirects to it.
 */
import { GET } from "@/app/api/proxy/v1/r/[id]/pdf/open/route"

const PAGE = "https://trendyreports.io/api/proxy/v1/r/r1/pdf/open"
const params = { params: Promise.resolve({ id: "r1" }) }

function api(...bodies: Array<{ status: number; body: Record<string, unknown> }>) {
  const fetchSpy = jest.fn()
  for (const b of bodies) fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(b.body), { status: b.status }))
  global.fetch = fetchSpy as unknown as typeof fetch
  return fetchSpy
}

it("each open redirects to a link signed for that open, and only asks the status route", async () => {
  const fetchSpy = api(
    { status: 200, body: { status: "ready", pdf_url: "https://r2.test/k.pdf?X-Amz-Signature=first" } },
    { status: 200, body: { status: "ready", pdf_url: "https://r2.test/k.pdf?X-Amz-Signature=an-hour-later" } },
  )
  const first = await GET(new Request(PAGE), params)
  const later = await GET(new Request(PAGE), params)
  expect(first.status).toBe(302)
  expect(first.headers.get("location")).toBe("https://r2.test/k.pdf?X-Amz-Signature=first")
  expect(later.headers.get("location")).toBe("https://r2.test/k.pdf?X-Amz-Signature=an-hour-later")
  expect(first.headers.get("cache-control")).toBe("no-store")
  // Two signings, no generation: the status route never queues anything.
  expect(fetchSpy).toHaveBeenCalledTimes(2)
  for (const [url, init] of fetchSpy.mock.calls) {
    expect(String(url)).toMatch(/\/v1\/r\/r1\/pdf\/status$/)
    expect(init?.method ?? "GET").toBe("GET")
  }
})

it.each([
  ["a PDF that is not ready", { status: 200, body: { status: "missing", message: "x" } }],
  ["an unknown report", { status: 404, body: { detail: "Report not found" } }],
  ["a ready answer with no link", { status: 200, body: { status: "ready" } }],
])("%s goes back to the report, where the button says what to do", async (_, answer) => {
  api(answer)
  const res = await GET(new Request(PAGE), params)
  expect(res.status).toBe(303)
  expect(new URL(res.headers.get("location") || "").pathname).toBe("/r/r1")
})

it("an API that cannot be reached goes back to the report", async () => {
  global.fetch = jest.fn().mockRejectedValue(new Error("down")) as unknown as typeof fetch
  jest.spyOn(console, "error").mockImplementation(() => {})
  const res = await GET(new Request(PAGE), params)
  expect(new URL(res.headers.get("location") || "").pathname).toBe("/r/r1")
})
