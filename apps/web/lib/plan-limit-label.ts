/**
 * The plan picker's label, from the plans table (D-293). It used to be typed —
 * "Free (5 reports/month)", "Trial (10 reports/month)" — from the legacy
 * `monthly_report_limit`, while the gate enforces 3 for both.
 */
export function planLimitLabel(limit: number | null | undefined): string {
  if (limit == null) return "no market-report limit set"
  if (limit >= 10000) return "unlimited market reports"
  return `${limit.toLocaleString()} market reports/month`
}
