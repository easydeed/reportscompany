# `/cma/[code]` — Home Value Page drop-in

`cma-funnel.tsx` is the client component for the six-step homeowner funnel (spec: `design_handoff_product/README.md` §Home Value Page; reference: `Home Value Page.dc.html`). It replaces the existing `cma-funnel.tsx`. `page.tsx` (server) is yours: load the agent by `code`, build the `api` object, render `<CmaFunnel agent api cover />`.

## What page.tsx supplies

- `agent` — `{ name, brokerage, dre, phone, photoUrl, brand, city }`. `brand` is the agent's property-report brand (`red · teal · cyan · amber · lime · violet`, `tests/golden/themes.json`). Nothing else on the page is branded.
- `api.suggest(q)` → up to 3 `{ address, locality }` for ≥2 chars (debounced 150ms in the component).
- `api.lookup(suggestion | string)` → `Record_` or `null`. Nulls render as a dash; the note under the facts names what was missing. Homeowner can edit beds/baths/sqft/year via "Something's off" — the edited record is what's submitted.
- `api.submit(lead)` → `{ reportUrl? }`. If `reportUrl` returns, Success shows "Open my report now"; if the PDF is async, omit it and the text/email carries the link.
- `cover({ record, requesterName, brand })` — render the property cover (elegant theme) for the record; `requesterName` updates live from the name field ("Prepared for"). The component pins it at 816×1056 and scales.

## Behaviour notes

- The waiting steps advance when both the stage ticker (3s / 4s) and the request have finished; a failed lookup returns to Address with an inline error and focuses the field; a failed submit returns to Contact.
- **No estimate number anywhere on the page.** The mock-up's success-screen "What's inside" list showed one — dropped here, per the rule. Don't add it back.
- No product logo. Footer right side is the brokerage · DRE.
- `CONSENT_COPY` (top of file) is empty on purpose. Until legal supplies the TCPA text the slot shows a grey italic placeholder; the checkbox is still required. Store `consentText` with the lead as shown at submit time.
