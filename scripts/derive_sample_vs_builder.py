#!/usr/bin/env python3
"""Does the branding preview's sample data supply what the builder reads?

`api/services/sample_report_data.py` stands in for a real MLS result on the
branding-preview path (`routes/branding_tools._render_sample_html`). A key the
builder READS and nothing on that path SUPPLIES is a preview quietly missing a
section; a key the sample supplies and nothing reads is sample data with no
consumer. D-139's shape, on a surface nobody had compared.

TWO CORRECTIONS THIS SCRIPT HAS ALREADY NEEDED, IN OPPOSITE DIRECTIONS
----------------------------------------------------------------------
1. FALSE POSITIVES. The first version attributed `agent_name` and
   `company_name` to `report_data`, because `(self.report_data.get("branding")
   or {}).get("agent_name")` is a `.get` whose chain contains `report_data` —
   the inner key belongs to `branding`. Two false positives out of seven, in a
   script written to find a divergence. So a read was narrowed to count only
   when `report_data` is the DIRECT receiver.

2. A FALSE NEGATIVE BOUGHT BY THAT FIX. `market_builder.py:435` does
   `data = self.report_data` and then reads `data.get("filters_label")` at 452
   — the masthead subtitle. The direct-receiver rule cannot see it, so
   `filters_label` was reported as read by nothing and the test pinned that.
   Reads are now followed through LOCAL ALIASES of `report_data` within the
   function that assigns them.

The pair is the lesson: narrowing a scan to kill false positives moves the
error to the other side of the ledger, and only measuring both directions
catches it.

AND THE SCOPE OF THE REVERSE CHECK IS PART OF ITS CLAIM (§0.6)
--------------------------------------------------------------
The reverse half used to scan the market Jinja tree alone and name its result
`supplied_read_by_nothing_at_all`. `period_label` and `report_date` are read
SEVEN TIMES in `apps/web/lib/templates.ts`, the print/social surface whose own
docstring reads *"NOT DEAD CODE — do not delete… Two archived documents
asserted this route had been removed. Both were wrong."* A one-surface scan
published as a repo-wide verdict is D-131 exactly, and D-131 was cited three
times as a reason to delete.

So the consumer surfaces are ENUMERATED, each one is asserted to exist, and
the output says WHICH surface reads each key rather than whether "anything"
does. A key with no surface is reported as read by none of THESE surfaces,
which is a claim the script can actually support.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MB = ROOT / "apps/worker/src/worker/market_builder.py"

#: Supplied by `_render_sample_html`, not by `get_sample_data`. A real part of
#: the preview path, so not a divergence.
INJECTED_BY_THE_ROUTE = {"branding", "accent_color", "theme_id"}

#: Read by the builder and supplied by `tasks.py` on the production path only
#: (`tasks.py:1753`). Listed so the output distinguishes "nothing supplies
#: this" from "the preview does not".
PRODUCTION_ONLY = {"closed_history", "closed_history_truncated",
                   "price_bands_note", "ai_insights"}

#: Every surface that can consume a key off the market result. Each is
#: checked to exist, because a renamed path would silently shrink the read
#: set and turn a live key into a deletion candidate.
#:
#: `apps/web/**` is the legacy print/social build. It renders no customer PDF
#: — `tasks.py:1775` always passes `html_content`, so `pdf_engine`'s
#: `/print/{run_id}` branch is unreachable from the market path, which is
#: D-101's fix — but the route still serves HTML on request and still reads
#: these keys. Unreachable-as-a-PDF-fallback is not the same claim as unread.
CONSUMER_SURFACES = {
    "market jinja2": ["apps/worker/src/worker/templates/market/**/*.jinja2"],
    "legacy print templates": ["apps/web/templates/*.html",
                               "apps/web/templates/social/*.html"],
    "legacy print mapper": ["apps/web/lib/templates.ts"],
}


def report_data_reads(path: Path):
    """Keys read off `report_data`, following local aliases of it.

    Returns `(direct, via_alias)` so a caller can see which rule found what.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    direct: set[str] = set()
    via_alias: dict[str, str] = {}

    def is_report_data(node) -> bool:
        # `self.report_data` or `report_data`, and nothing further chained.
        if isinstance(node, ast.Attribute):
            return node.attr == "report_data"
        return isinstance(node, ast.Name) and node.id == "report_data"

    def receiver_and_key(node):
        if (isinstance(node, ast.Call)
                and getattr(node.func, "attr", None) == "get" and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            return getattr(node.func, "value", None), node.args[0].value
        if (isinstance(node, ast.Subscript)
                and isinstance(node.slice, ast.Constant)
                and isinstance(node.slice.value, str)):
            return node.value, node.slice.value
        return None, None

    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # Locals bound to `report_data` in this function. Scoped per function
        # deliberately: a name meaning `report_data` in one method says
        # nothing about the same name in another.
        aliases = {t.id
                   for n in ast.walk(fn) if isinstance(n, ast.Assign)
                   and is_report_data(n.value)
                   for t in n.targets if isinstance(t, ast.Name)}
        for n in ast.walk(fn):
            recv, key = receiver_and_key(n)
            if key is None:
                continue
            if is_report_data(recv):
                direct.add(key)
            elif isinstance(recv, ast.Name) and recv.id in aliases:
                via_alias.setdefault(key, f"{fn.name}:{n.lineno} (via `{recv.id}`)")

    # Reads at module scope, outside any function.
    for n in ast.walk(tree):
        recv, key = receiver_and_key(n)
        if key is not None and is_report_data(recv):
            direct.add(key)

    return direct, {k: v for k, v in via_alias.items() if k not in direct}


def surface_text():
    """`{surface: text}` for every enumerated consumer surface.

    Raises if a surface matches no file: an empty surface silently shrinks the
    read set, which is the direction that produces a deletion candidate.
    """
    out = {}
    for name, globs in CONSUMER_SURFACES.items():
        paths = [p for g in globs for p in ROOT.glob(g)]
        if not paths:
            raise SystemExit(
                f"consumer surface {name!r} matched no files ({globs}). A "
                f"moved or renamed surface makes live keys look dead — fix "
                f"the glob, do not let the scan shrink."
            )
        out[name] = "\n".join(p.read_text(encoding="utf-8") for p in paths)
    return out


def main() -> int:
    sys.path.insert(0, str(ROOT / "apps/worker/src"))
    sys.path.insert(0, str(ROOT / "apps/api/src"))
    from api.services.sample_report_data import (
        SUPPORTED_SAMPLE_REPORT_TYPES, get_sample_data,
    )

    direct, via_alias = report_data_reads(MB)
    reads = direct | set(via_alias)
    report = {
        "builder_reads": sorted(reads),
        "builder_reads_via_alias": via_alias,
        "injected_by_the_route": sorted(INJECTED_BY_THE_ROUTE),
        "consumer_surfaces": sorted(CONSUMER_SURFACES),
        "per_type": {},
    }

    union = set()
    for rt in SUPPORTED_SAMPLE_REPORT_TYPES:
        keys = set(get_sample_data(rt, city="Irvine", lookback_days=30))
        union |= keys
        missing = sorted(reads - keys - INJECTED_BY_THE_ROUTE)
        report["per_type"][rt] = {
            "n_keys": len(keys),
            "missing": missing,
            "missing_and_not_production_only": sorted(
                set(missing) - PRODUCTION_ONLY),
        }

    report["union_n_keys"] = len(union)
    report["read_but_supplied_by_nothing"] = sorted(
        reads - union - INJECTED_BY_THE_ROUTE)
    report["supplied_but_not_read_by_the_builder"] = sorted(union - reads)

    # The reverse half, per surface. Substring rather than parsing,
    # deliberately: a false NEGATIVE here (a key wrongly called live) is the
    # safe direction for a list of things somebody might delete.
    texts = surface_text()
    read_by = {}
    for k in sorted(union - reads):
        where = sorted(name for name, text in texts.items() if k in text)
        read_by[k] = where
    report["supplied_not_read_by_builder_read_by"] = read_by
    report["supplied_read_by_no_enumerated_surface"] = sorted(
        k for k, where in read_by.items() if not where)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
