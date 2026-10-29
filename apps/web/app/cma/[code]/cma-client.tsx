"use client"

import { useMemo, useRef } from "react"
import CmaFunnel, { type Agent, type Lead, type Record_, type Suggestion } from "./cma-funnel"
import { ensureGooglePlaces, parseAddressComponents } from "@/hooks/useGooglePlaces"
import { cmaRequestBody, cmaSearchBody, storedProperty, type StoredProperty } from "@/lib/cma-lead"

export type CmaAgentSource = {
  name: string
  company_name: string | null
  license_number: string | null
  phone: string | null
  photo_url: string | null
  theme_color: string
}

function toRecord(property: StoredProperty): Record_ {
  return {
    address: property.address,
    city: property.city,
    state: property.state,
    zip: property.zip,
    type: property.property_type || "",
    beds: property.bedrooms ?? null,
    baths: property.bathrooms ?? null,
    sqft: property.sqft ?? null,
    yearBuilt: property.year_built ?? null,
  }
}

function demoProperty(address: string): StoredProperty {
  return {
    apn: "DEMO-0000",
    fips: "00000",
    address: address || "742 Evergreen Terrace",
    city: "San Diego",
    state: "CA",
    zip: "92101",
    owner_name: "Sample Homeowner",
    bedrooms: 4,
    bathrooms: 2.5,
    sqft: 2150,
    year_built: 1998,
    property_type: "Single Family",
  }
}

export function CmaExperience({
  code,
  isDemo,
  initialAddress,
  source,
}: {
  code: string
  isDemo: boolean
  initialAddress?: string
  source: CmaAgentSource
}) {
  const byAddress = useRef(new Map<string, StoredProperty>())
  const placeIds = useRef(new Map<string, string>())
  const codeRef = useRef(code)
  const demoRef = useRef(isDemo)
  codeRef.current = code
  demoRef.current = isDemo

  const api = useMemo(() => ({
    async suggest(q: string): Promise<Suggestion[]> {
      try {
        await ensureGooglePlaces()
      } catch {
        return []
      }
      if (!window.google?.maps?.places) return []
      const svc = new google.maps.places.AutocompleteService()
      const preds = await new Promise<google.maps.places.AutocompletePrediction[]>((resolve) => {
        svc.getPlacePredictions(
          { input: q, types: ["address"], componentRestrictions: { country: "us" } },
          (rows, status) => {
            resolve(status === google.maps.places.PlacesServiceStatus.OK && rows ? rows : [])
          },
        )
      })
      return preds.slice(0, 3).map((prediction) => {
        const suggestion = {
          address: prediction.structured_formatting.main_text,
          locality: prediction.structured_formatting.secondary_text,
        }
        placeIds.current.set(suggestion.address + suggestion.locality, prediction.place_id)
        return suggestion
      })
    },

    async lookup(input: Suggestion | string): Promise<Record_ | null> {
      const typed = typeof input === "string" ? input : input.address
      if (demoRef.current) {
        const property = demoProperty(typed)
        byAddress.current.set(property.address, property)
        return toRecord(property)
      }

      const body = typeof input === "string"
        ? cmaSearchBody(input)
        : await placeSearchBody(input, placeIds.current)
      if (!body) return null

      const res = await fetch(`/api/proxy/v1/cma/${codeRef.current}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
      if (!res.ok) return null
      const rows = await res.json() as StoredProperty[]
      const raw = Array.isArray(rows) ? rows[0] : null
      if (!raw?.address) return null
      const property = storedProperty(raw)
      byAddress.current.set(property.address, property)
      return toRecord(property)
    },

    async submit(lead: Lead): Promise<{ reportUrl?: string }> {
      if (demoRef.current) return {}
      const property = byAddress.current.get(lead.record.address)
      if (!property) throw new Error("missing property")
      const res = await fetch(`/api/proxy/v1/cma/${codeRef.current}/request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cmaRequestBody(property, {
          method: lead.method,
          contact: lead.contact,
          name: lead.firstName,
          beds: lead.record.beds,
          baths: lead.record.baths,
          sqft: lead.record.sqft,
          yearBuilt: lead.record.yearBuilt,
        })),
      })
      if (!res.ok) throw new Error("request failed")
      return {}
    },
  }), [])

  const agent: Agent = {
    name: source.name,
    brokerage: source.company_name ?? "",
    dre: source.license_number,
    phone: source.phone ?? "",
    photoUrl: source.photo_url,
    color: source.theme_color,
  }

  return (
    <>
      {isDemo && (
        <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-center text-sm text-amber-800">
          <strong>Demo Mode</strong> — This is a preview of what your agents&apos; CMA pages look like. No leads will be captured.
        </div>
      )}
      <CmaFunnel
        agent={agent}
        api={api}
        initialAddress={initialAddress}
        cover={({ record, requesterName }) => (
          <div className="flex h-full w-full flex-col justify-end bg-[#FAFAF7] p-12 text-[#0F172A]">
            <p className="text-[40px] font-extrabold leading-tight">{record?.address ?? "Your report"}</p>
            {record && (
              <p className="mt-2 text-[22px] text-[#64748B]">{record.city}, {record.state} {record.zip}</p>
            )}
            {requesterName ? <p className="mt-6 text-[22px]">Prepared for {requesterName}</p> : null}
          </div>
        )}
      />
    </>
  )
}

async function placeSearchBody(suggestion: Suggestion, placeIds: Map<string, string>) {
  const placeId = placeIds.get(suggestion.address + suggestion.locality)
  if (!placeId || !window.google?.maps?.places) return null
  const details = await new Promise<google.maps.places.PlaceResult>((resolve, reject) => {
    const svc = new google.maps.places.PlacesService(document.createElement("div"))
    svc.getDetails(
      { placeId, fields: ["address_components", "formatted_address", "geometry"] },
      (place, status) => {
        if (status !== google.maps.places.PlacesServiceStatus.OK || !place) reject(new Error(status))
        else resolve(place)
      },
    )
  })
  const parsed = parseAddressComponents(details)
  return cmaSearchBody({ address: parsed.address, city: parsed.city, state: parsed.state })
}
