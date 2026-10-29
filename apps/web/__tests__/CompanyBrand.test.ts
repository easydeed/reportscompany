import { brandFromApi, brandPatch, type Brand, type CompanyBranding } from "@/lib/company-brand"

const row = (over: Partial<CompanyBranding> = {}): CompanyBranding => ({
  brand_display_name: "Pacific Test Title", logo_url: "https://x/logo.png", email_logo_url: "https://x/logo.png",
  footer_logo_url: null, email_footer_logo_url: null, primary_color: "#0E7490", accent_color: "#D69649",
  rep_photo_url: "https://x/rep.png", contact_line1: "a", contact_line2: "b", website_url: "https://x", ...over,
})

describe("the form starts from what the company saved", () => {
  it("reads the saved brand", () => {
    expect(brandFromApi(row(), "Acct")).toEqual({ name: "Pacific Test Title", logo: "https://x/logo.png", logoOnWhite: null, primary: "#0E7490", accent: "#D69649" })
  })
  it("a new company starts from its account name and no colours — nothing chosen for it", () => {
    expect(brandFromApi(null, "Acct Name")).toEqual({ name: "Acct Name", logo: null, logoOnWhite: null, primary: "", accent: "" })
  })
})

describe("saving sends only what changed", () => {
  const before: Brand = brandFromApi(row(), "Acct")
  it("nothing changed, nothing sent", () => expect(brandPatch(before, before)).toEqual({}))
  it("a colour, alone", () => expect(brandPatch(before, { ...before, primary: "#112233" })).toEqual({ primary_color: "#112233" }))
  it("a colour change of case only is no change", () => expect(brandPatch(before, { ...before, primary: "#0e7490" })).toEqual({}))
  it("a logo goes to its report and email slots", () => {
    expect(brandPatch(before, { ...before, logo: "https://x/new.png" })).toEqual({ logo_url: "https://x/new.png", email_logo_url: "https://x/new.png" })
    expect(brandPatch(before, { ...before, logoOnWhite: "https://x/w.png" })).toEqual({ footer_logo_url: "https://x/w.png", email_footer_logo_url: "https://x/w.png" })
  })
  it("a half-typed colour is not sent", () => expect(brandPatch(before, { ...before, accent: "#D696" })).toEqual({}))
  it("an emptied name is not sent (the PATCH would keep the old one anyway)", () => expect(brandPatch(before, { ...before, name: "  " })).toEqual({}))
  it("a removed logo is not sent: the PATCH keeps a null", () => expect(brandPatch(before, { ...before, logo: null })).toEqual({}))
})
