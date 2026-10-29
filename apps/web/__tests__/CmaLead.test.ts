import { cmaRequestBody, cmaSearchBody, type StoredProperty } from "@/lib/cma-lead"

const property: StoredProperty = {
  apn: "1234-567",
  fips: "06059",
  address: "14 Cartwheel",
  city: "Irvine",
  state: "CA",
  zip: "92618",
  bedrooms: 4,
  bathrooms: 2.5,
  sqft: 2100,
  year_built: 1998,
  latitude: 33.68,
  longitude: -117.82,
  property_type: "Single Family",
}

const captured = JSON.stringify({
  phone: "5551234567",
  email: null,
  delivery_method: "sms",
  name: "Jane",
  property_apn: "1234-567",
  property_fips: "06059",
  property_address: "14 Cartwheel",
  property_city: "Irvine",
  property_state: "CA",
  property_zip: "92618",
  consent_given: true,
  bedrooms: 4,
  bathrooms: 2.5,
  sqft: 2100,
  year_built: 1998,
  latitude: 33.68,
  longitude: -117.82,
  property_type: "Single Family",
})

describe("the home-value request matches the page it replaces", () => {
  it("posts the same search body for a typed address", () => {
    expect(JSON.stringify(cmaSearchBody("14 Cartwheel"))).toBe(JSON.stringify({ address: "14 Cartwheel" }))
  })

  it("posts the same lead body, less the owner name (D-309)", () => {
    const body = cmaRequestBody(property, {
      method: "sms",
      contact: "(555) 123-4567",
      name: "Jane",
      beds: 4,
      baths: 2.5,
      sqft: 2100,
      yearBuilt: 1998,
    })
    expect(JSON.stringify(body)).toBe(captured)
  })

  it("sends an edited bed count and no owner name, even if one is handed in (D-309)", () => {
    // A stale session or an old cached search may still hold an owner name;
    // the request must not forward it. The person is named by `name` alone.
    const stale = { ...property, owner_name: "Previous Owner" } as StoredProperty
    const body = cmaRequestBody(stale, {
      method: "sms",
      contact: "5551234567",
      name: "Jane",
      beds: 3,
      baths: 2.5,
      sqft: 2100,
      yearBuilt: 1998,
    })
    expect(body.bedrooms).toBe(3)
    expect("owner_name" in body).toBe(false)
    expect(JSON.stringify(body)).not.toContain("Previous Owner")
  })
})
