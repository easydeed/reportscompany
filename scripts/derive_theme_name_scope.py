#!/usr/bin/env python3
"""Derive the cost of RENAMING a theme. Read-only; run from the repo root.

Jerry's question (2026-10-05): "how many places does a theme NAME appear as
opposed to an id, and is a rename one mapping change or a sweep?"

It is answered by counting, not estimating. Every number in
docs/THEME_RENAME_SCOPE.md comes from here — a count assembled by eye is a
count that drifts, which is what the 132-vs-146 correction was.

The first version of this script DISCOVERED NOTHING: it asserted a
hand-written list of mapping sites, so it could only confirm what had already
been found by grepping. It missed `scripts/qa_generate_all_reports.py`, which
the single-source gate then caught. This version discovers instead.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "apps/worker/src/worker/themes.json"

TREES = ("apps/api/src", "apps/web", "apps/worker/src", "apps/worker/scripts",
         "scripts", "db/migrations", "tests")
SKIP = ("node_modules", ".next", "dist", "build", "__pycache__", ".git",
        "output", "outputs", "_intake", "tmp")
CODE = (".py", ".ts", ".tsx", ".sql", ".json")

#: `bold` is a font weight far more often than a theme. Lines matching any of
#: these are not counted: the first pass over `apps/` returned 523 `bold`
#: hits, 469 of them CSS.
FONT_WEIGHT = re.compile(
    r"font-weight|font_weight|fontWeight|font-bold|bold-webfont|NexaBold"
    r"|Montserrat-Bold|--bold|text-bold|\bbolder\b|bariol_bold|Bebas",
    re.I,
)


def names():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    live = [t["name"] for t in reg["themes"]]
    retired = [t["name"] for t in reg["retired"]]
    return live, retired, reg


def files():
    for tree in TREES:
        for p in (ROOT / tree).rglob("*"):
            if p.suffix in CODE and not any(s in p.parts for s in SKIP):
                yield p


def rel(p):
    return str(p.relative_to(ROOT))


def main() -> int:
    live, retired, reg = names()
    allnames = live + retired
    # A BACKTICK IS NOT A STRING DELIMITER IN PYTHON, and counting it as one
    # made this derivation report prose as code. A comment reading "the schema
    # advertised `teal` as the default" is a sentence ABOUT the cut, not a
    # fifth site holding the name — and two such comments, written while
    # recording D-174, pushed the file count past its own ceiling and failed
    # the build. Python has no backtick literal at all, so the only backticks
    # in a `.py` file are prose. TypeScript's template literals are real, so
    # `.ts`/`.tsx` keep theirs.
    #
    # Substring-is-not-a-construct, instance thirteen, in the gate written to
    # count the other twelve.
    quoted_py = re.compile(r"[\"'](" + "|".join(allnames) + r")[\"']")
    quoted_web = re.compile(r"[\"'`](" + "|".join(allnames) + r")[\"'`]")
    bare_key = re.compile(r"\b(" + "|".join(allnames) + r")\s*:")
    report: dict = {
        "live": live,
        "retired": retired,
        "default_id": reg["default_id"],
    }

    # ── A. the NAME as a string in code ──────────────────────────────────
    by_file: dict = {}
    for p in files():
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits = []
        for n, line in enumerate(text.splitlines(), 1):
            if FONT_WEIGHT.search(line):
                continue
            quoted = quoted_py if p.suffix == ".py" else quoted_web
            for m in list(quoted.finditer(line)) + list(bare_key.finditer(line)):
                hits.append((n, m.group(1)))
        if hits:
            by_file[rel(p)] = hits
    report["name_in_code"] = {k: len(v) for k, v in sorted(
        by_file.items(), key=lambda kv: -len(kv[1]))}
    report["name_in_code_total"] = sum(len(v) for v in by_file.values())
    report["name_in_code_files"] = len(by_file)

    # ── B. the NAME in a path on disk ────────────────────────────────────
    paths = []
    for p in ROOT.rglob("*"):
        if any(s in p.parts for s in SKIP):
            continue
        if any(p.name.lower().startswith(n) for n in allnames):
            paths.append(rel(p))
    report["paths_named_after_a_theme"] = sorted(paths)

    # ── C. the NAME inside a live template ──────────────────────────────
    tdir = ROOT / "apps/worker/src/worker/templates/property"
    # THE CHAIN, resolved by parsing, because a theme on the shared
    # architecture is an entry file plus `_v2/report.jinja2`. Reading the
    # entry file alone reported bold at 3 self-references and no `<title>`,
    # which is true of thirty-four lines of `{% set %}` and not of the
    # document they render.
    def _chain(path):
        from jinja2 import Environment, nodes
        out, stack = [], [path]
        while stack:
            cur = stack.pop(0)
            if cur in out:
                continue
            out.append(cur)
            tree = Environment().parse(cur.read_text(encoding="utf-8"))
            for kind in (nodes.Include, nodes.Extends, nodes.Import,
                         nodes.FromImport):
                for node in tree.find_all(kind):
                    value = getattr(getattr(node, "template", None), "value", None)
                    for name in ([value] if isinstance(value, str)
                                 else list(value or [])):
                        if isinstance(name, str):
                            stack.append(tdir / name)
        return out

    tmpl = {}
    for t in reg["themes"]:
        # `chain_files`, not `files` — the local shadowed the module-level
        # `files()` generator and the sweep above it raised
        # UnboundLocalError. Python's scoping, not a logic error, and the
        # kind a name chosen for brevity buys.
        chain_files = _chain(tdir / t["template"])
        text = "\n".join(f.read_text(encoding="utf-8") for f in chain_files)
        own = re.compile(rf"\b{t['name']}\b", re.I)
        tmpl[t["name"]] = {
            "files": len(chain_files),
            "self_references": len(own.findall(text)),
            "css_custom_properties": len(re.findall(rf"--{t['name']}\b", text, re.I)),
            "title_tag": "<title>" in text,
        }
    report["inside_live_templates"] = tmpl

    # ── D. the NAME as a database identifier ────────────────────────────
    ident = set()
    for p in (ROOT / "db/migrations").glob("*.sql"):
        ident |= set(re.findall(
            r"\btheme_(?:" + "|".join(allnames) + r")\b", p.read_text()))
    report["db_identifiers"] = sorted(ident)

    # ── E. the NAME as a persisted VALUE ────────────────────────────────
    # `report_generations.theme_id` is VARCHAR(20). The market wizard POSTs a
    # NAME into it; `routes/reports.py` writes `str(<id>)` into the same
    # column. So the column holds a mix of "bold" and "5" — and nothing reads
    # it (D-164), which is what makes a rename cheap rather than a migration.
    g = (ROOT / "db/migrations/0046_market_report_theme.sql").read_text()
    report["name_valued_columns"] = (
        ["report_generations.theme_id VARCHAR(20) — written as a name by the "
         "market wizard, as a stringified id by routes/reports.py, READ BY "
         "NOTHING (D-164)"]
        if "theme_id VARCHAR(20)" in g else []
    )

    # ── F. the NAME in a test baseline ──────────────────────────────────
    base = (ROOT / "apps/worker/tests/pdf_contrast_baseline.txt").read_text()
    data = [l for l in base.splitlines() if l.strip() and not l.startswith("#")]
    families = [l.split("\t")[0] for l in data]
    report["contrast_baseline"] = {
        "entries": len(data),
        "by_theme": {n: families.count(f"property__{n}") for n in allnames},
        "market_entries": sum(1 for f in families if f.startswith("market__")),
    }
    golden = json.loads(
        (ROOT / "apps/worker/tests/golden/color_roles.json").read_text())
    report["color_roles_golden_themes"] = sorted(golden["property_themes"])

    lint = (ROOT / "scripts/template_color_baseline.txt").read_text()
    report["color_lint_baseline_lines_naming_a_theme_path"] = sum(
        1 for l in lint.splitlines()
        if l.strip() and not l.startswith("#")
        and any(f"property/{n}/" in l for n in allnames)
    )

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
