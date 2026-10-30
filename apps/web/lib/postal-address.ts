// The account's own postal address (D-079), for the foot of the emails it
// sends. Kept out of the pages so the decisions can be tested on their own.
//
// GET /v1/account/postal-address → PostalAddress. PUT takes
// `{ postal_address }`: an empty value CLEARS it and is never an error, and an
// account with none sends with TrendyReports' address — which the page says,
// with the address, rather than implying the footer goes blank.

export type PostalAddress = {
  postal_address: string | null
  can_edit: boolean
  /** Whose address the footer carries today. */
  source: "own" | "company" | "platform"
  in_use: string
  company_name: string | null
  platform_address: string
}

/** What the API stores for what was typed: one line, single-spaced, or null. */
export function cleanAddress(typed: string): string | null {
  const t = typed.replace(/\s+/g, " ").trim()
  return t || null
}

/** The PUT body, or null when saving would change nothing. */
export function addressPut(saved: string | null, typed: string): { postal_address: string | null } | null {
  const next = cleanAddress(typed)
  return next === (saved ?? null) ? null : { postal_address: next }
}

/** The sentence under the field: what the footer carries now, and whose it is. */
export function inUseNote(a: PostalAddress): string {
  if (a.source === "own") return `Your emails show: ${a.in_use}`
  if (a.source === "company") return `Your emails use ${a.company_name ?? "your company"}'s address: ${a.in_use}. Your company's admin sets it.`
  if (a.company_name) return `Your company hasn't set an address, so your emails carry TrendyReports' address: ${a.platform_address}`
  return `Not set. Until it is, your emails carry TrendyReports' address: ${a.platform_address}`
}
