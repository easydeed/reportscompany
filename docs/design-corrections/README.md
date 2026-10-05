# Corrections for Claude Design — 2026-10-05

Three documents. **Read `00-SHARED.md` first**: the mistakes in it appear in both handoffs, and
fixing them per-surface is how two surfaces end up with two different greens.

| | |
|---|---|
| **`00-SHARED.md`** | `#8A8E95` is 3.29:1, not ≥4.5 · small white text on a brand fill · the status-badge construct, one answer for both · where the live templates are |
| **`01-PROPERTY.md`** | the design survives; the implementation notes point at dead files. Six rows with no producer, a field that never reaches the renderer, and `COMP_SET_MAX = 15` against a page that holds six |
| **`02-MARKET.md`** | one decision — the running head — stated with its measurement. Plus page-1 capacity, and the news that this surface is at 1.3% failing |
| **`03-SEND.md`** | the cover note: what to read in what order, the type-mapping question that blocks the market work, and where we were wrong |

Both packages are correction lists, not redos. Each document leads with what the handoff got
right, because most of it is.

**Source review:** `../DESIGN_HANDOFF_REVIEW_2026-10-01.md`.
**Standards:** `../CLAUDE_DESIGN_HANDOVER.md`.
**Open product decision referenced by both:** `../JERRY_PROPERTY_FIELDS_DECISION.md`.

Every number here was measured on 2026-10-05 with `scripts/measure_contrast_by_pixel.py` or
computed directly, not quoted from an earlier write-up. Doing it that way caught two numbers in
our own defect list that were wrong, and one we had already sent to Design.
