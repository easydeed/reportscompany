import { IdempotencyKeys, PROBLEMS, sendCreate, type Product } from "./wizard-requests"

/** Each account has one first report and one first schedule. The API owns
 * deduplication across tabs, reloads and lost responses. Only confirmed IDs
 * are cached for display. Every submission consults the server. */
export async function createOnboardingAlert(
  accountId: string, product: Product, payload: string, storage: Storage,
): Promise<string> {
  const key = `onboarding-${accountId}-${product}`
  const result = await sendCreate(new IdempotencyKeys(() => key), product, payload)
  let id: string
  switch (result.kind) {
    case "created":
      id = result.resourceId
      break
    case "limit":
      throw new Error(`${result.title}. ${result.detail}`)
    case "verification":
      throw new Error(result.refusal.message)
    case "invalid":
    case "key_expired":
      if (!result.previousId) {
        throw new Error(result.kind === "invalid" ? result.message : "Check your existing reports and schedules before starting a new alert.")
      }
      if (product === "schedules" && (result.kind === "invalid" || !result.matches)) {
        throw new Error("An earlier monthly alert used different settings. Open Schedules to review or edit it.")
      }
      id = result.previousId
      break
    case "gone":
      throw new Error("Your earlier alert was deleted. Open Reports or Schedules to choose what to do next.")
    default:
      throw new Error(PROBLEMS[result.kind].sub)
  }
  // A durable receipt can outlive the report or its active schedule. The
  // server is also authoritative if the user resumes in a different browser.
  if (product === "schedules" || result.kind !== "created") {
    const resourceId = encodeURIComponent(id)
    const check = product === "schedules"
      ? await fetch(`/api/proxy/v1/schedules/${resourceId}`, { cache: "no-store" })
      : await fetch(`/api/proxy/v1/reports/${resourceId}`, { cache: "no-store" })
    if (!check.ok) throw new Error("Open Reports or Schedules to check the earlier alert before continuing.")
    if (product === "schedules" && (await check.json()).active !== true) {
      throw new Error("Your monthly alert is paused. Open Schedules to review or resume it.")
    }
  }
  storage.setItem(key, id)
  return id
}
