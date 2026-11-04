/**
 * D-352 — the property report page's lead form requires consent, and sends
 * the wording it showed.
 *
 * The box was optional: nothing checked it, and the lead was stored and handed
 * to the agent either way. Now the form refuses without it (and so does the
 * API — apps/api/tests/test_leads_require_consent.py), and the sentence beside
 * the box goes with the lead, as on the Home Value Page.
 */
import fs from "fs"
import path from "path"
import { P_CONSENT_COPY, P_CONSENT_REQUIRED } from "@/app/p/[code]/lead-capture-form"

const SRC = fs.readFileSync(path.join(__dirname, "../app/p/[code]/lead-capture-form.tsx"), "utf8")

describe("the property page lead form", () => {
  it("shows the sentence it has always shown", () => {
    expect(P_CONSENT_COPY).toBe("I consent to being contacted about this property and related services.")
    expect(SRC).toMatch(/\{P_CONSENT_COPY\}\s*<\/label>/)
  })

  it("will not submit without the box ticked", () => {
    expect(SRC).toMatch(/id="consent_given"[\s\S]*?required[\s\S]*?\/>/)
    expect(SRC).toMatch(/if \(!formData\.consent_given\) \{\s*setErrorMessage\(P_CONSENT_REQUIRED\)/)
    expect(P_CONSENT_REQUIRED).toMatch(/tick the box/)
  })

  it("sends the wording it showed with the lead", () => {
    expect(SRC).toMatch(/consent_text: P_CONSENT_COPY/)
  })
})
