# 17 always-empty fields on the Property Information page — one decision, three options

**For:** Jerry · **Date:** 2026-10-01 · **Engineering ref:** D-135

---

## The decision in one sentence

17 fields on the Property Information page render a dash on **every** report, because
nothing in the pipeline produces them — and **"we do not collect this" and "this parcel has no
value recorded" look identical on the page and mean different things to a seller.**

We can source them, label them, or remove them. We should not leave them as they are, because
as they are the page says the third thing: *we looked this up and found nothing*, which is not
what happened.

---

## Why they are empty

The property blob is written by exactly two things: SiteX's `PropertyData` model (28 fields) and
the report wizard's payload (25 fields). The builders read **41** fields off it. Nineteen are
read and produced by neither — not "sometimes missing", **never present**.

This was not visible before because a missing value renders a dash, and a dash looks like a
property-level gap rather than a pipeline-level one. It was found by diffing the readers against
the producers mechanically, and the diff is now a test that fails if the list changes in either
direction.

Two of the nineteen are already settled and are **not** part of this decision:

* **`mailing_address`** — deliberately excluded. For an absentee owner it is where a person
  lives, not a fact about the property.
* **`estimated_value`** — that is the estimated-range work, a separate decision.

**17 remain.**

---

## The three options

### A · Source them

Get the data and fill the fields.

* **Cost:** a vendor conversation per group. SiteX may already return several of these under
  names we do not parse — `zoning`, `use_code`, `total_rooms`, `num_units` and `tax_status` are
  the plausible ones, and finding out is one read-only credential trip, not a project.
* **Buys:** a Property Information page that is actually full, which is the page agents say sells
  the product.
* **Risk:** we would be paying for, or parsing, fields nobody has asked for. **This is the only
  option where the first step is a measurement rather than a decision** — we can find out what
  SiteX already answers before committing to anything.

### B · Label them

Keep the rows and say what the dash means — *"not collected"* rather than an unexplained dash.

* **Cost:** a copy change, one line per theme.
* **Buys:** the page stops making a claim it cannot support. Honest.
* **Risk:** 17 rows reading "not collected" is a page advertising what we do not have. It
  is the most truthful option and the worst-looking one.

### C · Remove them

Delete the rows. The page keeps APN, county, legal description, tax and assessment, beds, baths,
square footage, year built, lot size — the ones that are real.

* **Cost:** one change, five templates, no data work.
* **Buys:** a shorter page where every row has a value. **This is what a reader would call a
  better document.**
* **Risk:** if we source any of them later, the row has to come back — and a field that is
  sometimes present and sometimes absent is a worse design problem than one that is always
  absent, because then the dash *is* meaningful.

---

## The 17

Grouped by what they are, because the answer is probably not the same for all of them.

| group | fields | comment |
|---|---|---|
| **Plausibly available from SiteX** | `zoning`, `use_code`, `total_rooms`, `num_units`, `tax_status`, `tax_rate_area` | worth one read-only probe before deciding anything else |
| **Parcel-map detail** | `census_tract`, `housing_tract`, `lot_number`, `page_grid` | surveyor-grade; a seller is unlikely to want them and an agent might |
| **Building features** | `garage`, `fireplace`, `stories`, `partial_bath`, `pool` | the ones a buyer asks about, and the ones we are most visibly missing |
| **Derived** | `percent_improved` | computable from land value ÷ improvement value **when both are present**, which is its own gap |
| **Free text** | `notes` | no source, no obvious meaning, and the easiest removal |

---

## What I recommend, and what I am not deciding

**My recommendation is: probe first, then C for whatever the probe does not answer.**

The probe is cheap and read-only and it changes which option is even available for six of the
17. Deciding between B and C before knowing whether SiteX answers `zoning` is choosing in
the dark, and we have been caught by exactly that pattern twice this month — a field reported
absent because we looked in the wrong place, and a product decision filed against it.

**What is not mine to decide** is whether an empty Property Information row is a problem worth
solving at all. If agents never mention it, C is free and A is wasted money. You know that and I
do not.

**One thing that is time-sensitive:** Claude Design is about to redesign this surface. A designer
who does not know these rows are permanently empty will give them equal weight to the APN, and
we will have paid for a layout built around a block that is two-thirds dashes. The handover
document says so explicitly, but **an answer before the redesign starts is worth more than an
answer after it.**
