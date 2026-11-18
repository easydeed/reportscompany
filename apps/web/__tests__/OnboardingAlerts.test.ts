import { createOnboardingAlert } from "@/lib/onboarding-alerts"

const rid = "11111111-1111-4111-8111-111111111111"
const sid = "22222222-2222-4222-8222-222222222222"
const ok = (body: object) => ({ ok: true, json: async () => body })

it("resumes after a lost response to either step without a new identity", async () => {
  sessionStorage.clear()
  const api = global.fetch as jest.Mock
  api.mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce(ok({ report_id: rid }))
    .mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce(ok({ id: sid }))
  const report = () => createOnboardingAlert("acct", "market_reports", "{}", sessionStorage)
  const schedule = () => createOnboardingAlert("acct", "schedules", "{}", sessionStorage)
  await expect(report()).rejects.toThrow()
  await expect(report()).resolves.toBe(rid)
  await expect(schedule()).rejects.toThrow()
  // The server replays a completed step, even across browsers.
  api.mockReset()
  api.mockResolvedValueOnce(ok({ report_id: rid })).mockResolvedValueOnce(ok({ id: sid }))
    .mockResolvedValueOnce(ok({ active: true })).mockResolvedValueOnce(ok({ id: sid }))
    .mockResolvedValueOnce(ok({ active: true }))
  await expect(report()).resolves.toBe(rid)
  await expect(schedule()).resolves.toBe(sid)
  await expect(schedule()).resolves.toBe(sid)
  const keys = api.mock.calls.filter(([, init]) => init.method === "POST")
    .map(([, init]) => init.headers["Idempotency-Key"])
  expect(keys).toEqual(["onboarding-acct-market_reports", "onboarding-acct-schedules", "onboarding-acct-schedules"])
})

it("recovers the original report after the replay window in a fresh tab", async () => {
  const api = global.fetch as jest.Mock
  sessionStorage.clear()
  api.mockResolvedValueOnce({ ok: false, status: 410, json: async () => ({
    detail: { error: "idempotency_key_expired", resource_id: rid, request_matches: false },
  }) }).mockResolvedValueOnce(ok({ id: rid }))
  await expect(createOnboardingAlert("acct", "market_reports", "{}", sessionStorage)).resolves.toBe(rid)
  expect(api).toHaveBeenLastCalledWith(`/api/proxy/v1/reports/${rid}`, { cache: "no-store" })
})

it("identifies changed settings and a paused saved schedule", async () => {
  const api = global.fetch as jest.Mock
  api.mockResolvedValueOnce({ ok: false, status: 409, json: async () => ({
    detail: { error: "idempotency_key_reused", resource_id: sid },
  }) })
  await expect(createOnboardingAlert("acct", "schedules", "{}", sessionStorage)).rejects.toThrow("different settings")
  api.mockResolvedValueOnce(ok({ id: sid })).mockResolvedValueOnce(ok({ active: false }))
  await expect(createOnboardingAlert("acct", "schedules", "{}", sessionStorage)).rejects.toThrow("paused")
})
