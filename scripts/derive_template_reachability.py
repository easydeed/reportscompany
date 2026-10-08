#!/usr/bin/env python3
"""Which template files render, derived from the builders' own entry points.

WHY THIS EXISTS, AND WHY IT IS NOT A LIST
D-131 recorded a "dead template tree" under `templates/property/`. The entry
and the documents built on it say **"everything in `_base/` renders
nowhere"** — unqualified — and that sentence is in the handover that went to
Design. It has been cited three times as a reason to delete.

THERE ARE TWO `_base/` DIRECTORIES.

    templates/property/_base/   dead: nothing reaches it
    templates/market/_base/     LIVE: `market/market.jinja2` is one line,
                                `{% extends '_base/base.jinja2' %}`, and that
                                base imports `_base/macros.jinja2`. It is the
                                whole of every market report.

So "delete the `_base/` tree" is true of one and would delete the market
report's entire base. The original classification was not wrong about
`property/_base/` — it was written while looking at `templates/property/`,
and the sentence it produced does not say so.

This script answers the question by WALKING, from the roots the builders
actually render, so "dead" is a derived set per surface rather than a claim
about a directory name. Run it before acting on any statement that a template
is unreachable.

A TEMPLATE CAN BE A ROOT WITHOUT ANY JINJA REFERENCING IT
The first version of this script followed `extends`/`include`/`import`/`from`
only, and reported `market/_base/page_header.jinja2` and `page_footer.jinja2`
— 217 lines — as dead. They are not. `MarketReportBuilder.render_page_header_html`
does `self.env.get_template("_base/page_header.jinja2")` and `tasks.py` passes
both to `render_pdf` as PDFShift's native header and footer. They render on
every page of every market report.

**That is D-131's mistake, repeated one day after correcting it**: a
reachability claim that misses a dependency because it only looked at one kind
of reference. Filing a defect on those two files would have been the same
error with the surfaces swapped. So the roots are DERIVED TOO — every
`get_template("...")` literal in the worker's Python is a root — rather than
listed from the ones the author happened to know about.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jinja2 import Environment, nodes

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "apps/worker/src/worker/templates"

REFS = (nodes.Include, nodes.Extends, nodes.Import, nodes.FromImport)


def referenced(path: Path):
    """Template names this file reaches, as written."""
    tree = Environment().parse(path.read_text(encoding="utf-8"))
    out = []
    for kind in REFS:
        for node in tree.find_all(kind):
            value = getattr(getattr(node, "template", None), "value", None)
            for name in ([value] if isinstance(value, str) else list(value or [])):
                if isinstance(name, str):
                    out.append(name)
    return out


def walk(surface_dir: Path, roots):
    """Everything reachable from `roots`, resolved against `surface_dir`.

    Jinja resolves a template name against the loader's directory, and each
    builder gives its loader a different one — `templates/property` for the
    property reports, `templates/market` for the market ones. So the same
    string `'_base/base.jinja2'` names two different files depending on which
    builder is rendering, which is the whole of why the unqualified sentence
    is dangerous.
    """
    seen, stack = set(), list(roots)
    while stack:
        path = stack.pop()
        if path in seen:
            continue
        if not path.exists():
            raise SystemExit(f"{path} is referenced and does not exist")
        seen.add(path)
        for name in referenced(path):
            stack.append(surface_dir / name)
    return seen


def python_roots():
    """Template names passed to `get_template(...)` anywhere in the worker.

    Parsed with Python's own parser, not grepped — a `get_template` inside a
    comment or a docstring is not a call. Returns the names; which surface each
    belongs to is decided by whether the file resolves, because the same name
    can exist under both loaders.

    AND NOT ONLY LITERALS, WHICH IS WHERE THIS WAS WRONG. The first version
    collected `ast.Constant` arguments only. `market_builder` renders Design's
    page with

        template = self.env.get_template(
            V2_TEMPLATE_PATH if self.report_type in V2_KINDS else TEMPLATE_PATH)

    — module constants, not literals — so `_v2/report.jinja2` came back
    UNREACHABLE on its first render, and the gate's own message asked the right
    question: "are they reached from PYTHON?"

    That message exists because of D-131, where following only Jinja edges
    reported two live templates as dead. This is the same shape one level in:
    following only literal arguments misses a template referenced through a
    name. So module-level string constants are resolved too, and a `Name` or
    `Attribute` argument that resolves to nothing is reported rather than
    dropped — an argument the scan cannot follow is the thing that produced
    both of these.
    """
    import ast
    names = set()
    unresolved = []
    for path in (ROOT / "apps/worker/src").rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        # Module-level `NAME = "literal"`, which is how a template path is
        # spelled when it is also used for a dispatch decision.
        consts = {}
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = (node.targets if isinstance(node, ast.Assign)
                           else [node.target])
                value = node.value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    for t in targets:
                        if isinstance(t, ast.Name):
                            consts[t.id] = value.value

        def collect(arg):
            """One argument, which may be a literal, a name, or a ternary."""
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                names.add(arg.value)
                return True
            if isinstance(arg, ast.Name) and arg.id in consts:
                names.add(consts[arg.id])
                return True
            if isinstance(arg, ast.IfExp):
                # `a if cond else b` — BOTH branches are roots. Only taking one
                # is how a conditional render path goes missing.
                return collect(arg.body) and collect(arg.orelse)
            return False

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if getattr(node.func, "attr", None) != "get_template":
                continue
            for arg in node.args:
                if not collect(arg):
                    unresolved.append(
                        f"{path.relative_to(ROOT)}:{getattr(arg, 'lineno', '?')}")
    if unresolved:
        # TWO SITES ARE EXPECTED AND BOTH ARE COVERED ELSEWHERE, so the warning
        # is a list to read rather than a list of defects:
        #   property_builder.py — `get_template(template_path)`, a local from
        #     `THEME_TEMPLATES`, which this derivation imports directly.
        #   email/template.py — `get_template(f"blocks/{name}.jinja2")` on
        #     `_BLOCK_ENV`, a third loader that is neither market nor property.
        # A THIRD entry appearing is the thing to look at.
        print(f"WARNING: get_template arguments this scan could not resolve: "
              f"{unresolved}. A template reached only through one of these "
              f"will be reported as dead. Two are expected — see the note "
              f"above `python_roots`.", file=sys.stderr)
    return sorted(names)


def main() -> int:
    sys.path.insert(0, str(ROOT / "apps/worker/src"))
    from worker.theme_registry import THEME_TEMPLATES

    extra = python_roots()
    report = {"get_template_literals": extra}

    # ── property ────────────────────────────────────────────────────────
    prop_dir = TEMPLATES / "property"
    prop_roots = ([prop_dir / v for v in THEME_TEMPLATES.values()]
                  + [prop_dir / n for n in extra if (prop_dir / n).exists()])
    prop_live = walk(prop_dir, prop_roots)
    prop_all = set(prop_dir.rglob("*.jinja2"))

    # ── market ──────────────────────────────────────────────────────────
    # One root. `MarketReportBuilder` renders `market.jinja2` for every
    # report type; the layout is chosen inside the template, not by file.
    market_dir = TEMPLATES / "market"
    market_roots = ([market_dir / "market.jinja2"]
                    + [market_dir / n for n in extra if (market_dir / n).exists()])
    market_live = walk(market_dir, market_roots)
    market_all = set(market_dir.rglob("*.jinja2"))

    def describe(name, live, every, base):
        dead = sorted(every - live)
        lines = lambda ps: sum(len(p.read_text(encoding="utf-8").splitlines())
                               for p in ps)
        return {
            "live_files": sorted(str(p.relative_to(base)) for p in live),
            "live_lines": lines(sorted(live)),
            "dead_files": sorted(str(p.relative_to(base)) for p in dead),
            "dead_lines": lines(dead),
            "_base_is_live": any("_base/" in str(p.relative_to(base))
                                 for p in live),
        }

    report["property"] = describe("property", prop_live, prop_all, prop_dir)
    report["market"] = describe("market", market_live, market_all, market_dir)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
