#!/usr/bin/env python3
"""Re-derive DEFECT_LIST.md's summary table by parsing the entries.

    python3 scripts/derive.py

WHY THIS FILE NO LONGER HAS ITS OWN PARSER. It used to, and on 2026-09-30 the
two disagreed: this script reported 149 contiguous entries with `fixed = 89`
while `tests/test_defect_list_counts.py` saw 146 and `fixed = 86`. Three
entries had their `**Status:**` mid-line rather than at the start of one, which
the test's line-anchored regex requires and this script's did not. The script
said the document was fine; the test said it was not; the test was right.

A second implementation of "how to read this document" is a second answer
waiting to be believed — and this is the script whose whole job is to stop the
summary drifting from the entries. So it imports the test's `parse()` and there
is exactly one reader.
"""
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.test_defect_list_counts import parse  # noqa: E402

board = parse()
ids = sorted(board)
nums = [int(i[2:]) for i in ids]
missing = [n for n in range(nums[0], nums[-1] + 1) if n not in nums]

print(f"total {len(ids)}  first {ids[0]}  last {ids[-1]}")
print(f"missing {missing}  dupes {[i for i, n in collections.Counter(ids).items() if n > 1]}")

counts = collections.Counter(status for status, _ in board.values())

# EVERY status, not a hardcoded four. The four-name loop printed
# 0 + 52 + 103 + 4 = 159 against a stated total of 160 the moment a fifth
# status (`duplicate`) appeared, and printed it without complaint — a summary
# that can omit a row is the drift this script exists to catch, one level up.
for k in sorted(counts):
    print(f"  {k}: {counts[k]}")
assert sum(counts.values()) == len(ids), (
    f"statuses sum to {sum(counts.values())} against {len(ids)} entries")

opensev = collections.Counter(sev for status, sev in board.values() if status == "open")
print(f"open by severity: {dict(opensev)}  sum {sum(opensev.values())}")
