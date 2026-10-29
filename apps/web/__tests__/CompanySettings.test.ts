import { personRole, profilePatch, websitePatch, type Profile } from "@/lib/company-settings"

describe("what each role can do (D-280)", () => {
  it("admin", () => expect(personRole("admin").label).toBe("Admin"))
  it("anyone else sees, and changes nothing", () => expect(personRole("viewer")).toEqual({ label: "Viewer", can: "can see everything, change nothing" }))
})

describe("the website the PATCH can take", () => {
  it("adds https:// to a bare domain", () => expect(websitePatch(null, "pct.example.com")).toEqual({ website_url: "https://pct.example.com" }))
  it("an emptied box is not a change the PATCH can make", () => expect(websitePatch("https://a.example", "  ")).toBeNull())
  it("unchanged is nothing to send", () => expect(websitePatch("https://a.example", "https://a.example")).toBeNull())
  it("not a website is not sent", () => expect(websitePatch(null, "not a site")).toBeNull())
})

describe("your details send only what changed", () => {
  const before: Profile = { first_name: "Casey", last_name: "Lin", job_title: "", phone: "", avatar_url: null }
  it("nothing changed", () => expect(profilePatch(before, before)).toBeNull())
  it("one field", () => expect(profilePatch(before, { ...before, job_title: " Owner " })).toEqual({ job_title: "Owner" }))
  it("a new photo", () => expect(profilePatch(before, { ...before, avatar_url: "https://x/p.png" })).toEqual({ avatar_url: "https://x/p.png" }))
  it("a removed photo is not sent", () => expect(profilePatch({ ...before, avatar_url: "https://x/p.png" }, before)).toBeNull())
})
