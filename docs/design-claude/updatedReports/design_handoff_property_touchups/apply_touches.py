#!/usr/bin/env python3
"""Apply Design's property-report touches T1–T9 to the LIVE template.

    python apply_touches.py apps/worker/src/worker/templates/property/_v2/report.jinja2
    python apply_touches.py --check <path>     # report only, write nothing

Each touch is an exact-string replacement from touches.json. Every `before`
must occur EXACTLY ONCE in the file or nothing is written — so a file that
has moved on since these were cut fails loudly instead of being half-patched.
Nothing outside the `before` strings is touched.
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
touches = json.loads((HERE / "touches.json").read_text(encoding="utf-8"))

args = [a for a in sys.argv[1:] if not a.startswith("--")]
check_only = "--check" in sys.argv
if len(args) != 1:
    sys.exit(__doc__)
target = Path(args[0])
src = target.read_text(encoding="utf-8")

problems = []
for t in touches:
    n = src.count(t["before"])
    if n != 1:
        problems.append(f"{t['id']}: `before` found {n} times (need exactly 1) — {t['title']}")
if problems:
    print("Not applied. The live file differs from the one these edits were cut against:")
    print("\n".join("  " + p for p in problems))
    sys.exit(1)

out = src
for t in touches:
    out = out.replace(t["before"], t["after"], 1)
    print(f"{t['id']:4} ok  {t['title']}")

if check_only:
    print("--check: all touches apply cleanly; nothing written.")
else:
    target.write_text(out, encoding="utf-8")
    print(f"Wrote {target} ({len(src)} → {len(out)} bytes).")
