#!/usr/bin/env python3
"""Apply the digital-report round-2 touches to the live files, or refuse.

    python3 docs/design-claude/design_handoff_digital_report_r2/apply_touches.py --check
    python3 docs/design-claude/design_handoff_digital_report_r2/apply_touches.py

Run from the repo root. `touches.json` beside this script is the single
source: one entry per edit — `file`, `before`, `after`, optional `count`
(how many times `before` must occur; default 1).

THE RULE. Every `before` must occur exactly `count` times in its file, in
order, as the earlier touches leave it — or nothing is written to any file.
A string that occurs 0 or 2+ times means the anchor moved since this was
cut, and a replace against a moved anchor is how an edit lands in the wrong
place and passes review. `--check` runs the same simulation and writes
nothing either way.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE
while ROOT != ROOT.parent and not (ROOT / "apps").is_dir():
    ROOT = ROOT.parent


def main(check_only: bool) -> int:
    spec = json.loads((HERE / "touches.json").read_text(encoding="utf-8"))
    texts = {}
    for rel in spec["files"]:
        path = ROOT / rel
        if not path.is_file():
            print(f"MISSING  {rel}")
            return 2
        texts[rel] = path.read_text(encoding="utf-8")

    problems = []
    for t in spec["touches"]:
        want = int(t.get("count", 1))
        text = texts[t["file"]]
        found = text.count(t["before"])
        if found != want:
            problems.append(f"{t['id']:<4} {t['file']}: expected {want} occurrence(s), found {found}")
            continue
        texts[t["file"]] = text.replace(t["before"], t["after"])

    if problems:
        print("REFUSED — anchors moved; nothing written:")
        for p in problems:
            print("  " + p)
        return 1

    n = len(spec["touches"])
    if check_only:
        print(f"OK — all {n} anchors present exactly as cut; nothing written (--check).")
        return 0

    for rel, text in texts.items():
        (ROOT / rel).write_text(text, encoding="utf-8")
        print(f"wrote    {rel}")
    print(f"applied {n} touches.")
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv[1:]))
