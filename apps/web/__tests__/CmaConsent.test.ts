/**
 * The home value page's consent wording.
 *
 * #238 emptied the consent copy and showed a grey "[Consent wording — …]"
 * placeholder beside the checkbox, on every agent's live page, while the lead
 * still recorded consent_given = true. The owner's decision was to keep the
 * sentence the page has always shown, and leave a SEPARATE slot for the
 * brokerage's TCPA wording. This pins both halves.
 */
import fs from "fs"
import path from "path"
import { CONSENT_COPY, TCPA_COPY, consentText } from "@/app/cma/[code]/cma-funnel"

const SRC = fs.readFileSync(path.join(__dirname, "../app/cma/[code]/cma-funnel.tsx"), "utf8")

describe("home value page consent", () => {
  it("shows the sentence the live page has always shown, in the agent's name", () => {
    expect(consentText("Dana Ortiz")).toBe(
      "I agree to receive my report and to be contacted by Dana Ortiz about my property.")
  })

  it("never shows a placeholder beside the checkbox", () => {
    expect(consentText("Dana Ortiz")).not.toMatch(/\[|Consent wording/)
    expect(SRC).not.toMatch(/\[Consent wording/)
  })

  it("keeps the TCPA slot empty until the brokerage writes it", () => {
    expect(CONSENT_COPY).not.toBe("")
    expect(TCPA_COPY).toBe("")
  })

  it("records exactly the wording it showed", () => {
    expect(SRC).toMatch(/<span>\{consentText\(agent\.name\)\}<\/span>/)
    expect(SRC).toMatch(/consentText: consentText\(agent\.name\)/)
  })
})
