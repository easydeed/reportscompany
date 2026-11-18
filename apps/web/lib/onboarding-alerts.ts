import { IdempotencyKeys, PROBLEMS, sendCreate, type Product } from "./wizard-requests"

/** Each account has one first report and one first schedule. The API owns
 * deduplication across tabs, reloads and lost responses. Only confirmed IDs
 * are cached in this tab so completing the second step can skip the first. */
export async function createOnboardingAlert(
  accountId: string, product: Product, payload: string, storage: Storage,
): Promise<string> {
  const key = `onboarding-${accountId}-${product}`
  const existing = storage.getItem(key)
  if (existing) return existing
  const result = await sendCreate(new IdempotencyKeys(() => key), product, payload)
  switch (result.kind) {
    case "created":
      storage.setItem(key, result.resourceId)
      return result.resourceId
    case "limit":
      throw new Error(`${result.title}. ${result.detail}`)
    case "invalid":
      throw new Error(result.message)
    case "verification":
      throw new Error(result.refusal.message)
    case "key_expired":
    case "gone":
      throw new Error("Check your existing reports and schedules before starting a new alert.")
    default:
      throw new Error(PROBLEMS[result.kind].sub)
  }
}
