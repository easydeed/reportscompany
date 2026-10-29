// The company Settings page's decisions, kept out of the page so they can be
// tested on their own. Every field read here is one GET /v1/company/settings
// returns (tests/test_company_settings_reads_what_the_api_returns.py).

/** GET /v1/company/settings. */
export type CompanySettings = {
  company: { name: string | null; website_url: string | null; postal_address: string | null }
  people: Person[]
  you: string | null
  can_manage: boolean
}

/** One person on the company account. `role` is the API's label of account_users.role. */
export type Person = { id: string; name: string; email: string; role: "admin" | "viewer" }

/** What a role can do, in the page's words (D-280). */
export function personRole(role: Person["role"]): { label: string; can: string } {
  return role === "admin"
    ? { label: "Admin", can: "can change everything" }
    : { label: "Viewer", can: "can see everything, change nothing" }
}

/** The editable part of PATCH /v1/users/me this page owns. */
export type Profile = { first_name: string; last_name: string; job_title: string; phone: string; avatar_url: string | null }

/** Only what changed; null when nothing did. A removed photo is not sent. */
export function profilePatch(before: Profile, after: Profile): Partial<Profile> | null {
  const p: Partial<Profile> = {}
  for (const k of ["first_name", "last_name", "job_title", "phone"] as const) {
    if (after[k].trim() !== before[k].trim()) p[k] = after[k].trim()
  }
  if (after.avatar_url && after.avatar_url !== before.avatar_url) p.avatar_url = after.avatar_url
  return Object.keys(p).length ? p : null
}

/**
 * The website as PATCH /v1/company/branding takes it, or null when there is
 * nothing to send. The PATCH keeps a field sent empty (COALESCE), so an
 * emptied box is not a change it can make; a bare domain gets https://.
 */
export function websitePatch(saved: string | null, typed: string): { website_url: string } | null {
  const t = typed.trim()
  const url = /^https?:\/\//i.test(t) ? t : `https://${t}`
  if (!/^https?:\/\/[^\s/]+\.[^\s/]+/i.test(url)) return null
  return url === (saved ?? "") ? null : { website_url: url }
}
