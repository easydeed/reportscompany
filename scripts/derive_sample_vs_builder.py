#!/usr/bin/env python3
"""Does the branding preview's sample data supply what the builder reads?

`api/services/sample_report_data.py` stands in for a real MLS result on the
branding-preview path (`routes/branding_tools._render_sample_html`). A key the
builder READS and nothing on that path SUPPLIES is a preview quietly missing a
section; a key the sample supplies and nothing reads is sample data with no
consumer. D-139's shape, on a surface nobody had compared.

WHY THE READ SET IS NOT JUST AN AST SCAN
The first version of this script attributed `agent_name` and `company_name` to
`report_data`, because `(self.report_data.get("branding") or {}).get(
"agent_name")` is a `.get` whose chain contains `report_data` — the inner key
belongs to `branding`, not to the top level. Reporting those as missing would
have been two false positives out of seven, in a script written to find a
divergence. So a read is only counted when `report_data` is the DIRECT
receiver.
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

#: Read by the builder and supplied by `tasks.py` on the production path only.
#: Listed so the script's output distinguishes "nothing supplies this" from
#: "the preview does not".
PRODUCTION_ONLY = {"closed_history", "closed_history_truncated",
                   "price_bands_note", "ai_insights"}


def direct_report_data_reads(path: Path):
    """Keys read with `report_data` as the DIRECT receiver."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = set()

    def is_report_data(node) -> bool:
        # `self.report_data` or `report_data`, and nothing further chained.
        if isinstance(node, ast.Attribute):
            return node.attr == "report_data"
        return isinstance(node, ast.Name) and node.id == "report_data"

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if (getattr(fn, "attr", None) == "get" and node.args
                    and is_report_data(getattr(fn, "value", None))
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                out.add(node.args[0].value)
        if isinstance(node, ast.Subscript) and is_report_data(node.value):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                out.add(node.slice.value)
    return out


def main() -> int:
    sys.path.insert(0, str(ROOT / "apps/worker/src"))
    sys.path.insert(0, str(ROOT / "apps/api/src"))
    from api.services.sample_report_data import (
        SUPPORTED_SAMPLE_REPORT_TYPES, get_sample_data,
    )

    reads = direct_report_data_reads(MB)
    report = {"builder_reads": sorted(reads),
              "injected_by_the_route": sorted(INJECTED_BY_THE_ROUTE),
              "per_type": {}}

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
    report["supplied_but_read_by_nothing"] = sorted(union - reads)

    # The reverse half needs the TEMPLATES too: a key the builder does not
    # read may still be interpolated by `market.jinja2`. Checked by substring
    # rather than by parsing, deliberately — a false NEGATIVE here (a key
    # wrongly called live) is the safe direction for a list of things to
    # delete.
    market_templates = "\n".join(
        p.read_text(encoding="utf-8")
        for p in (ROOT / "apps/worker/src/worker/templates/market").rglob("*.jinja2"))
    report["supplied_read_by_nothing_at_all"] = sorted(
        k for k in report["supplied_but_read_by_nothing"]
        if k not in market_templates)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
