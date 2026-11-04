# Design handoff rules

Owner's text, 2026-11-04, committed exactly as given.

Standing rules for every Design handoff:
1. Name the live file and the main commit you cut against.
2. One change per edit: page, why, exact before, exact after.
3. Ship a check that refuses to apply if any anchor moved.
4. No full-file copies. No new files unless asked.
5. Templates and styles only. Never data, builders, or Python.
6. Flag any edit touching a fixed rule: page count, brand colour,
   derived inks, text on gradients or photos, missing-data dashes,
   the estimate panel.
7. Structural changes are a separate question, not an edit.
Handoffs that break these are rejected, naming the rule.

On every handoff: run their --check first, never copy a Design file over
a live one.
