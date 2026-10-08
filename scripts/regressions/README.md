# Recorded regressions

One JSON file per gate or per area. Each entry is a mutation that **must** make
its gate fail — run them with:

    python3 scripts/apply_regressions.py scripts/regressions/<file>.json

Exit 0 means every mutation fired. Exit 1 means one did not, which is a gate
that does not guard. Exit 2 means the harness could not prove its own state and
has told you nothing about the gate.

**Why these are recorded rather than re-invented.** "Seen to fail" is the only
evidence a gate works, and a mutation described in a commit message cannot be
re-run. Keeping the mutation itself means the claim can be checked a year later
by someone who was not there — and it means a gate that is weakened later fails
a run rather than silently losing its teeth.

`scripts/regress.py` is the predecessor: the same idea for `themes.py` alone,
with its eleven mutations ported to `themes.json` here. It is left in place
because it also restores the golden file, which no spec expresses yet.


## It was built to catch bad mutations. It mostly finds missing tests.

Three days, three kinds of result — and only one of them is what the harness was
for:

| reported | what it actually was |
|---|---|
| `DID NOT FIRE` on a `height: 180px` mutation | **a gate passing on a substring**: `"height: 180px;" in css` matches inside `min-height: 180px;`, so the change that voided a whole measurement left it green |
| `DID NOT FIRE` on the `_ensure_readable_on_light` fallback | **a mutation on dead code**: 64 steps of 6% darkening reaches near-black from anywhere, so the fallback is unreachable for any hex input and nothing could have observed the change |
| `DID NOT FIRE` on an `isinstance(lst, ...)` guard | **an untested case**: a second guard caught the `None`, so the type check looked redundant — it is the only thing between a string list price and a `TypeError` on the render path, and nothing tested it |
| `DID NOT FIRE` on three `new_listings` mutations | **a whole kind with no tests**: the kind was wired and nothing covered what makes it different from `closed`. Eleven tests followed |

So: one bad mutation, one dead branch, and **three kinds' worth of behaviour
nobody had tested**. The harness was built to stop a no-op mutation reading as a
pass; its larger use has been pointing at code with no test behind it, which is
a different question and one nothing else here asks.

`DID NOT FIRE` therefore has three readings, and they are worth distinguishing
before changing anything:

1. **the gate is weak** — it matches text where a construct is meant, or asserts
   something the mutation does not touch;
2. **the mutation is wrong** — it targets a branch nothing can reach, or a case
   a different guard already covers;
3. **the behaviour is untested** — the mutation is fine, the gate is fine, and
   there is simply no test for the thing being broken.

Only (1) is a defect in the gate. (2) is a finding about the code — an
unreachable branch is worth a comment saying so. (3) is the common one, and the
answer is a test, not a weaker mutation.

## And once a kind has tests, the mutations stop finding things

`market_v2_kinds.json` grew from 14 to 22 entries when `price_bands` was wired,
and **all eight new mutations fired on the first run** — no `DID NOT FIRE` at
all, where `new_listings`' three had all come back untested.

The difference is the order of work. `new_listings`' mutations were recorded
against gates written for `closed`; `price_bands`' were recorded against gates
written for `price_bands`, after four defects had already been found by a
different instrument — repointing the old band chart's tests at the page that
replaced it rather than deleting them (D-180, D-181).

Which is the useful thing to know about this tool: **a clean run is evidence
about the gates, not about the code.** Eight for eight says the recorded
mutations express defects the suite catches. It says nothing about the defects
nobody thought to mutate, and the four found that day were all in that second
category.
