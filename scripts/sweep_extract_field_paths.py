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
    python3 scripts/sweep_extract_field_paths.py --capture out/downey.json

WHAT IT FOUND, 2026-09-28: `daysOnMarket` read at the top level where the feed
puts it under `mls` (D-105, fixed), and `bathrooms` read as `property.bathrooms`
where the feed carries `bathsFull`/`bathsHalf` (D-106, open). A third flag,
`status`, is a dead fallback rather than a defect — the expression reads
`mls.status` first. Verify every flag; the tool points, it does not conclude.

FIRST RUN AGAINST REAL DATA, 2026-10-01: 24 reads, 0 unacknowledged misreads,
against 301 listings from a live market. `closeDate`, `closePrice` and
`daysOnMarket` confirmed reading the paths the feed actually uses.

THREE VERDICTS, AND ONLY TWO OF THEM USED TO FAIL — WHICH IS HOW THAT CLEAN RUN
COEXISTED WITH AN OPEN DEFECT. `bathrooms` exists at NO path in any payload, so
it was never `MISREAD`; it was `not in fixtures`, which did not fail the run and
did not appear in the count. Anyone reading "0 unacknowledged misreads" took it
as an all-clear on a field that is empty in every report.

Against two bundled fixtures that shrug is correct — absent from two files is
unproven rather than wrong. Against a `--capture` of hundreds of real rows it is
not: the feed demonstrably does not send that key, and a read that never
resolves is a column that is always empty. So with `--capture` the verdict
becomes `ABSENT FROM CAPTURE` and exits 1, with the same escape hatch as a
misread: `ACKNOWLEDGED` tolerates a known one WITH ITS REASON RECORDED, and a
new one fails. `bathrooms` is acknowledged there now, naming D-106 — acknowledged
is not fixed, and the board is the source of truth for which it is.

LIMIT, STATED. It sweeps `compute/extract.py` and nothing else. The four sites
D-145 fixed live in `routes/property.py`, `worker/tasks.py`,
`services/simplyrets.py` and `schemas/property.py`; their guard is the AST test
in `apps/api/tests/test_close_price_field_path.py`, not this. And without
`--capture` it checks against two fixtures. `tools/dump_market_snapshot.py`
writes a raw dump of a live page by default (D-150); pass it here and every row
joins the sample.
"""
import argparse, ast, json, sys
from pathlib import Path

#: Derived from this file's own location, not hardcoded. It was
#: `Path("/home/user/reportscompany")`, which runs on exactly one machine —
#: and the point of this script is that somebody with credentials runs it
#: against a fresh capture, on theirs.
REPO = Path(__file__).resolve().parents[1]


def load_payloads(capture: Path | None) -> dict:
    """The shapes to check reads against.

    `tests/fixtures/listing_*.json` are two captured responses: real in shape,
    and two. A key absent from both is UNPROVEN rather than wrong, and the
    difference matters — this tool points, it does not conclude.

    `--capture` widens that. `tools/dump_market_snapshot.py` writes a live
    page fetched with real credentials, so one file can carry hundreds of rows
    from a real market rather than two from a demo one. Passing it here is the
    difference between "absent from two fixtures" and "absent from 301 real
    listings", which are different findings.
    """
    out = {p.stem: json.load(open(p))
           for p in sorted((REPO / "tests/fixtures").glob("listing_*.json"))}
    if capture:
        data = json.loads(capture.read_text(encoding="utf-8"))
        # A capture is a page of rows, or an object wrapping one. Take the
        # first row of whichever, because `index()` wants one listing's shape
        # and every row in a page shares it.
        # A MARKET SNAPSHOT IS NOT A CAPTURE, and accepting one would be worse
        # than refusing it. `tools/dump_market_snapshot.py`'s output carries
        # `listings_sample`, which looks like rows and is not: five closed and
        # five active, already NORMALISED (`close_price`, not
        # `sales.closePrice`) and with every date field stripped. Reading it
        # here would report the feed's own key names as absent from real data
        # — the exact false negative that made the probe say 0/20 and got
        # D-144 filed on a premise that was not true.
        if isinstance(data, dict) and "listings_sample" in data and "metrics" in data:
            sys.exit(
                f"{capture} is a market SNAPSHOT, not a capture of raw rows.\n"
                f"Its `listings_sample` is five closed and five active rows, "
                f"already normalised and with the date fields removed, so "
                f"every path below would read as absent and none of it would "
                f"be true.\n"
                f"Re-capture the rows themselves:\n"
                f"    python3 tools/dump_market_snapshot.py --city {data.get('city', 'Downey')} "
                f"--raw-out tmp/{str(data.get('city', 'downey')).lower()}_raw.json\n"
                f"    python3 scripts/sweep_extract_field_paths.py --capture "
                f"tmp/{str(data.get('city', 'downey')).lower()}_raw.json")
        rows = data if isinstance(data, list) else (
            data.get("listings") or data.get("rows") or data.get("data") or [])
        if not isinstance(rows, list) or not rows:
            sys.exit(f"{capture}: no list of listings found. Top-level keys: "
                     f"{list(data)[:10] if isinstance(data, dict) else type(data).__name__}")
        # Every row, not just the first: a field present on some listings and
        # absent from others is exactly what two fixtures cannot show.
        for i, row in enumerate(rows):
            out[f"{capture.stem}[{i}]"] = row
        print(f"capture: {capture.name} — {len(rows)} listing(s)\n")
    return out


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
    ("bathrooms", "property.bathrooms"):
        "D-106, OPEN. The feed does not send this key — absent from all 301 rows of the "
        "2026-10-01 Downey capture, not merely from the two bundled fixtures. The bath count "
        "lives at `bathsFull`/`bathsHalf`. Listed here so the run stays green while the "
        "DEFECT ITSELF IS UNFIXED: remove this line when extract.py reads the right keys, and "
        "the entry on the board is the source of truth for whether that has happened.",
    ("daysOnMarket", "daysOnMarket"):
        "D-105's retained fallback. `mls.daysOnMarket` is read first, and the "
        "top-level read only runs when that returned None, for deployments "
        "that put it there. Written as an `if dom is None` reassignment rather "
        "than `a or b` ON PURPOSE: a DOM of 0 is a real value and `or` would "
        "discard it, which is the defect one line over in a different costume.",
}

_parser = argparse.ArgumentParser(description=__doc__)
_parser.add_argument(
    "--capture", type=Path, default=None,
    help="a JSON page of real listings (tools/dump_market_snapshot.py's "
         "output). Every row in it joins the two bundled fixtures, so a key "
         "reported absent is absent from real data rather than from a sample "
         "of two.")
_args = _parser.parse_args()

FIXTURES = load_payloads(_args.capture)
#: A key absent from two bundled fixtures is unproven; absent from a real
#: capture of hundreds of rows, it is a finding. The verdict differs.
HAVE_CAPTURE = _args.capture is not None

TARGET = REPO / "apps/worker/src/worker/compute/extract.py"
rows = sweep(TARGET)
idx = {name: index(p) for name, p in FIXTURES.items()}

# Which receivers are the raw row or a sub-object of it?
ROW_VARS = {"p": "", "addr": "address", "pr": "property", "mls": "mls", "sales": "sales"}

print(f"{len(rows)} `.get(\"...\")` reads in {TARGET.relative_to(REPO)}\n")
print(f"{'line':>4}  {'read as':28s} {'expected path':26s} verdict")
print("-" * 96)
problems = []
absent = []
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
    # THE THIRD VERDICT USED TO BE A SHRUG, AND THAT IS HOW A CLEAN RUN
    # COEXISTED WITH AN OPEN DEFECT. `bathrooms` (D-106) exists at NO path in
    # any payload, so it was never "MISREAD" — it was "not in fixtures", which
    # did not fail the run and did not appear in the count. A reader skimming
    # "0 unacknowledged misreads" took that as an all-clear.
    #
    # Against two bundled fixtures the shrug is correct: absent from two files
    # is unproven rather than wrong, and the docstring says so. Against a
    # `--capture` of hundreds of real rows it is not a shrug any more — the
    # feed demonstrably does not send that key. So the verdict splits on
    # whether a capture was supplied, and only the capture-backed one is a
    # finding.
    if bad:
        state, detail = "MISREAD", bad[0][2]
    elif any(v[1] == "ok" for v in verdicts):
        state, detail = "ok", ""
    elif HAVE_CAPTURE:
        state, detail = "ABSENT FROM CAPTURE", ""
    else:
        state, detail = "not in fixtures", ""
    print(f"{lineno:>4}  {recv + '.get(' + repr(key) + ')':28s} {want:26s} {state}"
          + (f"  -> lives at {detail}" if detail else ""))
    if bad:
        problems.append((lineno, recv, key, want, detail))
    elif state == "ABSENT FROM CAPTURE":
        absent.append((lineno, recv, key, want))

print()
new_problems = [x for x in problems if (x[2], x[3]) not in ACKNOWLEDGED]
known = [x for x in problems if (x[2], x[3]) in ACKNOWLEDGED]
for lineno, recv, key, want, detail in known:
    print(f"acknowledged  extract.py:{lineno}  {want}")
    print(f"              {ACKNOWLEDGED[(key, want)]}")
if known:
    print()
new_absent = [x for x in absent if (x[2], x[3]) not in ACKNOWLEDGED]
known_absent = [x for x in absent if (x[2], x[3]) in ACKNOWLEDGED]
for lineno, recv, key, want in known_absent:
    print(f"acknowledged  extract.py:{lineno}  {want}  (absent from the capture)")
    print(f"              {ACKNOWLEDGED[(key, want)]}")
if known_absent:
    print()

if new_problems:
    print(f"{len(new_problems)} MISREAD — the key exists in the payload, at a different path:")
    for lineno, recv, key, want, detail in new_problems:
        print(f"  extract.py:{lineno}  reads {want}   payload has {detail}")
if new_absent:
    print(f"{len(new_absent)} ABSENT FROM CAPTURE — the key is at no path in "
          f"{len(FIXTURES)} real rows:")
    for lineno, recv, key, want in new_absent:
        print(f"  extract.py:{lineno}  reads {want}   the feed sends no such key")
    print("  A read that never resolves is a column that is always empty. Either the "
          "key is\n  wrong or the field is genuinely unavailable — establish which, "
          "then either fix\n  the path or add it to ACKNOWLEDGED with the reason.")
if new_problems or new_absent:
    sys.exit(1)
if HAVE_CAPTURE:
    print(f"no unacknowledged misreads and no unacknowledged absences, across "
          f"{len(FIXTURES)} real rows")
    if known_absent:
        print(f"  ({len(known_absent)} read(s) resolve nowhere and are acknowledged "
              f"above — acknowledged is not fixed.)")
else:
    print("no unacknowledged misreads among keys present in the fixtures")
    print("  (two bundled fixtures only. A key absent from both is UNPROVEN, not "
          "correct —\n  pass --capture with a real dump to turn that into an answer.)")
print()
print(f"{len(skipped)} reads NOT against a raw row (reported, not dropped):")
for lineno, recv, key in skipped:
    print(f"  line {lineno}: {recv}.get({key!r})")
