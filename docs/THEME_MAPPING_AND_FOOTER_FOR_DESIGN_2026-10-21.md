# Two things to confirm before we touch either cover

**For Design. Nothing has been applied.** No template, no contrast baseline, no measurement code.
We stopped because a stopgap keyed on the wrong theme is worse than the defect it fixes, and twice
in two days a name has turned out to mean something different on each side.

---

## 1. The name mapping — measured from the files, not from either of our lists

Your answer names the live themes **`elegant`, `bold`, `modern`** and says **`harbor` is removed**.
Ours are `atlas`, `linen`, `harbor`. Rather than reconcile two lists, we asked git what the files
are. `2726c599`, 2026-10-13, with git's own rename detection and the similarity it reports:

| was | is now | content similarity | id |
|---|---|---|---|
| `bold/bold_report.jinja2` | **`atlas/atlas_report.jinja2`** | **95%** | 5 |
| `elegant/elegant_report.jinja2` | **`linen/linen_report.jinja2`** | **97%** | 3 |
| `modern/modern_report.jinja2` | **`harbor/harbor_report.jinja2`** | **98%** | 2 |

So all three are **the same files renamed**, ids unchanged, and `classic` and `teal` are the pair we
cut on 2026-10-05. Three live themes, under two vocabularies.

**Which makes one sentence in your answer ambiguous in a way that matters.** *"`harbor` is
removed"* cannot be about our `harbor`: the name is eight days old, it belongs to the theme you
call `modern`, and your own live list includes `modern`. Two readings and they lead to opposite
work:

* **you mean `modern`** — then the cover-title guidance applies to a theme we ship, and the fix
  lands in `harbor/harbor_report.jinja2`;
* **you mean a design of yours that happens to be called harbor** — then your note is about
  something our tree does not contain, and we should not read cover-title guidance from it at all.

**Please confirm against the files rather than the names.** The cover title we measured is
`harbor_report.jinja2:52`:

    .cover-title span{background:var(--gradient-coral);
                      -webkit-background-clip:text;
                      -webkit-text-fill-color:transparent;}

If that element is in your redesign's scope, we have the right file. If it is not, tell us and we
will stop.

---

## 2. The footer — "legacy and retired" is true of your package and false of our build

You said the brand-tinted footer is legacy and gone in the redesign. **It is in a file we ship
today**, and it is not in a shared base template — we checked, because a finding reached us saying
it was.

### The inheritance chain, as it actually is

    registry (themes.json)        ->  atlas/atlas_report.jinja2  -> includes _v2/report.jinja2
                                      linen/linen_report.jinja2  -> self-contained, 720 lines
                                      harbor/harbor_report.jinja2 -> self-contained, 795 lines

**Only `atlas` is on your shared page.** `linen` and `harbor` still carry their own full templates,
which is why they are the two with the failing covers — and why your `on_primary` /
`primary_on_dark` vocabulary does not appear in them. They use the older `theme_color_*` names for
the same values.

There is also a `property/_base/` directory containing `base.jinja2` and `_macros.jinja2`. **It
renders nowhere.** Three files extend it — `atlas/atlas.jinja2`, `linen/linen.jinja2`,
`harbor/harbor.jinja2` — and none of those is a template the registry names; a gate
(`test_one_comp_set.py`) forbids a live template from reaching that directory. It declares
`.cover-agent-name` at **15px** while the runs we measured are **22px** (`linen`) and **18px**
(`harbor`), so the measurements come from the self-contained files, not from there. Worth saying
plainly because the same filename exists under `market/_base/`, where it **is** live.

### The surface, in the file we ship

`linen/linen_report.jinja2`:

    :13   --burgundy: {{ theme_color }};
    :46   .cover{background:linear-gradient(135deg,var(--burgundy),var(--burgundy-dark));}
    :62   .cover-footer{padding:0.5in 0.6in; background:rgba(0,0,0,0.2); …}
    :65   .cover-agent-info{color:#fff;}
    :66   .cover-agent-name{font-size:22px;}

Measured over 38 brands — 32 spaced evenly in relative luminance plus your six presets —
`div.cover-agent-name` **passes up to brand luminance 0.417 and fails from 0.439**, and it is not
the worst thing on that cover:

| surface | brands failing, of 38 |
|---|---|
| `div.cover-label` | **36** |
| `div.cover-brand-text` | 34 |
| `th` / `td` | 29 / 28 |
| `div.cover-agent-title` | 25 |
| `div.cover-agent-name` | 19 |

`atlas`, on your shared page, fails **one** brand out of 38 on eight surfaces and nothing else. The
sweep reproduces your ruling without being told it: the covers not yet on your architecture are the
covers that fail.

### The question

**Is your redesigned footer meant to replace this one, or does your package simply not contain
it?** Both are consistent with "legacy and retired" — the first means the fix is to land your
footer, the second means we have a surface you have never seen and the fix is ours to specify.

We would rather ask than apply a stopgap to a file your redesign is about to replace.

---

## What we are holding, and why

Both stopgaps, together, because you gave them as one decision:

| surface | the change, as we read it | worst of 6 presets |
|---|---|---|
| footer band | solid `primary` plate, ink `on_primary` | **4.83** against 4.5 |
| cover title | solid `primary_on_dark` glyphs, gradient and the two circles removed | **3.90** against 3.0 |

Both clear. The reason for the hold is ours and not yours: changing the band colour re-keys our
contrast baseline (5 of `linen`'s 36 rows are footer selectors keyed on the tinted band), and
whether to regenerate that family is a policy call on our side.

One correction to something we sent you yesterday: we reported that `on_primary` *made the footer
worse*. That was us swapping the ink while leaving the band as `rgba(0,0,0,0.2)` over the gradient.
`on_primary` is ink guaranteed against `primary`, so **the plate is not optional** — it is what
makes the token correct. `theme_color_text` against a solid brand reproduces your
`contrast_on_primary` figures to the hundredth for all six brands, so the two names are one token.
