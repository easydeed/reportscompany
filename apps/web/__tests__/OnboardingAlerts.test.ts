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
  // Re-enter the flow as after a reload. The first report is already confirmed.
  await expect(report()).resolves.toBe(rid)
  await expect(schedule()).resolves.toBe(sid)
  await expect(schedule()).resolves.toBe(sid)
  expect(api).toHaveBeenCalledTimes(4)
  const keys = api.mock.calls.map(([, init]) => init.headers["Idempotency-Key"])
  expect(keys[0]).toBe(keys[1])
  expect(keys[2]).toBe(keys[3])
  expect(keys[0]).not.toBe(keys[2])
})
