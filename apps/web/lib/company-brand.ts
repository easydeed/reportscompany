// The company Branding page's decisions, kept out of the page so they can be
// tested on their own. Every field read here is one GET /v1/company/branding
// returns, and every field written is one PATCH /v1/company/branding accepts
// (tests/test_company_brand_reads_what_the_api_returns.py).
//
// What the company sets: its name, its two logos and its two colours. The
// PATCH cascades them to every rep that hasn't set their own, and the reps'
// reports and emails carry them with the rep's own photo and contact line
// (worker `_resolve_email_brand`). The page never sends `rep_photo_url` or
// `contact_line*` — those are each rep's — nor `website_url`.

/** GET /v1/company/branding → `branding`. */
export type CompanyBranding = {
  brand_display_name: string | null
  logo_url: string | null
  email_logo_url: string | null
  footer_logo_url: string | null
  email_footer_logo_url: string | null
  primary_color: string | null
  accent_color: string | null
  rep_photo_url: string | null
  contact_line1: string | null
  contact_line2: string | null
  website_url: string | null
}

/** What the page edits. */
export type Brand = { name: string; logo: string | null; logoOnWhite: string | null; primary: string; accent: string }

/** The PATCH body: only fields the page owns. */
export type BrandPatch = Partial<Pick<CompanyBranding,
  "brand_display_name" | "logo_url" | "email_logo_url" | "footer_logo_url" | "email_footer_logo_url" | "primary_color" | "accent_color">>

export const HEX = /^#[0-9a-fA-F]{6}$/

/**
 * The form's starting point. A company with no branding row yet (a new one)
 * starts from its account name and no colours: nothing is filled in that the
 * company did not choose.
 */
export function brandFromApi(b: CompanyBranding | null | undefined, accountName: string): Brand {
  return {
    name: b?.brand_display_name || accountName,
    logo: b?.logo_url || b?.email_logo_url || null,
    logoOnWhite: b?.footer_logo_url || b?.email_footer_logo_url || null,
    primary: b?.primary_color || "",
    accent: b?.accent_color || "",
  }
}

/**
 * Only what changed, in the PATCH's fields. A logo goes to both its report and
 * its email slot, as the page before this one did. The PATCH keeps a field it
 * is sent `null` for (COALESCE), so a removal cannot be saved — the page
 * offers Replace, never Remove — and an empty or malformed colour is not sent.
 */
export function brandPatch(before: Brand, after: Brand): BrandPatch {
  const p: BrandPatch = {}
  const name = after.name.trim()
  if (name && name !== before.name.trim()) p.brand_display_name = name
  if (after.logo && after.logo !== before.logo) { p.logo_url = after.logo; p.email_logo_url = after.logo }
  if (after.logoOnWhite && after.logoOnWhite !== before.logoOnWhite) { p.footer_logo_url = after.logoOnWhite; p.email_footer_logo_url = after.logoOnWhite }
  if (HEX.test(after.primary) && after.primary.toLowerCase() !== before.primary.toLowerCase()) p.primary_color = after.primary
  if (HEX.test(after.accent) && after.accent.toLowerCase() !== before.accent.toLowerCase()) p.accent_color = after.accent
  return p
}

/**
 * What saving does, said before it happens. The PATCH cascades to every rep
 * whose row has `branding_override` false — a rep who set their own brand
 * keeps it — so this does not promise a count.
 */
export const SAVE_NOTE = "Saving updates every rep who hasn't set their own brand — their next report and email carry it."
