# Property report — final visual touches

Date: 2026-11-03 · Reviewed against: `uploads/property__{atlas,harbor,linen}__full.pdf` (1358 5th Street, La Verne; agent path; 4 closed comps, no comp photos, no monthly chart) and `apps/worker/src/worker/templates/property/_v2/report.jinja2` @ `35e6e6db`.

Deliverable: **edits, not a file.** `EDITS.md` lists each touch T1–T9 as an exact-string replacement against `property/_v2/report.jinja2` on `main` @ `35e6e6db` — what it changes, the lines before and after, and why. `touches.json` is the same list machine-readable; `apply_touches.py --check <path>` verifies every `before` still occurs exactly once in your copy and writes nothing unless all do. Nothing outside those strings changes. Theme entry files, builder, tests: untouched.

Rules kept: six pages, same order; no new pages; no brand colour moved; text on brand uses the derived inks; no text on gradients or photos; dashes untouched; no estimate outside the range panel. No new colour anywhere — every pairing introduced already exists in the baseline under another selector.

---

## The prompt, filled in

```markdown
Final visual touches on the reports — no structural changes.

What I'd like improved, page by page:

  Page 1 · cover
  - "Prepared for / The owners of 1358 5th Street" breaks as "…1358 5th / Street"
    — an orphan under the most personal line on the cover. Same on all three themes.
  - "In short" is sliced mid-line on harbor: Manrope runs the paragraph to four
    full lines and the fifth is cut through its x-height by the 81px cap.
  - The running head says "Property report" while the masthead says "Seller's
    report" / "Home value report". Two titles on one sheet.

  Page 2 · your home
  - "Not on record" reads as a bold warning sentence with thirteen field names
    run on. It is a caption.

  Page 3 · comparable sales
  - Four comps in a six-cell grid: the second row is two-thirds empty.
  - All four tiles say "La Verne / NO PHOTO ON FILE" — four copies of one tile.

  Page 4 · what the comps support
  - The "▲ your home's last recorded sale" caption is centred under the axis
    while the marker sits at 2% — the arrow points at nothing.

  Page 5 · your market
  - With no monthly series the page is a one-line note over ~400px of white.
    Reads as a failed render.

  Page 6 · next steps
  - Phone and email are plain text. On a phone (where the consumer copy is
    opened) they should be tap-to-call / tap-to-write.
```

---

## The nine touches

| # | Page | Site | Touch | What it does |
|---|---|---|---|---|
| T1 | 1 | `.cover-for-name`, `.cover-for-note` | 22→20px; `text-wrap: balance` on the name, `pretty` on the note | "The owners of / 1358 5th Street" — two even lines, no orphan. Column stays 200px so "In short" keeps its width. |
| T2 | 1 | `.inshort-text` | `max-height/overflow` → `-webkit-line-clamp: 5` | Paragraph ends on "…" at a word boundary instead of a half-cut line. Five lines, not four: the hero plate is `flex:1` with a 300px floor and measures ~440px on the fixture, so the 20px comes out of the photo, never the page. The ~380-char generation cap remains the primary bound. |
| T3 | all | `.runhead-address` | `Property report` → `{{ doc.report_kind }}` | "Seller's report · 1358 5th Street" / "Home value report · …" — one name for the document, matching the masthead. |
| T4 | 2 | `.notonrecord` | Column layout; label in the page's label voice (10.5px caps, muted) over the list at 11.5px | Reads as a caption, not a sentence. Same panel, same colours. |
| T5 | 3 | `.comp-grid` | Quantity selectors via `:has()`: 4 comps → 2×2; 1–3 → one row, plates at 4:3, row top-aligned; 5–6 unchanged | No empty cells. No builder change — the template counts its own children. Chromium (PDFShift) supports `:has()`. |
| T6 | 3 | `.comp-nophoto` | Tile shows `comp.v2_dist` ("0.24 mi") in display type over "FROM YOUR HOME · NO PHOTO ON FILE"; city only when distance is a dash | Four tiles that differ and say the thing the card below doesn't lead with. Same tokens (`primary_ink` on `tint`). |
| T7 | 4 | `.band-you` (new row) | Caption moves out of the axis row into its own row, anchored at `subject_x`: left-aligned <30%, right-aligned >70%, centred between | The ▲ sits under the marker it describes. Axis row now carries only low / high. Same `#fff` 600 11px. |
| T8 | 5 | `.chart-empty` | Fills the chart's `flex:1` area on `--strip`, centred, radius per theme; copy names the city and the window the four figures were measured over | A designed empty state. The page closes on a fact ("…measured over the last 90 days of closed sales") rather than a gap. |
| T9 | 6 + footer | `.agentpanel-phone`, `.agentpanel-email`, footer phone | `span` → `a` with `tel:` / `mailto:`; `a { color: inherit; text-decoration: none }` | Tap-to-call / tap-to-write in the PDF. Pixel-identical. `tel:` digits are the display phone with spaces, parens, dashes and dots stripped. |

### What the checks will see
- **Contrast**: no new `(fg, bg)` pairing. New selectors that will appear as baseline entries: `span.band-you-text` (`#fff` on `#0f172a`, same as the old `.band-axis-mid`), `p.chart-empty` (`#5E636B` on `#F6F6F3` — the `.notonrecord` pairing, already in the baseline), `a.agentpanel-phone` / `a.agentpanel-email` / footer `a` (inherit; same values as the spans they replace), `span.comp-nophoto-name` unchanged pairing at 22px instead of 20.
- **Page fit**: nothing on any page grows. T2 adds ≤20px to the cover grid, absorbed by the hero plate's `flex:1`. T7 adds a 19px row inside the range panel; page 4 on the fixture has ~110px of slack under the bars (measure on a 15-comp render: `bar_height` 14 / `bar_gap` 5 already compress it — if tight, drop `.band-you` `height` to 15px). T8 replaces a 48px note with a flex child — net zero.
- **Fonts**: no new faces or weights.
- **Page count**: unchanged.
- **Tests likely to need a one-line update**: any that asserts the literal `Property report ·` in the running head (T3). None found under `apps/worker/tests/` by grep; `cover_brand_sweep.json` keys on `p.inshort-text` and stays valid.

---

## Left on the table

Things the document could carry that it does not. None are in the diff — each needs a producer or an owner decision. Ordered by what it would do for the reader.

### Information
1. **Comp photos.** All six photo sites on page 3 were empty on the fixture: no `photo_url` AND no `map_image_url`. The nearest-six photos are the one piece of imagery in the middle of the document. Check the photo proxy and the static-map key before anything else here — zero design work, biggest visual lift. (Also the ≥1080px source note from the email/social package.)
2. **Over / under asking, per closed comp.** `list_price` and `sale_price` are already on every comp dict. "Sold 3% over asking" is the single most persuasive line a seller reads, and the market page already shows the aggregate (sale-to-list). Spec: builder sets `c["v2_vs_ask"]` — `list_price` 0/absent → omit; within ±0.5% → "at asking"; else "`N`% over asking" / "`N`% under asking", integer. Template: fourth `.comp-line`, and the compare table gains no row (five rows is the fit).
3. **Days on market, per comp.** Present as `days_on_market` but the producer collapses unknown to 0, and 0 renders "New" (D-137 note in the builder). Needs the `_known` treatment first; then "Sold Jul 2026 · 12 days" on the third line.
4. **Page 2 column balance.** The home: 8 rows. Record & taxes: 11 (agent) / 10 (consumer). Garage is a home attribute listed under Record & taxes — moving it (builder list edit, one line) gives 9/10 and 9/9. Stories and Pool are already on the left.
5. **"In short" vs. page 3 disagree on the window.** The narrative says "over the past year"; the comps page says "last 6 months". The AI narrative prompt should receive `comps_window.pill`.
6. **Monthly median chart is `None` for a city the size of La Verne.** T8 makes the empty state deliberate; it is still empty. Consider a ZIP/radius fallback or a 12-month window before the chart gives up.

### Marketing
7. **A scannable way back to the agent.** The agent panel on page 6 has room beside the phone pill for a 72px QR to `sms:{phone}` (agent path) or to the agent's home-value page (consumer path). Needs `agent.qr_url` from the builder (any static QR generator or a `qrcode` PNG uploaded to R2). New element on an existing page — your call whether that counts as structural; I'd ship it.
8. **Agent headshot and logo.** The fixture renders initials in the avatar and the company name as text in the masthead — both slots exist, both are empty. An onboarding nudge ("add a photo — it appears on every report") is worth more than any template change.
9. **The consumer "Prepared for" note** says "Requested from {company} home-value page". Consider "Requested by you on {date}" — the reader knows where they were; the date tells them the report is fresh.
10. **Social/email reuse.** The range panel (page 4) is the natural hero for the home-value email and a story card — same tokens, same copy. Nothing to do here; noting that the email package's `read:insight` block can quote `range_low – range_high` once the estimate question (keep/drop) is settled.

---

## Files
```
design_handoff_property_touchups/
  README.md            this file — what bugged me, the nine touches, left on the table
  EDITS.md             T1–T9 as before/after edits with rationale (human-readable)
  touches.json         the same edits, machine-readable (source for both EDITS.md and the script)
  apply_touches.py     --check verifies all edits apply exactly once; without it, applies them
```
