/**
 * D-079: the postal-address settings' decisions. An empty save clears the
 * address (and is still a save); the note under the field always names the
 * address the footer carries and whose it is — never a blank.
 */
import { addressPut, cleanAddress, inUseNote, type PostalAddress } from "@/lib/postal-address"

const PLATFORM = "440 Rte. 66, Glendora, CA 91740"
const base: PostalAddress = { postal_address: null, can_edit: true, source: "platform", in_use: PLATFORM, company_name: null, platform_address: PLATFORM }

describe("cleanAddress", () => {
  it("is one line, single-spaced, or null", () => {
    expect(cleanAddress("  12 Oak Ave,\n  Anytown ")).toBe("12 Oak Ave, Anytown")
    expect(cleanAddress("   ")).toBeNull()
    expect(cleanAddress("")).toBeNull()
  })
})

describe("addressPut", () => {
  it("sends nothing when nothing changed", () => {
    expect(addressPut(null, "  ")).toBeNull()
    expect(addressPut("12 Oak Ave", " 12 Oak  Ave ")).toBeNull()
  })
  it("sends the cleaned value", () => {
    expect(addressPut(null, " 12 Oak Ave ")).toEqual({ postal_address: "12 Oak Ave" })
  })
  it("an emptied field is a clear, sent as null", () => {
    expect(addressPut("12 Oak Ave", "")).toEqual({ postal_address: null })
  })
})

describe("inUseNote", () => {
  it("names the platform address when none is set", () => {
    expect(inUseNote(base)).toBe(`Not set. Until it is, your emails carry TrendyReports' address: ${PLATFORM}`)
  })
  it("names the account's own", () => {
    expect(inUseNote({ ...base, postal_address: "12 Oak Ave", source: "own", in_use: "12 Oak Ave" })).toBe("Your emails show: 12 Oak Ave")
  })
  it("names the company's, and who sets it, for a rep", () => {
    const note = inUseNote({ ...base, can_edit: false, source: "company", in_use: "1 Title Plaza", company_name: "Seat Co A" })
    expect(note).toBe("Your emails use Seat Co A's address: 1 Title Plaza. Your company's admin sets it.")
  })
  it("a rep whose company set none is told the platform's", () => {
    expect(inUseNote({ ...base, can_edit: false, company_name: "Seat Co A" })).toContain(PLATFORM)
  })
})
