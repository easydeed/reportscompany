# Notes for the next Design request

Points to carry into the next request to Design, whatever its subject. Each was decided
after a handoff; once a point has gone out in a request, move it to that request's record
rather than deleting it.

## Rule 6: flag every brand-derived text colour

Flag every edit that colours text with a brand-derived ink under rule 6 of
`docs/DESIGN_HANDOFF_RULES.md`, even when the ink is used for its normal job: `primary_ink` on
white, `primary_on_dark` on the dark neutral, `on_primary` on the brand fill, `display_ink`, and so
on.

Why (Jerry, 2026-11-05): round 2 for `/p` and `/r`
(`docs/design-claude/bpages/design_handoff_digital_report_r2/`, applied in #269) put `primary_ink`
on two runs of text without a flag. One was the consent asterisk (F7a), the other the phone link on
the phone agent line (B2). Both were used correctly and pass contrast, so they were accepted as
applied rather than sent back over a missing label. The flag is how we know where to measure. From
the next handoff on, an unflagged brand-derived text colour is returned under rule 6.
