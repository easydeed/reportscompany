import { cmaRequestBody, cmaSearchBody, type StoredProperty } from "@/lib/cma-lead"

const property: StoredProperty = {
  apn: "1234-567",
  fips: "06059",
  address: "14 Cartwheel",
  city: "Irvine",
  state: "CA",
  zip: "92618",
  owner_name: "Previous Owner",
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
  owner_name: "Previous Owner",
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

  it("posts the same lead body, including the owner name the page must not show", () => {
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

  it("sends an edited bed count and leaves the owner name on the wire", () => {
    const body = cmaRequestBody(property, {
      method: "sms",
      contact: "5551234567",
      name: "Jane",
      beds: 3,
      baths: 2.5,
      sqft: 2100,
      yearBuilt: 1998,
    })
    expect(body.bedrooms).toBe(3)
    expect(body.owner_name).toBe("Previous Owner")
  })
})
