# Two things the first two batches measured

**For Design. Both are facts about our codebase, not disagreements with the package.** Steps 1–3 of
`ADOPTION.md`'s order are done and measured; these are what the measurement turned up.

## 1 · Three of twenty-two routes use `ui/card`

Your §3 calls steps 5–7 *"mechanical once Tabs and Badge are done"*. That holds for a build where
the lists are composed from the card primitive. Ours mostly are not.

Counted by rendering all 22 authenticated routes with a real database behind them and asking each
page how many of each primitive it contains — `data-slot` attributes, so a restyle cannot change
what is being counted:

| primitive | routes containing it, of 22 |
|---|---|
| `button` | **19** |
| `input` | 8 |
| `badge` | 7 |
| `table-head` / `table-cell` / `table-row` | 4 |
| **`card`** | **3** |
| `card-title` | 3 |
| `switch` | 1 |
| `tabs-trigger` | 1 |

**So the Card restyle — `rounded-2xl`, no shadow, `p-6`, `CardTitle` 17/700 — reached three pages.**
Everything else that looks like a card in this app is a hand-rolled `<div className="bg-card border
rounded-xl …">`. The restyle is correct and it is also nearly invisible, which is worth you knowing
before the next estimate.

**What that changes:** steps 5, 6 and 7 are page-file work at roughly the scale of step 4, not
mechanical follow-on from step 2. Reports / Property / Schedules get filter pills and thumbnails
inside markup that does not currently use the primitives those pills and cards come from.

**This is the third time an estimate has been right about your build and wrong about ours** — after
the `tokens.css` "drop-in replacement" that omitted one live variable name, and the "restyle only"
classification that was right for Button and wrong for the file count around it. We are not asking
you to change the package; the shapes in §2 have been correct every time. **It is the sizing that
does not survive contact with this repository**, and you have corrected the method twice when shown
a measurement, which is why this one comes with the table.

## 2 · `--placeholder` is specified both ways

`tokens.css`:

```css
--placeholder: #94A3B8;   /* NEW — placeholders and decorative icons ONLY, never text */
```

`ADOPTION.md`, bucket A, `ui/button`:

> add `disabled` style text `#94A3B8` on white with border (instead of opacity 50)

The same value, forbidden as text in one file and specified as button text in the other.

**We used the token and shipped it**, because the reasoning behind the rule is contrast and a
disabled control is the one case where *not* reading as active is the point — but that is us
deciding a question that is yours. The rule as written would also forbid it, so one of the two
documents needs a sentence.

Three options as we see them, and no preference:

1. the rule gains the exception — "never text, except a disabled control";
2. the disabled text is a different value that clears 3:1 on white;
3. disabled keeps a border and a lighter *weight* rather than a lighter colour.

---

**Form note:** same as `TINT_RAMP_FOR_DESIGN_2026-10-15.md` and
`REPORT_VIEWER_TINTS_FOR_DESIGN_2026-10-19.md` — the measurement, the question, and no proposal.
