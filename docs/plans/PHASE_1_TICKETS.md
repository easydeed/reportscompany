# Delivery Surfaces — Phase 1 Ticket Pack

**Source:** `DELIVERY_SURFACES_MASTER_PLAN.md`
**Governs:** §0 Rules of Engagement from `EXECUTION_PLAN_2026-08-17.md` — branch hygiene, scope
discipline, token efficiency, and the self-review gate after every ticket.
**Base:** `main`

Six branches. **None has dependencies on the others** — they can run in any order, though the
listed order puts consumer-facing work first.

Standing rules for this pack, in addition to §0:

- **Templates are the spec, not the PDFs.** The rendered files were reviewed visually. Before
  fixing anything, locate the template that produces it and confirm the finding is in the source
  rather than an artifact of one render.
- **Two render generations exist** (master plan §02). If a fix behaves differently across themes,
  stop and report rather than fixing one and assuming the rest.
- **Report, don't guess, on anything gated.** Decisions 07, 08 and 09 are unanswered. Tickets note
  where they bite.

---

## P1-A · Consumer-facing · `fix/p1a-consumer-facing`

**Why first:** both items are on documents delivered to consumer leads through the capture funnel,
with no agent in the loop.

### A1 — Remove the property owner block · E1 · BROKEN

The property report prints the owner's legal name (`HERNANDEZ GERARDO J` / `MENDOZA YESSICA S`)
under a heading reading **"Prospective Property"**. All five themes.

1. Remove the owner name fields (primary and secondary) from the rendered output.
2. Rename the section. "Prospective Property" tells the recipient they are a prospect — use
   "Property Details" or equivalent.
3. Fix the aerial page body copy in Teal and Modern: *"the neighborhood in which your prospective
   property is located"* → address the reader as the owner.
4. **Keep** APN, county, legal description, tax and assessment — those are informative and
   expected. It is the *name* and the *framing* that come out.

**If an internal-use variant exists** where the owner block is intentional, gate it to that
context rather than deleting the capability. Check before removing.

**Acceptance:** grep the property templates for owner-name fields returns only gated uses. Render
all five themes and confirm no personal name appears. Cite the template and line for each theme.

### A2 — Aerial fallback · E4 · BROKEN

Bold, Classic, Modern and `teal.pdf` render a stock drone photograph of a suburb that is **not the
subject's location** — and Modern and `teal.pdf` drop a location pin on it. Elegant and
`teal_report` render a real Google map of La Verne.

**Investigate before fixing.** Answer:

1. Where does the aerial image come from in each theme? One code path or several?
2. Is the stock photo a deliberate fallback for a failed map fetch, or a fixture that leaked in?
3. Does the same substitution occur on the Range of Sales page? (It appears to.)

**Then fix:** a failed map fetch must fail visibly. A labelled placeholder — "Map unavailable" —
is correct. A plausible photograph of somewhere else, with a pin on it, is not.

**Do not** simply swap the stock asset for a different stock asset.

**Acceptance:** with the map source forced to fail, every theme renders the placeholder. With it
succeeding, every theme renders the real map. Report which themes were on which path before the
fix.

**→ PR. This is the one I want merged fastest.**

---

## P1-B · Email links and compliance · `fix/p1b-email-links`

### B1 — Establish what production actually emits · B19 · BROKEN

Every link in all eight email templates is a placeholder:

```
https://example.com/report.pdf     ← primary CTA
https://example.com/unsubscribe    ← unsubscribe
#                                  ← "Update Preferences"
mailto:affiliate@trendyreports-demo.com
```

**Investigation first, and report before changing anything.** Are these design samples, or is this
what the renderer emits? Render one email through the real pipeline with real data and compare.

If production substitutes correctly, this ticket is closed by evidence and the sample files are
simply samples. If it does not, every scheduled send since January has carried dead links — which
would be a far larger finding than the register currently reflects.

**The unsubscribe link is the one to check first.** Its live counterpart has never successfully
unsubscribed anyone, and the fix merged last week assumed the URL was being generated correctly.

### B2 — `tel:` URI · B21 · WRONG

`href="tel:(213) 309-7286"` — parentheses and spaces. Use `tel:+1XXXXXXXXXX` (digits only, E.164)
with the formatted number as the link *text*.

### B3 — "Update Preferences" · B22 · WRONG

`href="#"` in all eight. Either point it at a real preference centre or remove the link. A dead
preference link beside a working unsubscribe pushes people toward unsubscribing.

**If no preference centre exists**, remove it and note that as the reason.

### B4 — Contact block · B23 · ROUGH

- The agent's email renders as the word "Email" — show the address.
- Default title is `Realtor`. REALTOR® is a restricted NAR certification mark. If it's a template
  default, change to "Real Estate Agent". If it comes from a user profile field, leave it and say
  so.

### B5 — Postal address · B20 · BROKEN · **GATED**

CAN-SPAM requires a physical postal address in commercial email. The footer has none.

**Decision 09 is unanswered.** Build the footer slot, wire it to a config value, and leave the
value unset with a clear TODO. Do not invent an address. Note it in the PR as blocked.

**Acceptance:** grep across all eight templates for `example.com`, `href="#"`, and `tel:(` returns
zero hits, or the B1 investigation shows they never reach production and that's documented.

**→ PR.**

---

## P1-C · Email rendering · `fix/p1c-email-rendering`

### C1 — Mobile classes attached to nothing · B4 · BROKEN

`.mobile-stack`, `.metric-card` and `.band-row` are defined in the `@media (max-width: 600px)`
block and applied to **zero elements** in all eight templates. The four-across metric strip never
stacks; 10px labels wrap to three lines at ~75px wide.

Attach the classes to the actual cells. **Highest-impact single fix in the pack** given mobile
open share.

**Acceptance:** confirmed stacking on a real Android device or a client-testing service, not in a
browser at a narrow viewport. Browser rendering does not predict Gmail.

### C2 — Contrast failure in Open Houses · B3 · BROKEN

Quick Take label is `#1D4ED8` on a `#DC2626` panel — measured **1.4:1**.

Interim fix now: use a color that passes against that panel. The panel is removed entirely in
Workstream C's rebuild, so do not over-invest — but 1.4:1 is shipping today.

### C3 — Price band bars misrepresent the data · B6 · WRONG

Bars are normalised to the largest band while labels show share of total, so Move-Up reads **43%
beside a bar filled to 100%**. Bar width must equal the percentage shown.

### C4 — Dark mode · B11 · FRAGILE

Current state: `color-scheme: light` plus a rule that dark mode must never touch the content card.
Apple Mail honours it; **Gmail Android force-inverts anyway**, producing an undesigned mid-grey
card. Separately, the `.dark-*` classes that do exist are applied to about four elements per email
— so treated and untreated regions won't match after inversion.

Implement a real `prefers-color-scheme` block against the dark neutrals in master plan §3.2, and
apply the classes across the whole template rather than four elements.

**Acceptance:** Gmail Android dark and Apple Mail dark both render the designed palette. Real
devices — this row cannot be tested in a simulator.

**→ PR.**

---

## P1-D · Placeholder and fallback handling · `fix/p1d-placeholders`

One ticket because they are one problem: **the templates render a container whether or not the
data exists.**

### D1 — "Footer Logo" · B2 · BROKEN

The literal string `Footer Logo` renders in a teal box on every page of every market report PDF,
beside the agent's contact details.

Implement the §3.6 fallback: uploaded logo at 28px optical height, or the company name in
letterspaced caps at the same optical size. Never the label.

**Also:** the email carries the company mark in both header and footer of a 600px layout. One logo
per document.

### D2 — Missing listing photo · B5 · BROKEN

Two different undesigned failures in the same suite: a broken-image glyph with alt text
`Property` printed beside it (`price_bands`), and a blank grey box (1068 Cedar Ct, all eight
reports).

One labelled placeholder: hatched fill, camera glyph, "Photo pending". Same treatment everywhere.

### D3 — Missing agent headshot · E14 · BROKEN

All five property themes render an empty shape — navy square, grey circle, empty gold ring, or
nothing at all. The property report cover also renders `Real Estate Professional •` with a
trailing bullet and nothing after it, and phone/envelope glyphs with no values beside them.

**Conditional rendering.** No data, no element, no separator. Where a headshot is genuinely
expected, use initials in a circle rather than an empty shape.

### D4 — Empty cell as bare hyphen · B12 · ROUGH

Renders `-`. Use "no data" in muted type. A hyphen is ambiguous — it reads as zero, or as an em
dash, or as a rendering fault.

Also: the status chip sits on the photo in gallery layouts and past the price in list rows. Pick
one position.

**Acceptance:** with a fixture that has no logo, no photo, no headshot and null fields, every
surface renders a designed state. Show the render.

**→ PR.**

---

## P1-E · Data contract · `feat/p1e-data-contract`

**Largest ticket in the pack, and the one that closes the most.** Master plan §09 is the spec.

Closes **B1, B7, B8, B14** and structurally prevents **E3, E5, E6, E7**.

### E1 — Implement the shape

Every report returns exactly the structure in §09. No report may render a figure not in it, and
**copy generation receives this dict, not a separate query.**

That last clause is the actual fix for B1 and B8. `117` appearing as the masthead figure on all
eight reports while the insight says "thirty-eight homes closed" and the caption says "all 50"
means three sources are in play.

**Before implementing, answer decision 03:** where does the generated commentary get its numbers
today? If it runs a separate query or a separate prompt, that coupling is the fix. Report the
current path before writing code.

### E2 — Render-time assertions

All nine from §09, including the four added for the property report. Assertion 1 is the important
one: **fail the render** if generated copy contains a figure absent from `headline` or `metrics`.
A wrong number in a client document is worse than a late send.

Assertion 4's pattern is extended — it must also catch `123 Main St` and `example.com`.

### E3 — Prove it closes the register items

For each of B1, B7, B8, B14, E3, E6: demonstrate the defect reproduces against the current code
and does not against the contract. Same standard as the C4 regression test from the security work
— **run it, don't reason about it.**

**Acceptance:** the nine assertions exist with tests. A report with a deliberately mismatched
figure fails to render. Price Bands bands sum to the stated total or the discrepancy is labelled.

**→ PR.**

---

## P1-F · Report copy and labels · `fix/p1f-report-copy`

Small, independent, low-risk.

### F1 — Generation date · B17 · ROUGH

No market report carries one. "Last 30 days" is relative with no anchor — a client who saves the
PDF cannot tell when it was produced.

Date on page 1 and in every page footer. The property report's Market Trends source line
("Generated Mar 3, 2026") is the right pattern — apply it more prominently.

### F2 — Redundant badges · B18 · ROUGH

Every card in Featured Listings is tagged `FEATURED`; every card in Open Houses, `OPEN HOUSE`;
every card in New Listings Gallery, `NEW`. The title already said it.

Badges only where the value varies between cards. **Market Snapshot does this correctly** —
ACTIVE / PENDING / CLOSED differs per card and carries information. Follow that.

### F3 — Closed Sales missing sale date · B16 · WRONG

For a closed comp, **date sold** is a primary field and it isn't in the table. Add it.

Separately: the DOM column runs 3, 6, 9 … 87 then restarts at `-`, 3, 6. Investigate whether
that's fixture cycling or a real data fault, and report which. **Do not fix it blind.**

### F4 — Filter line contradiction · B13 · WRONG · **investigate only**

Every page reads `2+ beds, SFR, under $1.5M (First-Time Buyer)` while listing properties at
$1,762,500 · $1,837,500 · $1,912,500. Price Bands renders a **"$1.5M+" band** under an "under
$1.5M" filter.

**Determine which is true:** the filter is applied and the chip is stale, or the chip is right and
the filter isn't being applied. These have very different severities — the second means saved
search criteria are being ignored.

**Report; do not fix in this branch.** If the filter isn't applied, that's its own ticket.

**Acceptance:** F1–F3 rendered and shown. F4 answered with evidence.

**→ PR.**

---

## Not in Phase 1

| Item | Why deferred |
|---|---|
| **B9** masthead repetition, page fill | Workstream D architecture — needs the pagination baseline reconciled (decision 11) |
| **B10** commentary attribution | **Decision 10** — liability question, not a design one. Do not implement as v1 specified |
| **B15** inventory showing closed-sale metrics | Needs the §10 report matrix decided; it's a product change |
| **E2** comps 3–4 years old | **Decision 08** — query fix or copy fix, unknown which |
| **E3, E5–E22** property report | Workstream E, blocked on decisions 07 and 08 |
| All Workstream A / C / D design work | Phase 2+ |

---

## Kickoff

```markdown
Read DELIVERY_SURFACES_MASTER_PLAN.md, then this ticket pack. §0 Rules of
Engagement from EXECUTION_PLAN_2026-08-17.md still governs everything.

Six branches, no interdependencies. Start with P1-A — both items are on
documents reaching consumer leads today.

Standing rules for this pack:
- The templates are the spec. The PDFs and emails I reviewed are renders.
  Locate the template before fixing anything and confirm the finding is in
  the source.
- Two render generations exist (master plan §02). If a fix behaves differently
  across themes, stop and report rather than fixing one and assuming.
- Several tickets are investigate-first: A2, B1, F3, F4. Report before changing.
- Decisions 07, 08 and 09 are unanswered. Where a ticket is gated, build the
  slot and leave the value unset with a TODO. Never invent a value.

Full self-review block after each ticket, including UNCERTAIN ABOUT.

Report after P1-A before starting P1-B.
```
