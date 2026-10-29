# Design handoff — Emails and social share images

Repo: `easydeed/reportscompany` · Prepared 2026-10-28 · Grounded in `apps/worker/src/worker/email/template.py` (REPORT_BLOCKS, the `§06` block environment), `apps/worker/src/worker/themes.py` (`derive_theme`), `apps/worker/src/worker/email/send.py` (per-recipient unsubscribe), `apps/api/src/api/services/email.py` (transactional senders), `apps/web/lib/social-templates.ts` + `apps/web/templates/social/*`.

Open `Emails & Social.dc.html` to see everything on one canvas. Every frame is the actual file.

## What's in the folder

| path | what |
|---|---|
| `emails/market/{kind}.html` × 8 | the market report email, one per `report_type`, built from the ten blocks (below) in the sequence `REPORT_BLOCKS` declares |
| `emails/market/theme-tests/` | the same Snapshot on navy / green / wine / amber / lime, and the no-postal-address footer |
| `emails/home-value/home-value-ready.html` | CMA delivery to a homeowner (+ amber variant) |
| `emails/transactional/*.html` × 12 | one shell, twelve bodies: 3 invites, verify, reset, 4 welcomes, 80%, limit, schedule failure |
| `social/{kind}.html` × 8 | 1080×1920 stories, one per kind (+ amber/lime tests) |

All emails: 600px, tables, every style inline, system font stack, `color-scheme: light dark` with a small dark-mode `<style>` that only adjusts neutrals (the brand fill and its `on_primary` text are left alone so they survive Gmail's inversion). Under 30 KB each. Images are grey placeholder cells with the slot named — swap for hosted `https` URLs.

## Rules applied everywhere

1. **Brand colour is a fill, never text on a light surface.** Text on brand = `on_primary`; brand as text = `primary_ink`; panels = `tint`; the big social number = `primary_ink` on `tint`, never `display_ink` on `primary` (we don't put display text on the fill at all in these surfaces, so `display_ink` isn't needed; see "What changed from the brief").
2. **No gradients, no text on photos.** Masthead and brand bands are solid `primary`. Social photo kinds put the photo in its own 1080×900 region and all text below it on white.
3. **Absence is a dash.** Every number goes through `dash()`; the Snapshot's "Open this weekend" and Inventory's "Price cuts" cells show it on purpose. Never "0", never a default.
4. **CAN-SPAM on anything sent to a list.** Reason line + one-click unsubscribe (the per-recipient URL from `send.py`, `List-Unsubscribe` headers already exist) + postal address. Agent with address: *"Jennifer Realty · 4000 MacArthur…"*. No address on file: *"Sent by TrendyReports on behalf of Jennifer Martinez · 18575 Jamboree Rd…"* — our name appears **only** in that case. Transactional emails carry our address and a one-line reason instead of an unsubscribe; the usage warnings point to Settings → Email me.
5. **One idea per surface.** The email leads with a sentence (the insight) and one number; the social story is the sentence, the number, four cells, and who sent it.

## 1 · Market report email — the ten blocks

Rendered in exactly the names `template.py` uses so the mock maps 1:1 onto `templates/email/blocks/*.jinja2`. `masthead`, `cta`, `signature` are invariant (`INVARIANT_BLOCKS`); the rest follow `REPORT_BLOCKS[report_type]`.

| block | variant(s) | what it is in the design | structural or styling |
|---|---|---|---|
| `masthead` | — | 60px solid `primary` band: brand name (or `header_logo_url` at ≤160×32) left, date right; then the kind · area · period label on white. **No gradient** — `masthead.jinja2` currently takes `accent_color` for one; drop it. | structural (gradient removed; accent no longer used anywhere in the email) |
| `read` | `insight`, `panel` | 25px/800 headline + 15px paragraph. `panel` = headline only (Open Houses, no AI copy). | styling |
| `chrome` | `hero` | the one number, 46px `primary_ink` on a `tint` panel, label + delta line under it | styling (token swap: today's hero uses `_ink` on `#f8fafc`; move to `tint`) |
| | `count_pill` / `section_label` | not a pill — an 11px uppercase sentence: "118 homes sold · the 4 most recent" | styling |
| | `filter_blurb` | one grey line under the hero when `filter_description` exists | styling |
| | `truncation_note` | "Showing 4 of 118. All of them are in the report." centred | styling |
| | `divider` | not used; vertical rhythm comes from padding | styling |
| `spec_list` | `strip` | four 136px cells on `#F8FAFC`, 1px `#ECEAE3` border, 20px value / 11px label; stack on mobile via `.tr-stack` | styling |
| | `supporting` | three cells, no fill, hairline top (Price Bands: days-to-sell per band) | styling |
| `gallery` | `row` | photo-left 120×90, price in `primary_ink`, address, specs; `New` marker as ink chip | styling |
| | `badged` | `row` + status chip: Sold `#065F46`/`#D1FAE5`, Active/Reduced `#475569`/`#F1F5F9` | styling |
| | `plain` / `large` / `compact` / `stacked` | **collapsed into `row` and `grid:rows`.** Six photo sizes was a builder concern; two shapes read better and halve the test surface. | structural |
| `grid` | `rows` | 2-up 264px cards (gallery kinds); `table` shape is just the wrapper for `table` | styling |
| `table` | — | five columns, 2px ink rule under the header, `tint` zebra, price column in `primary_ink` | styling |
| `bands` | — | label + "n homes · median" line, then a two-cell bar (brand / `#ECEAE3`), min 2% | styling |
| `cta` | — | bulletproof button: `primary` fill, `on_primary` text, radius 10; "Open the full report" + "PDF · one page · Irvine, last 30 days" | styling (copy change from "View Full PDF") |
| `signature` | — | agent block (56px initials disc on `primary` / `rep_photo_url`, name, title · brand, phone · email in `primary_ink`), then the footer rules above | structural (footer logic: address present → agent only; absent → "Sent by TrendyReports") |

Block sequence as built (matches `REPORT_BLOCKS` as read on 2026-10-28; `market_snapshot` and `open_houses` entries were partly off-screen — confirm `spec_list:strip` on Snapshot and `read:panel` on Open Houses):

- market_snapshot · new_listings: read:insight → hero → (filter_blurb) → count → gallery:row → spec_list:strip → truncation
- open_houses: read:panel → hero → count → gallery:row → truncation
- closed · inventory: read:insight → hero → count → gallery:badged → table → spec_list:strip → truncation
- price_bands: read:insight → hero → spec_list:supporting → bands → count → gallery:row → truncation
- new_listings_gallery · featured_listings: read:insight → count → grid:rows → truncation

Subject lines stay as `schedule_email_subject` produces them; the preheader is the headline sentence.

## 2 · Home value delivery (`home-value-ready.html`)

Agent-branded (same masthead as the market email, no TrendyReports mark anywhere). Title "Tom, your report is ready." · one paragraph · cover thumbnail (200×259 — a rendered PNG of page 1, hosted) beside the **estimate, range, basis** and the button · "What's inside" four rows · agent card with a sentence and Call / Text buttons · footer: where and when they asked, "one-time email, not a list", agent address, "not an appraisal".

**Decision to confirm:** the estimate is *in the email.* The Home Value Page deliberately withholds the number until contact is given; once it is, holding it back again in the email reads as a bait. If you'd rather the number live only in the PDF, delete the `$1.41M` block and the thumbnail carries the email.

Needs from the API: `estimate`, `range_low/high`, `comp_count`, `radius`, `confidence` label, `cover_png_url`, `pdf_url`, the request `source_url` + timestamp, agent postal address.

## 3 · Transactional shell

Cream page, 600px white card, the Ticker lockup top-left (text + a `#D1FAE5` cell — no image), 26px title, one paragraph, optional body, ink button, footer with **a one-line reason this email exists** + our address + Help. Bodies:

| file | replaces in `services/email.py` | body |
|---|---|---|
| `invite-agent` | `send_invite_email` (from a rep) | title names the rep and the seat; "Take the seat"; 7-day note |
| `invite-rep` | `send_role_invite_email` (affiliate) | company set up a seat; what a rep does |
| `invite-company-admin` | `send_role_invite_email` (admin) | who added you; "Set your password" |
| `verify-email` | `send_verification_email` | "Nothing goes out in your name until…" |
| `password-reset` | `send_password_reset_email` | 1-hour note; "your password is unchanged" |
| `welcome-agent` | `send_regular_agent_welcome_email` | three numbered steps (`_step_row`) |
| `welcome-sponsored-agent` | `send_sponsored_agent_welcome_email` | names the rep; "he sees that reports went out, never what's in them" |
| `welcome-rep` | `send_rep_welcome_email` **and** `send_affiliate_welcome_email` | fold the legacy affiliate welcome into this one |
| `welcome-company-admin` | `send_company_admin_welcome_email` | set the brand → invite reps → dashboard |
| `usage-80` | `send_limit_warning_email` | plan line + amber bar at 80% |
| `usage-limit` | `send_limit_reached_email` | red bar + which schedules are paused |
| `schedule-failed` | new (worker → account owner) | what happened / what you can do; not optional |

Shell = `_email_base`; button = `_cta_button`; steps = `_step_row`. Replace those three and every body inherits.

Needs from the API: for `usage-limit`, the list of schedules that will pause and their next-run dates; for `schedule-failed`, a human reason string per failure class (feed empty · MLS timeout · no recipients) and the recipient count.

## 4 · Social stories (1080×1920)

Two layouts, eight kinds, from the same six placeholders the builders already fill (`{{market_name}}`, `{{median_price}}`, …):

- **Stats** (snapshot, closed, inventory, new listings, price bands): 120px solid `primary` band with brand name + kind · area/period label · 76px headline · hero number (`primary_ink` on `tint`, 210px; 170px when the value is longer than six characters) · 2×2 cells (or three band bars) · 260px ink footer with the agent disc (brand ring), name, contact line, source/date right.
- **Photo** (gallery, featured, open houses): the same band · photo in its own 1080×900 box · count line · 132px price · address · specs · the same footer. Nothing is drawn over the photo.

Font: Plus Jakarta Sans via Google Fonts (headless Chrome renders it; keep `display=swap` off in production so the screenshot waits for the font — or self-host). `Inter` and the two-colour gradient in `templates/social/*` go away; `--pct-accent` is no longer read.

Structural changes to `social-templates.ts`: the headline sentence is new input (`{{headline}}` — the same insight the email's `read:insight` uses; pass it through), the hero needs a `{{hero_sub}}` delta line, and photo kinds need `{{count_line}}`. Everything else is a placeholder that already exists.

Needs from the API: `headline` on the social payload; `hero_photo_url` at ≥1080 wide for photo kinds (the current gallery first-listing photo may be a 640px MLS thumbnail — check).

## What changed from the brief

- **`display_ink` isn't used.** It exists for display text on the brand fill. These surfaces never put the big number on the fill — it sits on `tint` in `primary_ink`, which clears 4.5:1 on every brand by construction. The amber and lime tests show why: white on amber is 2.15:1, and `display_ink` would pick near-black there, which reads as a different brand. Keeping the number off the fill avoids the question.
- **Accent colour is gone from email and social.** It was only ever the far end of a gradient and the "+N more" callout.
- **Gallery sizes collapsed from six to two shapes** (see block table).
- **Open Houses** uses `read:panel`, not an AI insight — the kind is paused and the data isn't reliable enough to narrate.

## Data the design assumes and the API may not have

1. Agent postal address — needed to decide the footer. If absent the footer falls back to ours; make sure it's a field on branding/profile, not inferred.
2. Delta vs. prior period for the hero (`▲ 2.1%`). If the builder doesn't compute it, the sub line is omitted, not a dash — a dash under a headline number reads as broken.
3. `headline` on the social payload (today only the email gets the insight).
4. Home value: `confidence`, `radius`, `source_url`, `cover_png_url`.
5. Schedule failure reason strings and paused-schedule list.
6. Listing photos ≥1080px for the social photo kinds.

## Not done, on purpose

- Plain-text alternates (`get_*_email_text`) — copy is in the HTML; mirror it.
- Per-client renders (Litmus/Email on Acid). The markup follows the conservative set (nested tables, `bgcolor` + `background`, `mso` conditionals, no web fonts) but has not been run through a render farm.
- A rep-sent market email. Reps don't broadcast (DECISIONS #4 in the sponsor package); `sender_type` only changes the insight's voice.
