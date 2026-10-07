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
