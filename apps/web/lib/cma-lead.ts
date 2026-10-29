/**
 * The body the live home-value page already posts. Design's funnel speaks in
 * a different shape; page.tsx translates, and this is the translation.
 * Keys and omissions match apps/web/app/cma/[code] as it stood on d1b48bcc,
 * less `owner_name`: the public search no longer returns it (D-309), and the
 * person asking is named by `name`, never by the assessor roll.
 */

export type StoredProperty = {
  apn: string
  fips: string
  address: string
  city: string
  state: string
  zip: string
  bedrooms?: number | null
  bathrooms?: number | null
  sqft?: number | null
  year_built?: number | null
  latitude?: number | null
  longitude?: number | null
  property_type?: string | null
}

export type LeadFacts = {
  method: "sms" | "email"
  contact: string
  name?: string
  beds: number | null
  baths: number | null
  sqft: number | null
  yearBuilt: number | null
}

/** A manual search sends only `address`. A picked place always sends city and state too. */
export function cmaSearchBody(input: string | { address: string; city: string; state: string }) {
  if (typeof input === "string") return { address: input }
  return { address: input.address, city: input.city, state: input.state }
}

function fact(edited: number | null, stored: number | null | undefined) {
  return edited === (stored ?? null) ? stored : edited
}

export function cmaRequestBody(property: StoredProperty, lead: LeadFacts) {
  return {
    phone: lead.method === "sms" ? lead.contact.replace(/\D/g, "") : null,
    email: lead.method === "email" ? lead.contact.trim() : null,
    delivery_method: lead.method,
    name: lead.name?.trim() || null,
    property_apn: property.apn,
    property_fips: property.fips,
    property_address: property.address,
    property_city: property.city,
    property_state: property.state,
    property_zip: property.zip,
    consent_given: true,
    bedrooms: fact(lead.beds, property.bedrooms),
    bathrooms: fact(lead.baths, property.bathrooms),
    sqft: fact(lead.sqft, property.sqft),
    year_built: fact(lead.yearBuilt, property.year_built),
    latitude: property.latitude,
    longitude: property.longitude,
    property_type: property.property_type,
  }
}

/** Keep the fields the old page kept. Anything else the search returns stays off the wire. */
export function storedProperty(raw: StoredProperty): StoredProperty {
  return {
    apn: raw.apn,
    fips: raw.fips,
    address: raw.address,
    city: raw.city,
    state: raw.state,
    zip: raw.zip,
    bedrooms: raw.bedrooms,
    bathrooms: raw.bathrooms,
    sqft: raw.sqft,
    year_built: raw.year_built,
    latitude: raw.latitude,
    longitude: raw.longitude,
    property_type: raw.property_type,
  }
}
