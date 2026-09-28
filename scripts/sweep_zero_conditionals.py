"""Every Jinja conditional on a value that can honestly be zero.

D-108. `{% if x %}` is falsy for 0, so a real zero renders as nothing.

WHICH NAMES ARE NUMERIC IS DERIVED, NOT GUESSED: build a real context from the
market and property builders, walk it, and collect the leaf paths whose values
are int/float. Then match every bare `{% if ... %}` in every template against
that set. A hand-written list of "numeric-looking names" is the mistake this
project keeps finding.
"""
import ast, re, sys
from pathlib import Path

REPO = Path("/home/user/reportscompany")
sys.path.insert(0, str(REPO / "apps/worker/src"))
TEMPLATES = REPO / "apps/worker/src/worker/templates"

# ── numeric leaf names, from a real built context ───────────────────────────
import importlib.util
spec = importlib.util.spec_from_file_location("m", REPO / "scripts/measure_market_pagination.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
from worker.market_builder import MarketReportBuilder, ALL_REPORT_TYPES

numeric_names = set()

def walk(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)):
                numeric_names.add(k)
            walk(v)
    elif isinstance(obj, list):
        for v in obj[:3]:
            walk(v)

for rt in ALL_REPORT_TYPES:
    d = m.report_data(rt, 6)
    d["price_bands"] = [{"label": "a", "count": 3, "pct": 20}]
    b = MarketReportBuilder(d)
    walk(b._build_stats_context())
    walk(b._build_header_context())
    walk(b._build_listings_context())
    walk(d)

# ── every bare conditional in every template ────────────────────────────────
COND = re.compile(r"\{%-?\s*if\s+(.+?)\s*-?%\}", re.S)
BARE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")

hits = []
for path in sorted(TEMPLATES.rglob("*.jinja2")):
    text = path.read_text(encoding="utf-8")
    for match in COND.finditer(text):
        expr = " ".join(match.group(1).split())
        if not BARE.match(expr):
            continue                      # comparisons, `is not none`, and/or — already explicit
        leaf = expr.split(".")[-1]
        if leaf in numeric_names:
            line = text[:match.start()].count("\n") + 1
            hits.append((str(path.relative_to(TEMPLATES)), line, expr, leaf))

print(f"{len(numeric_names)} numeric leaf names derived from built contexts")
print(f"{len(hits)} bare conditionals on one of them\n")
by_file = {}
for f, line, expr, leaf in hits:
    by_file.setdefault(f, []).append((line, expr))
for f in sorted(by_file):
    print(f"{f}")
    for line, expr in sorted(by_file[f]):
        print(f"   {line:>5}  {{% if {expr} %}}")
print()
print("distinct expressions:", ", ".join(sorted({e for _, _, e, _ in hits})))
