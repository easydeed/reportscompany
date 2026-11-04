# Edits to `apps/worker/src/worker/templates/property/_v2/report.jinja2`

Cut against `main` @ `35e6e6db` (fetched 2026-11-04 01:00 UTC; 43,632 bytes). Each edit is an exact-string replacement; every `before` occurs exactly once in that file. `apply_touches.py --check <path>` confirms they still apply to whatever you have before writing anything. Nothing outside these strings changes.

Rules kept on every edit: six pages, same order; no brand colour moved; derived inks on brand; no text on gradients or photos; dashes untouched; no new colour (every pairing introduced already exists in the baseline under another selector).

---

## T1 — "Prepared for" name no longer orphans its last word

**Page:** 1 · cover

**Why:** "The owners of 1358 5th Street" broke as "…1358 5th / Street" in the 200px column on all three renders. 20px instead of 22 and `text-wrap: balance` split it "The owners of / 1358 5th Street"; the note below gets `pretty` for the same reason ("Prepared at the request of Zoe / Noelle"). Column width is unchanged so "In short" keeps its measure. Colour untouched.

**Before**
```
  .cover-for-name { font-family: var(--display); font-weight: var(--display-weight); font-size: 22px; line-height: 1.15; letter-spacing: var(--display-tracking); }
  .cover-for-note { font-size: 13px; color: var(--muted); }
```

**After**
```
  .cover-for-name { font-family: var(--display); font-weight: var(--display-weight); font-size: 20px; line-height: 1.15; letter-spacing: var(--display-tracking); text-wrap: balance; }
  .cover-for-note { font-size: 13px; color: var(--muted); text-wrap: pretty; }
```

---

## T2 — "In short" ends on an ellipsis, not a sliced line

**Page:** 1 · cover

**Why:** `max-height: 81px; overflow: hidden` cut the paragraph through its x-height on harbor, where Manrope sets the ~380-character narrative to four full lines plus a fifth. `-webkit-line-clamp` ends on "…" at a word boundary. Five lines (101px) rather than four: the hero plate above is `flex: 1` with a 300px floor and measures ~440px on the fixture, so the 20px comes out of the photo, never the page. The generation cap stays the primary bound.

**Before**
```
  /* Four lines, bounded. The only other thing on page 1 that grows with data
     is the title, and the ladder bounds that. */
  .inshort-text { margin: 0; font-size: 13.5px; line-height: 1.5; color: var(--body); max-height: 81px; overflow: hidden; }
```

**After**
```
  /* Five lines, bounded, ending on an ellipsis at a word boundary rather
     than a line sliced by max-height. The only other thing on page 1 that
     grows with data is the title, and the ladder bounds that. */
  .inshort-text { margin: 0; font-size: 13.5px; line-height: 1.5; color: var(--body); display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 5; overflow: hidden; }
```

---

## T3 — One name for the document

**Page:** all · running head

**Why:** The running head said "Property report" on every page while the cover's masthead said "Seller's report" or "Home value report" — two titles on one sheet, and the consumer copy named a kind the funnel never offered. `doc.report_kind` is already the masthead's value.

**Before**
```
    <span class="runhead-address">Property report · {{ doc.street }}</span>
```

**After**
```
    <span class="runhead-address">{{ doc.report_kind }} · {{ doc.street }}</span>
```

---

## T4 — "Not on record" reads as a caption, not a warning

**Page:** 2 · your home

**Why:** A bold label sharing one line with thirteen field names read as a paragraph of warning. Label above the list in the page's own label voice (10.5px caps), list at 11.5px. Same panel, same colour (`--muted` on `--strip`, already in the baseline).

**Before**
```
  .notonrecord { display: flex; gap: 14px; align-items: baseline; padding: 14px 16px; background: var(--strip); border-radius: var(--radius); font-size: 12px; line-height: 1.5; color: var(--muted); }
  .notonrecord-label { font-weight: 700; white-space: nowrap; }
```

**After**
```
  .notonrecord { display: flex; flex-direction: column; gap: 4px; padding: 12px 16px 13px; background: var(--strip); border-radius: var(--radius); font-size: 11.5px; line-height: 1.5; color: var(--muted); }
  .notonrecord-label { font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase; font-weight: 600; white-space: nowrap; }
```

---

## T5 — The grid fits the number of comps

**Page:** 3 · comparable sales

**Why:** Six cells for four comps left the second row two-thirds empty on every fixture render. Quantity selectors, so no builder change: 5–6 comps keep 3×2; 4 comps go 2×2; 1–3 comps sit in one top-aligned row with plates at 4:3 so three tall slivers do not stretch to the footer. `:has()` is supported by the Chromium PDFShift renders with.

**Before**
```
  .comp-grid { flex: 1; min-height: 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); grid-template-rows: repeat(2, minmax(0, 1fr)); gap: 20px 16px; }
  .comp { display: flex; flex-direction: column; min-height: 0; }
```

**After**
```
  .comp-grid { flex: 1; min-height: 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); grid-template-rows: repeat(2, minmax(0, 1fr)); gap: 20px 16px; }
  /* The grid fits the count. 5–6 comps: 3 × 2 as designed. 4 comps: 2 × 2,
     no empty cells. 1–3 comps: one top-aligned row, plates at 4:3. Quantity
     selectors — the template counts its own children. */
  .comp-grid:has(.comp:nth-child(4):last-child) { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .comp-grid:has(.comp:nth-child(3):last-child),
  .comp-grid:has(.comp:nth-child(2):last-child),
  .comp-grid:has(.comp:first-child:last-child) { grid-template-rows: none; align-content: start; }
  .comp-grid:has(.comp:nth-child(3):last-child) .comp-plate,
  .comp-grid:has(.comp:nth-child(2):last-child) .comp-plate,
  .comp-grid:has(.comp:first-child:last-child) .comp-plate { flex: none; aspect-ratio: 4 / 3; }
  .comp { display: flex; flex-direction: column; min-height: 0; }
```

---

## T6 — A missing-photo tile says how far away the sale is

**Page:** 3 · comparable sales

**Why:** All four tiles read "La Verne / NO PHOTO ON FILE" — four copies of one tile. `comp.v2_dist` ("0.24 mi") is already on the comp; shown in the same display slot over "FROM YOUR HOME · NO PHOTO ON FILE", the tiles differ and lead with the number a seller asks about first. City falls back in only when the distance is itself a dash. Same tokens (`primary_ink` on `tint`), same position, no CSS change.

**Before**
```
          <div class="comp-nophoto">
            <span class="comp-nophoto-name">{{ comp.neighborhood or doc.city_name }}</span>
            <span class="comp-nophoto-note">No photo on file</span>
          </div>
```

**After**
```
          <div class="comp-nophoto">
            {# Distance from the subject where it is known; the city only when
               the distance is itself a dash. #}
            {% if comp.v2_dist and comp.v2_dist != '-' %}
            <span class="comp-nophoto-name">{{ comp.v2_dist }}</span>
            <span class="comp-nophoto-note">From your home · no photo on file</span>
            {% else %}
            <span class="comp-nophoto-name">{{ comp.neighborhood or doc.city_name }}</span>
            <span class="comp-nophoto-note">No photo on file</span>
            {% endif %}
          </div>
```

---

## T7a — Range caption — the style

**Page:** 4 · what the comps support

**Why:** Replaces `.band-axis-mid` (centred middle item of a space-between row) with a row of its own under the axis, in which the caption is absolutely positioned at the marker's x. Same `#fff`, 600, 11px on `--dark`; the pairing is already in the baseline under the old selector.

**Before**
```
  .band-axis-mid { color: #fff; font-weight: 600; }
```

**After**
```
  /* The marker's caption, under the marker. A row of its own: left-anchored
     in the first 30% of the axis, right-anchored in the last 30%, centred
     between — so the ▲ points at the marker whatever its position. */
  .band-you { position: relative; height: 17px; margin-top: 2px; font-size: 11px; color: #fff; font-weight: 600; }
  .band-you-text { position: absolute; top: 0; white-space: nowrap; }
```

---

## T7b — Range caption — the markup

**Page:** 4 · what the comps support

**Why:** On the fixture the subject's last sale sits at 2% of the axis and the centred "▲ your home's last recorded sale" pointed at nothing. The axis row now carries only low and high; the caption gets its own row anchored at `subject_x`. Adds 19px inside the range panel; page 4 has ~110px of slack under the bars on the fixture, and the 15-comp case already runs `bar_height` 14 / `bar_gap` 5.

**Before**
```
        <div class="band-axis" style="margin-top:6px">
          <span>{{ doc.axis_low }}</span>
          {% if doc.subject_x is not none %}
          <span class="band-axis-mid">▲ your home's last recorded sale · {{ doc.last_sale_label }}</span>
          {% endif %}
          <span>{{ doc.axis_high }}</span>
        </div>
```

**After**
```
        <div class="band-axis" style="margin-top:6px">
          <span>{{ doc.axis_low }}</span>
          <span>{{ doc.axis_high }}</span>
        </div>
        {% if doc.subject_x is not none %}
        <div class="band-you">
          {% if doc.subject_x < 30 %}
          <span class="band-you-text" style="left:{{ doc.subject_x }}%">▲ your home's last recorded sale · {{ doc.last_sale_label }}</span>
          {% elif doc.subject_x > 70 %}
          <span class="band-you-text" style="right:{{ 100 - doc.subject_x }}%">▲ your home's last recorded sale · {{ doc.last_sale_label }}</span>
          {% else %}
          <span class="band-you-text" style="left:{{ doc.subject_x }}%;transform:translateX(-50%)">▲ your home's last recorded sale · {{ doc.last_sale_label }}</span>
          {% endif %}
        </div>
        {% endif %}
```

---

## T8a — Empty chart — the style

**Page:** 5 · your market

**Why:** The one-line note sat under the chart heading and the chart's `flex: 1` left ~400px of white below it — reads as a failed render. The note now fills the chart's area on `--strip`, centred, radius per theme, same muted type. `--muted` on `--strip` is the `.notonrecord` pairing, already in the baseline. `margin-bottom: 24px` matches the `.chart-xaxis` padding the chart would otherwise end with.

**Before**
```
  .chart-empty { margin: 0; padding: 24px 0; font-size: 12px; line-height: 1.5; color: var(--muted); }
```

**After**
```
  /* A designed empty state: fills the chart's area rather than leaving it
     white under a one-line note. */
  .chart-empty { margin: 0 0 24px; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; text-align: center; padding: 24px 72px; background: var(--strip); border-radius: var(--radius); font-size: 12.5px; line-height: 1.55; color: var(--muted); text-wrap: pretty; }
```

---

## T8b — Empty chart — the copy

**Page:** 5 · your market

**Why:** Names the city and the window the four figures above were measured over, so the page still closes on a fact. Both values are already in context (`doc.city_name`, `market_trends.window_label`, e.g. "Last 90 Days").

**Before**
```
      <p class="chart-empty">Not enough recorded sales to chart a monthly median for this area.</p>
```

**After**
```
      <p class="chart-empty">Not enough recorded sales in {{ doc.city_name }} to chart a monthly median. The four figures above are measured over the {{ market_trends.window_label | lower }} of closed sales.</p>
```

---

## T9a — Tap-to-call — the style

**Page:** 6 · next steps + footer

**Why:** Links inherit the colour of the text they sit in and carry no underline, so the anchors in T9b/T9c are pixel-identical to the spans they replace. Placed directly after the `body` block.

**Before**
```
    font-variant-numeric: lining-nums;
  }

  /* 8.5 x 11in at 96dpi.
```

**After**
```
    font-variant-numeric: lining-nums;
  }
  /* Links carry the colour of the text they sit in and no underline: the
     phone and email on page 6 and the footer phone are tap-to-call in the
     PDF and must look exactly as they did as spans. */
  a { color: inherit; text-decoration: none; }

  /* 8.5 x 11in at 96dpi.
```

---

## T9b — Tap-to-call — agent panel

**Page:** 6 · next steps

**Why:** A PDF opened on a phone — where the consumer copy is opened — keeps `tel:` and `mailto:` links. The `tel:` value is the display phone with spaces, parentheses, dashes and dots stripped; a leading `+` survives.

**Before**
```
        <span class="agentpanel-phone">{{ agent.phone }}</span>
        <span class="agentpanel-email">{{ agent.email }}</span>
```

**After**
```
        <a class="agentpanel-phone" href="tel:{{ agent.phone | replace(' ', '') | replace('(', '') | replace(')', '') | replace('-', '') | replace('.', '') }}">{{ agent.phone }}</a>
        <a class="agentpanel-email" href="mailto:{{ agent.email }}">{{ agent.email }}</a>
```

---

## T9c — Tap-to-call — footer phone

**Page:** all · footer

**Why:** Same link on the footer phone, every page. Colour inherits `--muted` from `.pagefoot-brand`; nothing visible changes.

**Before**
```
    <span><span class="pagefoot-agent">{{ agent.name }}</span><span class="pagefoot-brand"> · {{ agent.company_name }} · {{ agent.phone }}</span></span>
```

**After**
```
    <span><span class="pagefoot-agent">{{ agent.name }}</span><span class="pagefoot-brand"> · {{ agent.company_name }} · <a href="tel:{{ agent.phone | replace(' ', '') | replace('(', '') | replace(')', '') | replace('-', '') | replace('.', '') }}">{{ agent.phone }}</a></span></span>
```

---

## What the checks will see
- **Contrast** — new selectors, no new pairings: `span.band-you-text` (#fff on #0f172a — was `span.band-axis-mid`), `p.chart-empty` (#5E636B on #F6F6F3 — the `.notonrecord` pairing), `a.agentpanel-phone` / `a.agentpanel-email` / footer `a` (inherit; same values as the spans). `span.band-axis-mid` leaves the baseline.
- **Page fit** — nothing grows past its page. T2: ≤20px into the cover grid, absorbed by the hero plate's `flex:1` (300px floor, ~440px on the fixture). T7: +19px inside the range panel; ~110px slack on the 4-comp fixture; if a 15-comp render is tight, set `.band-you` height to 15px. T8: replaces a 48px note with a flex child — net zero. T5: changes the shape of the comps grid, not its height.
- **Fonts** — none added.
- **Page count** — unchanged.
- **Tests** — T3 changes the running-head literal; grep of `apps/worker/tests/` found nothing asserting `Property report ·`. `cover_brand_sweep.json` keys on `p.inshort-text`, which keeps its selector and colours.
