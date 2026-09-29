"""Re-run D-108's enumeration by hand.

The check itself lives in `apps/worker/tests/_zero_conditionals.py` and runs in
CI as `test_zero_conditionals.py`. This script is the same walk with its
workings printed, for when you want the list rather than a pass/fail — after
adding a template, or before deciding whether a new field needs an exemption.

One implementation, two front ends. An audit script and a gate that each
carried their own copy of the rule would disagree, and the one that disagreed
quietly would be the gate.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/worker/tests"))

from _zero_conditionals import (  # noqa: E402
    EXEMPT, audit_all, audit_python, numeric_leaf_names, unexempt,
    unused_exemptions,
)

names = numeric_leaf_names()
findings = audit_all() + audit_python(names)
open_ = unexempt(findings)

print(f"\n{len(names)} numeric leaf names, derived from real built contexts")
print(f"{len(findings)} places a template or a statistic decides one of them\n   by truthiness alone")
print(f"{len(open_)} of those are not exempt\n")

by_file = {}
for f in findings:
    by_file.setdefault(f.template, []).append(f)
for template in sorted(by_file):
    print(template)
    for f in sorted(by_file[template], key=lambda f: (f.line, f.expr)):
        mark = "OPEN " if f in open_ else "     "
        reason = EXEMPT.get(f.expr) or EXEMPT.get(f.expr.split(".")[-1]) or ""
        print(f"  {mark}{f.line:>5}  {f.expr:<28} {f.kind:<8} {reason}")
    print()

stale = unused_exemptions(findings)
if stale:
    print(f"STALE EXEMPTIONS (nothing uses these any more): {stale}")
if open_:
    print("OPEN — these render nothing when the value is a real 0:")
    for f in open_:
        print(f"  {f}")
    sys.exit(1)
print("No template hides a zero it has not been excused for.")
