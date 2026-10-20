# Both property covers put the customer's brand in a contrast pair with no floor under it

**For Design. One decision, and it is structural rather than chromatic — the argument you have
made twice yourselves.** Nothing has been changed. No template, no contrast baseline, no
measurement code. This document is the ask.

## The short version

Two surfaces on the property report covers derive a contrast pair from `theme_color`, which is the
account's own brand colour. Neither has a floor. Across the six brands in the corpus today,
**six of twelve brand/surface combinations fail their WCAG threshold**, and the two failing sets
are **disjoint**:

| surface | mechanism | fails for | passes for |
|---|---|---|---|
| `linen` · `.cover-agent-name` | **white** on a footer tinted by the brand | amber, lime | the other four |
| `harbor` · `.cover-title span` | **brand-coloured glyphs** on near-black | violet, coastal, demo_title, luxury_estates | amber, lime |

The light brands fail the first. The dark brands fail the second. **No choice of colour fixes
either, because the colour is the customer's** — which is why we think this is a question about
the construction of the two surfaces and not about a palette.

## Surface 1 — `linen`, the agent's name on the cover footer

`linen_report.jinja2`:

    :13   --burgundy: {{ theme_color }};
    :46   .cover{background:linear-gradient(135deg,var(--burgundy),var(--burgundy-dark));}
    :62   .cover-footer{padding:0.5in 0.6in; background:rgba(0,0,0,0.2); …}
    :65   .cover-agent-info{color:#fff;}
    :66   .cover-agent-name{font-size:22px;}

22px is **not** WCAG large text (≈16.5pt, under the 18pt line), so the threshold is 4.5:1.
Measured over the corpus — 2,640 runs, 12 on this selector — the backdrop is **0.677 × the brand
colour** on every one of the six, to within channel rounding:

| brand | brand | backdrop | ratio | |
|---|---|---|---|---|
| lime | `#84CC16` | `#58880e` | **4.25** | fails |
| amber | `#F59E0B` | `#a66b07` | **4.44** | fails |
| luxury_estates | `#0D9488` | `#08645c` | 7.03 | passes |
| demo_title | `#DC2626` | `#951919` | 8.64 | passes |
| coastal | `#0E7490` | `#084d60` | 9.37 | passes |
| violet | `#7C3AED` | `#5427a0` | 9.66 | passes |

Brand relative luminance runs violet 0.134, coastal 0.146, demo_title 0.167, luxury_estates 0.230,
then **amber 0.439 and lime 0.481**. **Nothing sits between 0.23 and 0.44**, so these six cannot
tell us where the cut-off is — a brand someone picks tomorrow lands anywhere in that gap, and the
build reports it as a regression although no template changed.

## Surface 2 — `harbor`, the word "Report" on the cover title

`harbor_report.jinja2`:

    :21   --gradient-coral: linear-gradient(135deg, {{ theme_color }} 0%,
                                            {{ theme_color_light }} 50%, #FFB199 100%);
    :43   .cover-left{background:var(--gradient-dark);}   /* #1A1F36 -> #2D3348 */
    :44   .cover-left::before{background:var(--coral); opacity:0.1;}
    :51   .cover-title{font-size:56px; color:var(--pure);}
    :52   .cover-title span{background:var(--gradient-coral); background-clip:text;
                            -webkit-text-fill-color:transparent;}

`<h1 class="cover-title">Seller's<span>Report</span></h1>` — "Seller's" is white and fine.
"Report" is the brand gradient, clipped to the glyphs, over near-black. 56px is large text, so the
threshold is 3.0:1. Worst glyph stop against the worst point of the backdrop:

| brand | stop 0 | stop 50% | worst | |
|---|---|---|---|---|
| violet | `#7C3AED` | `#a97ef3` | **2.07** | fails |
| coastal | `#0E7490` | `#62a4b6` | **2.16** | fails |
| demo_title | `#DC2626` | `#e87171` | **2.49** | fails |
| luxury_estates | `#0D9488` | `#61b9b1` | **2.99** | fails |
| amber | `#F59E0B` | `#f8bf60` | 4.91 | passes |
| lime | `#84CC16` | `#afdd67` | 5.27 | passes |

**This surface is invisible to our gate**, which is how it went unnoticed. The measurement blanks
glyphs with the same `-webkit-text-fill-color` the template uses, so for this element blanking
changes nothing and the sampled "backdrop" comes back as the title's own gradient. The gate
correctly declines to measure it — and the hand calculation that justified declining it,
`4.47:1 worst / 9.28:1 best`, was done on `#FF6B5B`, **the template default, which is the colour
used when no brand is set.** It reproduces exactly and it describes a document no customer
receives. Filed as D-206.

## What we are asking

**Is the fix a scrim or a plate — something structural between the brand and the text — rather
than a colour?**

We ask it that way because the three options are not equivalent and only one of them survives a
brand nobody has picked yet:

1. **A floor on the derived colour** — clamp the composited backdrop (or the glyph stop) until the
   pair clears its threshold. This is the `accent_ink` / `display_ink` pattern already in the
   codebase (D-171, D-177). It works, and it **changes the customer's brand colour on their own
   document**, differently for different customers, which is the thing those two entries were
   careful about.
2. **Per-brand exceptions in the contrast baseline** — bookkeeping only. It encodes the
   instability instead of removing it and leaves the document exactly as unreadable.
3. **A scrim or a solid plate** — `.cover-footer` on an opaque dark plate rather than
   `rgba(0,0,0,0.2)` over the brand; the title on a backdrop that does not derive from the brand
   at all, or the brand gradient moved to an element that is not text. The brand stays the
   customer's colour, the contrast pair stops depending on it, and a brand at any luminance is
   safe before anyone picks it.

Option 3 is **structural, not chromatic**, which is the argument you made for the embedded report
page (constraint #2 — scaled, never reflowed) and again for the tint removal (*"it competes with
the report, which is what the agent is selling"*). We think it applies here and we would rather
hear it from you than infer it.

## What we have not done, deliberately

- **Not regenerated the contrast baseline.** It would close D-205 by writing down what the gate
  currently reports, which is the one move that file exists to prevent — and it would leave lime's
  4.25:1 recorded and unfixed, as it already is.
- **Not touched `EXPECTED_DECLINED`.** The count is right; what expired is the reasoning behind
  it.
- **Not changed a template.** Both of these are visible on every property cover that ships, so the
  change is yours to specify.

## If you want to see it

    scripts/local_stack.sh up
    python3 -m pytest apps/worker/tests/test_pdf_contrast.py

The gate prints `linen`'s failure. `harbor`'s does not appear, by construction — the table above
is the hand calculation, and the stops are in the two files quoted.
