#!/usr/bin/env python3
"""Every key read off a raw SimplyRETS row, checked against a real payload's shape.

WHY THIS IS A SCRIPT AND NOT ONLY A TEST. The test beside it
(apps/worker/tests/test_extract_field_paths.py) asserts that fields the feed
carries come out populated — it catches a wrong path once the field is known.
This enumerates the reads themselves with `ast`, so a field added tomorrow with
a guessed key shows up as "not in fixtures" rather than as silence.

Run it whenever extract.py gains a read, and whenever a fresh payload is
captured:

    python3 scripts/sweep_extract_field_paths.py

WHAT IT FOUND, 2026-09-28: `daysOnMarket` read at the top level where the feed
puts it under `mls` (D-105, fixed), and `bathrooms` read as `property.bathrooms`
where the feed carries `bathsFull`/`bathsHalf` (D-106, open). A third flag,
`status`, is a dead fallback rather than a defect — the expression reads
`mls.status` first. Verify every flag; the tool points, it does not conclude.

LIMIT, STATED. It checks against `tests/fixtures/listing_*.json` — captured
responses, real in shape, but two of them. A key absent from both is unproven
rather than wrong. `tools/dump_market_snapshot.py` fetches a live page with
SimplyRETS credentials and would widen the sample in one call.
"""
import ast, json, sys
from pathlib import Path

REPO = Path("/home/user/reportscompany")
FIXTURES = {p.stem: json.load(open(p)) for p in sorted((REPO / "tests/fixtures").glob("listing_*.json"))}


def walk(obj, path=""):
    """Every key in the payload, with its full path."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else k
            yield k, here, v
            yield from walk(v, here)
    elif isinstance(obj, list) and obj:
        yield from walk(obj[0], f"{path}[0]")


def index(payload):
    out = {}
    for k, path, v in walk(payload):
        out.setdefault(k, []).append(path)
    return out


def source_of(node):
    """Render the receiver of a .get() call, normalised.

    `(addr or {}).get("city")` unparses to `(addr or {})`, which the first
    version of this sweep did not match against its list of row variables — so
    it silently examined 10 of 22 reads and reported completeness. Unwrap the
    `x or {}` guard, which is how every sub-object in this file is read.
    """
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        node = node.values[0]
    try:
        return ast.unparse(node)
    except Exception:
        return "?"


def is_get(node):
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get" and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str))


def fallback_reads(tree):
    """Reads that are a later branch of `a.get(k) or b.get(k)`.

    Both remaining flags after D-105's fix are this shape — `mls.daysOnMarket`
    or `p.daysOnMarket`, `mls.status` or `p.status` — where the correct path is
    read first and the flagged one can only run when it returned None. Without
    this the tool reports two defects that are not defects, and a tool whose
    every flag is a false positive gets ignored, which costs more than the
    noise.
    """
    out = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or)):
            continue
        seen = {}
        for branch in node.values:
            for inner in ast.walk(branch):
                if is_get(inner):
                    key = inner.args[0].value
                    if key in seen:
                        out.add((inner.lineno, source_of(inner.func.value), key))
                    else:
                        seen[key] = True
    return out


def sweep(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fallbacks = fallback_reads(tree)
    rows = []
    for node in ast.walk(tree):
        if is_get(node):
            rows.append((node.lineno, source_of(node.func.value),
                         node.args[0].value,
                         (node.lineno, source_of(node.func.value),
                          node.args[0].value) in fallbacks))
    return rows


#: Flags that have been looked at and are correct. Same contract as the colour
#: lint's baseline: a known finding is tolerated with its reason recorded, a new
#: one fails. An empty reason is not allowed — the point is that someone
#: checked.
ACKNOWLEDGED = {
    ("daysOnMarket", "daysOnMarket"):
        "D-105's retained fallback. `mls.daysOnMarket` is read first, and the "
        "top-level read only runs when that returned None, for deployments "
        "that put it there. Written as an `if dom is None` reassignment rather "
        "than `a or b` ON PURPOSE: a DOM of 0 is a real value and `or` would "
        "discard it, which is the defect one line over in a different costume.",
}

TARGET = REPO / "apps/worker/src/worker/compute/extract.py"
rows = sweep(TARGET)
idx = {name: index(p) for name, p in FIXTURES.items()}

# Which receivers are the raw row or a sub-object of it?
ROW_VARS = {"p": "", "addr": "address", "pr": "property", "mls": "mls", "sales": "sales"}

print(f"{len(rows)} `.get(\"...\")` reads in {TARGET.relative_to(REPO)}\n")
print(f"{'line':>4}  {'read as':28s} {'expected path':26s} verdict")
print("-" * 96)
problems = []
skipped = []
for lineno, recv, key, is_fallback in sorted(rows):
    if recv not in ROW_VARS:
        skipped.append((lineno, recv, key))
        continue
    if is_fallback:
        print(f"{lineno:>4}  {recv + '.get(' + repr(key) + ')':28s} {'(fallback)':26s} "
              f"skipped — the same key is read from a more specific path first")
        continue
    prefix = ROW_VARS[recv]
    want = f"{prefix}.{key}" if prefix else key
    verdicts = []
    for name, keys in idx.items():
        paths = keys.get(key, [])
        if want in paths:
            verdicts.append((name, "ok", want))
        elif paths:
            verdicts.append((name, "ELSEWHERE", ", ".join(paths)))
        else:
            verdicts.append((name, "absent", ""))
    bad = [v for v in verdicts if v[1] == "ELSEWHERE"]
    state = "MISREAD" if bad else ("ok" if any(v[1] == "ok" for v in verdicts) else "not in fixtures")
    detail = bad[0][2] if bad else ""
    print(f"{lineno:>4}  {recv + '.get(' + repr(key) + ')':28s} {want:26s} {state}"
          + (f"  -> lives at {detail}" if detail else ""))
    if bad:
        problems.append((lineno, recv, key, want, detail))

print()
new_problems = [x for x in problems if (x[2], x[3]) not in ACKNOWLEDGED]
known = [x for x in problems if (x[2], x[3]) in ACKNOWLEDGED]
for lineno, recv, key, want, detail in known:
    print(f"acknowledged  extract.py:{lineno}  {want}")
    print(f"              {ACKNOWLEDGED[(key, want)]}")
if known:
    print()
if new_problems:
    print(f"{len(new_problems)} MISREAD — the key exists in the payload, at a different path:")
    for lineno, recv, key, want, detail in new_problems:
        print(f"  extract.py:{lineno}  reads {want}   payload has {detail}")
    sys.exit(1)
print("no unacknowledged misreads among keys present in the fixtures")
print()
print(f"{len(skipped)} reads NOT against a raw row (reported, not dropped):")
for lineno, recv, key in skipped:
    print(f"  line {lineno}: {recv}.get({key!r})")
