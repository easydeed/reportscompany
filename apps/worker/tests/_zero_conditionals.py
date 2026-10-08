"""Every place a template decides whether to render a number by its truthiness.

D-108. Jinja treats `0` as falsy, so `{% if value %}` hides a real zero: a
studio shows no bed count, a same-day sale shows no DOM, a market with nothing
for sale shows no months-of-supply. The value is present and interesting and
the page omits it.

WHY THIS IS A MODULE AND NOT FORTY FIXES IN FORTY PLACES. The market and
property templates are being replaced. Forty corrected conditionals leave with
them; a checker that walks whatever templates exist does not. So nothing here
is keyed to a file, a line, a class name or a fragment of markup:

  * the numeric names are DERIVED from what the builders actually put in a
    context — walk the built dicts, keep every int/float leaf. A new template
    set reads the same contexts, so the same names are in scope for it.
  * templates are found by walking the templates tree, not by a list.
  * each one is parsed with JINJA'S OWN PARSER. No regex, no substring match.
    §0.6 has four separate entries about substring false positives in this
    repo; an AST cannot produce one.
  * "this zero is handled" is judged STRUCTURALLY — the conditional has an
    `{% else %}` — not by looking for the word "Studio" in the output. Copy
    can change without the guard going quiet, and a new template that renders
    zero some other way passes on its own merits.

FOUR SYNTAXES, because this defect has appeared in all four in this repo:

  {% if x %}…{% endif %}             hides the field        (D-108)
  {{ x if x else '-' }}              same thing, expression (D-108)
  {{ bands | selectattr('count') }}  drops the zero rows    (band chart, twice)
  [r["dom"] for r in rows
            if r.get("dom")]         drops them from the    (D-108's Python
                                     STATISTIC                half, 11 sites)

The fourth is the worst of them, because it is silent: a template that hides a
zero is visibly missing a chip, while an average that excludes its zeros just
reads a little high and nothing on the page says so.

`EXEMPT` names the expressions where zero is not reachable, each with the
reason. It is checked for staleness: an entry no template uses any more is a
failure, so the list cannot quietly outlive the thing it excused.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from typing import Iterable, NamedTuple

from jinja2 import Environment, nodes

REPO = Path(__file__).resolve().parents[3]
TEMPLATES = REPO / "apps/worker/src/worker/templates"


# ── expressions where a zero cannot occur, and why ──────────────────────────
# Keyed by LEAF NAME (`sqft`) so a replacement template inherits the exemption
# whether it writes `listing.sqft`, `l.sqft` or `row.sqft` — or by the full
# dotted path when the claim is true on one surface and not another. Adding an
# entry means claiming the value cannot honestly be zero; say why.
#
# Checked for staleness below: an entry nothing uses any more is a failure, so
# the list cannot quietly outlive the thing it excused, and cannot be padded
# in advance to pre-clear a defect that has not been filed.
EXEMPT = {
    "sqft": "0 sqft on a dwelling is bad data; land carries None",
    "baths": "0 baths is not a habitable dwelling — and D-106 means the "
             "market field is None today regardless",
    "bathrooms": "as baths",
    "list_price": "a $0 list price is bad data, not a price",
    "close_price": "a $0 sale is bad data, not a sale",
    "price": "as list_price",
    "price_per_sqft": "a market with no sales has nothing to divide by, so "
                      "the metric is None rather than 0",
    # D-178 replaced the raw key with a normalised one, and the exemption's
    # ARGUMENT got stronger rather than being carried over. It used to be "a 0
    # ratio means every sale closed at $0" — an argument about plausibility,
    # which is the weakest kind on this list. `_ratio_as_percent` now returns
    # None for anything zero or non-numeric, so the value reaching the template
    # CANNOT be 0: the truthiness test is safe by construction, not by the
    # input being unlikely.
    "list_to_sale_pct": "the producer cannot emit 0 — `_ratio_as_percent` "
                        "returns None for a zero or non-numeric ratio, so "
                        "falsy means absent and nothing else (D-178)",
    "year_built": "year 0 is not a year",
    "lot_size": "0 lot size is missing parcel data",
    # Surface-specific. `beds` on the market report IS fixed (renders
    # "Studio"); `property.bedrooms` is not, and deliberately:
    # property_builder collapses None to 0 (`sitex_data.get("bedrooms") or 0`),
    # so on that surface a 0 does not yet mean a studio and rendering "Studio"
    # would invent data. Filed as D-109. This entry is here so the next person
    # does not "fix" the template into inventing it.
    "property.bedrooms": "D-109: property_builder collapses None to 0, so 0 "
                         "does not mean studio on this surface yet",
}


class Finding(NamedTuple):
    template: str
    line: int
    expr: str
    kind: str        # "if" | "ternary" | "filter" | "comprehension"

    def __str__(self) -> str:
        shape = {
            "if": "{%% if %s %%} with no {%% else %%}",
            "ternary": "{{ … if %s else … }}",
            "filter": "selectattr(%r)",
            "comprehension": "[… for … if %s]",
        }[self.kind]
        return f"{self.template}:{self.line}  " + (shape % self.expr)


# ── which names hold numbers: derived from real built contexts ──────────────
def numeric_leaf_names() -> set[str]:
    """Every dict key the builders fill with an int or a float.

    Derived, never listed. A hand-written set of "numeric-looking names" is
    the mistake this repo keeps re-finding, and it goes stale the moment a
    builder adds a field.
    """
    import sys
    src = str(REPO / "apps/worker/src")
    if src not in sys.path:
        sys.path.insert(0, src)

    spec = importlib.util.spec_from_file_location(
        "_measure_market_pagination", REPO / "scripts/measure_market_pagination.py"
    )
    measure = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(measure)
    from worker.market_builder import ALL_REPORT_TYPES, MarketReportBuilder
    from worker.property_builder import PropertyReportBuilder

    names: set[str] = set()

    def walk(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, bool):
                    continue          # a bool is not a measurement
                if isinstance(value, (int, float)):
                    names.add(key)
                walk(value)
        elif isinstance(obj, list):
            for value in obj[:3]:
                walk(value)

    for report_type in ALL_REPORT_TYPES:
        data = measure.report_data(report_type, 6)
        data["price_bands"] = [{"label": "a", "count": 3, "pct": 20}]
        builder = MarketReportBuilder(data)
        walk(builder._build_stats_context())
        walk(builder._build_header_context())
        walk(builder._build_listings_context())
        walk(data)

    # The property report too, or its own numeric fields are invisible here and
    # the guard silently covers half the templates it walks.
    prop = PropertyReportBuilder({})
    walk(prop._build_property_context())
    walk(prop._build_stats_context())

    # AND A POPULATED ONE, BECAUSE "AN EMPTY INPUT STILL NAMES THEM ALL" STOPPED
    # BEING TRUE. That was this block's stated premise and it rested on the
    # builder defaulting every numeric to 0. D-119 changed that deliberately:
    # a Low/Medium/High column with no listing behind it now renders `-`
    # rather than `$0`, so on an EMPTY input `stats.low.price` and its
    # siblings are strings, `price` drops out of this set, and two real
    # comprehension findings in `tasks.py` silently stopped being reported.
    #
    # Nothing failed. The audit just got quieter, which is the failure mode
    # this whole file exists to prevent — so the set is derived from a
    # populated context as well as an empty one, and a field that is only
    # numeric when there is data to put in it is still named.
    populated = PropertyReportBuilder({
        "sitex_data": {"last_sale_price": 369000, "sqft": 786, "bedrooms": 2},
        "comparables": [{"price": 470000, "sqft": 800, "year_built": 1950},
                        {"price": 590000, "sqft": 900, "year_built": 1960},
                        {"price": 635000, "sqft": 1000, "year_built": 1970}],
    })
    walk(populated._build_property_context())
    walk(populated._build_stats_context())
    return names


# ── the walk ────────────────────────────────────────────────────────────────
def _dotted(node) -> str | None:
    """`listing.beds` for a plain name/attribute chain, else None.

    Anything else — a comparison, `is not none`, `and`/`or`, a filter, a call —
    is already explicit about what it tests and is not this defect.
    """
    parts: list[str] = []
    while isinstance(node, nodes.Getattr):
        parts.append(node.attr)
        node = node.node
    if isinstance(node, nodes.Name):
        parts.append(node.name)
        return ".".join(reversed(parts))
    return None


def _if_chains(tree) -> Iterable[tuple[nodes.If, bool]]:
    """Each `If` node with whether ITS CHAIN has an else.

    `{% if a %}…{% elif b %}…{% else %}…{% endif %}` parses as one `If` whose
    `elif_` holds the b-node and whose `else_` holds the tail. The else covers
    the whole chain, so the elif must not be judged on its own empty `else_` —
    the first version of this walk failed two correct fallback chains that way.
    """
    # `find_all` reaches elif nodes too, so visit chain roots only and hand
    # each elif the ROOT's coverage. Yielding both ways reported every correct
    # fallback chain as a defect.
    in_a_chain = {
        id(branch)
        for node in tree.find_all(nodes.If)
        for branch in node.elif_
    }
    for node in tree.find_all(nodes.If):
        if id(node) in in_a_chain:
            continue
        covered = bool(node.else_)
        yield node, covered
        for branch in node.elif_:
            yield branch, covered


def audit_template(path: Path, numeric: set[str], env: Environment) -> list[Finding]:
    rel = str(path.relative_to(TEMPLATES))
    tree = env.parse(path.read_text(encoding="utf-8"))
    found: list[Finding] = []

    def numeric_expr(node) -> str | None:
        expr = _dotted(node)
        if expr is None:
            return None
        return expr if expr.split(".")[-1] in numeric else None

    for node, covered in _if_chains(tree):
        if covered:
            continue                      # zero has a rendering of its own
        expr = numeric_expr(node.test)
        if expr:
            found.append(Finding(rel, node.lineno, expr, "if"))

    for node in tree.find_all(nodes.CondExpr):
        if node.expr2 is None:
            continue                      # no else branch to compare against
        expr = numeric_expr(node.test)
        # `{{ x if x else '-' }}` only: a ternary testing a DIFFERENT value is
        # a deliberate choice, not a truthiness slip.
        if expr and _dotted(node.expr1) == expr:
            found.append(Finding(rel, node.lineno, expr, "ternary"))

    for node in tree.find_all(nodes.Filter):
        if node.name not in ("selectattr", "rejectattr"):
            continue
        # One string argument = a bare truthiness test on that attribute.
        # With a second (`selectattr('count', 'gt', 0)`) the test is explicit.
        if len(node.args) == 1 and isinstance(node.args[0], nodes.Const):
            attr = node.args[0].value
            if isinstance(attr, str) and attr.split(".")[-1] in numeric:
                found.append(Finding(rel, node.lineno, attr, "filter"))
    return found


def audit_all() -> list[Finding]:
    numeric = numeric_leaf_names()
    env = Environment()
    findings: list[Finding] = []
    for path in sorted(TEMPLATES.rglob("*.jinja2")):
        findings.extend(audit_template(path, numeric, env))
    return findings


def _exempt_key(expr: str) -> str | None:
    """The EXEMPT entry covering `expr`: the full path first, then the leaf."""
    if expr in EXEMPT:
        return expr
    leaf = expr.split(".")[-1]
    return leaf if leaf in EXEMPT else None


def unexempt(findings: Iterable[Finding]) -> list[Finding]:
    return [f for f in findings if _exempt_key(f.expr) is None]


def unused_exemptions(findings: Iterable[Finding]) -> list[str]:
    """EXEMPT entries no template relies on. See EXEMPT's note on staleness."""
    used = {_exempt_key(f.expr) for f in findings}
    return sorted(set(EXEMPT) - used)


# ── the same defect in Python ───────────────────────────────────────────────
# `[r["dom"] for r in rows if r.get("dom")]` drops every zero from the list it
# is about to average. Walked with `ast` for the same reason the templates are
# walked with Jinja's parser: a regex over `.get(` would match the reads too.
PY_ROOTS = ("apps/worker/src/worker",)


def _filter_key(node) -> str | None:
    """The key a comprehension filter tests, when the filter is bare.

    `if r.get("dom")` and `if r["dom"]` only. `if r.get("dom") is not None`,
    `if r.get("dom") > 0` and anything compound are already explicit.
    """
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get" and len(node.args) == 1
            and isinstance(node.args[0], ast.Constant)):
        key = node.args[0].value
    elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
        key = node.slice.value
    else:
        return None
    return key if isinstance(key, str) else None


def audit_python(numeric: set[str] | None = None) -> list[Finding]:
    import ast as _ast
    numeric = numeric_leaf_names() if numeric is None else numeric
    found: list[Finding] = []
    for root in PY_ROOTS:
        for path in sorted((REPO / root).rglob("*.py")):
            if "__pycache__" in str(path):
                continue
            try:
                tree = _ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            rel = str(path.relative_to(REPO))
            for node in _ast.walk(tree):
                if not isinstance(node, (_ast.ListComp, _ast.SetComp, _ast.GeneratorExp)):
                    continue
                for gen in node.generators:
                    for cond in gen.ifs:
                        key = _filter_key(cond)
                        if key and key.split(".")[-1] in numeric:
                            found.append(Finding(rel, cond.lineno, key, "comprehension"))
    return sorted(set(found))
