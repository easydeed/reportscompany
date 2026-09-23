#!/usr/bin/env python3
"""
Lint: no brand hex literal in a template.

This is Workstream A's acceptance criterion (master plan §04), made mechanical.
The reason it is a lint and not a review note: the brand literals in these
templates were not put there carelessly. Each one was a reasonable local choice
— pick the shade that looks right here — and the aggregate is a build where an
affiliate's colour reaches maybe a third of the places it should, and where
Luxury Estates ships a 3.74:1 price on every card because one of those local
choices was made against the default teal and never revisited.

A reviewer cannot hold thirty files in their head. A rule can.

WHAT COUNTS AS A BRAND HEX LITERAL
----------------------------------
Two rules, reported separately because they have different strengths.

  BRAND-ROLE   A hex literal standing in a brand ROLE: the value of a
               brand-role CSS custom property (`--primary-color`,
               `--color-accent`, `--pct-blue`, ...) or the `default()` fallback
               of a brand-role Jinja variable. Structural and exact — if a
               declaration names a brand role and its value is a literal, the
               affiliate's colour cannot reach it. No judgement, no threshold.

  BRAND-ADJACENT
               A coloured hex literal elsewhere in the file whose HUE is within
               15° of a brand role declared in that same file. Catches the
               hand-picked relatives — the gradient end, the darker navy, the
               zebra tint — without a maintained list of known shades, because
               each file declares its own brand hue and the relatives are
               found relative to it.

               Deliberately under-inclusive at two edges, both stated rather
               than hidden: a literal paler than the chroma floor (16/255) is
               treated as a neutral, and a brand relative in a file that
               declares no brand role at all is not found. Neither weakens the
               acceptance criterion, which BRAND-ROLE carries.

WHAT IS NOT A VIOLATION
-----------------------
Fixed neutrals (§3.2) and status colours (§3.3) are specified as literals —
they are not themeable and must not be drawn from the brand palette. They are
exempt by role, not by value: a status colour sitting in a brand-role property
is still a BRAND-ROLE violation, because the role is what makes it wrong.

    Note a collision the design system should resolve: Demo Title's brand
    primary is #DC2626, and #DC2626 is also the status red used for "bad",
    "buyers" and "negative" throughout. On that theme, brand and error are the
    same colour. That is a design finding, not something a lint can decide.

SUPPRESSION
-----------
`lint-allow-hex: <reason>` on the same line or the line above, inside a comment.
The reason is required — a bare suppression is itself an error, because the
whole value of this rule is that every remaining literal has an argument
attached to it.

THE BASELINE, AND WHY THERE IS ONE
----------------------------------
There are 111 of these today. They cannot all be removed in the commit that
introduces the rule: replacing a hand-picked shade with a derived one CHANGES
WHAT SHIPS, and Workstream A is specified to ship invisibly. Removing them is
the migration, and the migration is reviewed one surface at a time.

So the rule runs as a ratchet against `scripts/template_color_baseline.txt`:
a finding already in the baseline is tolerated, a new one fails. The count only
goes down. `--check-baseline` is what CI runs; `--write-baseline` is what you
run after retiring some, and shrinking that file is the visible progress.

The baseline records path + rule + colour, not line numbers, so it does not
churn when a template is edited above the offending line.

USAGE
-----
    python3 scripts/lint_template_colors.py                  # lint, exit 1 on findings
    python3 scripts/lint_template_colors.py --summary        # counts only
    python3 scripts/lint_template_colors.py --check-baseline # CI: fail on NEW findings
    python3 scripts/lint_template_colors.py --write-baseline # after retiring some
    python3 scripts/lint_template_colors.py PATH ...         # lint specific paths
"""
from __future__ import annotations

import argparse
import colorsys
import pathlib
import re
import sys
from collections import Counter
from typing import Dict, Iterable, List, NamedTuple, Optional, Set

REPO = pathlib.Path(__file__).resolve().parents[1]

#: The template directories §04 names. Both are live: the worker renders the
#: jinja2 tree, and apps/web/templates is the print-page fallback that
#: pdf_engine.py falls back to (see apps/web/lib/templates.ts's header).
TEMPLATE_ROOTS = (
    "apps/worker/src/worker/templates",
    "apps/web/templates",
)

#: A CSS custom property is a brand role if its name matches one of these.
#: Kept as substrings because the three surfaces spell the same role three
#: ways (`--primary-color`, `--color-primary`, `--pct-blue`).
BRAND_ROLE_PROPERTY = re.compile(
    r"--(?:"
    r"primary-color|accent-color|accent-light|accent-on-dark|accent-on-light|accent-text"
    r"|color-primary(?:-light|-dark)?|color-accent(?:-light|-dark)?"
    r"|pct-blue|pct-accent"
    r"|brand[\w-]*|theme[\w-]*"
    r")\s*:",
    re.I,
)

#: Jinja variables that carry a brand value. A `default('#xxxxxx')` on one of
#: these is a brand literal even though it only renders when the value is
#: missing — "only when branding fails" is precisely when it is worst.
BRAND_ROLE_VARIABLE = re.compile(
    r"\b(?:accent_color|primary_color|theme_color\w*|accent_on_dark|accent_on_light"
    r"|accent_light|accent_text|brand_\w*color\w*)\b",
    re.I,
)

HEX = re.compile(r"#(?P<v>[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")

SUPPRESS = re.compile(r"lint-allow-hex\s*:\s*(?P<reason>\S.*?)\s*(?:\*/|-->|#\}|$)")

#: Below this max-minus-min across RGB, a colour reads as a neutral regardless
#: of its nominal hue. Chosen from the actual distribution in these templates:
#: every literal below 16 is a grey, an off-white or a paper tone; the first
#: recognisable colours (#dff6f3, a teal tint, at 23) sit above it.
CHROMA_FLOOR = 16

#: Degrees of hue within which a literal counts as a relative of a brand role.
HUE_WINDOW = 15.0

#: Status colours (§3.3) and their neighbours. Exempt from BRAND-ADJACENT only
#: — they remain violations in a brand role.
STATUS_HEXES = {
    "#16a34a", "#15803d", "#059669", "#10b981",   # good / sellers / positive
    "#dc2626", "#b91c1c", "#ef4444",              # bad / buyers / negative
    "#ca8a04", "#d97706", "#f59e0b", "#fbbf24",   # balanced / caution
}

#: Selector or property fragments that mark a status context. A literal here is
#: a status colour by position even if it is not in the set above.
STATUS_CONTEXT = re.compile(
    r"--(?:success|danger|warning|error)\b"
    r"|--(?:good|bad|positive|negative)\b"
    r"|(?:good|bad|positive|negative|sellers|buyers|balanced|caution|sold|pending|active)\b",
    re.I,
)


BASELINE_PATH = REPO / "scripts/template_color_baseline.txt"


class Finding(NamedTuple):
    path: str
    line: int
    rule: str
    hex_value: str
    text: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.rule} {self.hex_value}  |  {self.text.strip()[:96]}"

    @property
    def key(self) -> str:
        """Identity for the baseline: no line number, so edits above do not churn it."""
        return f"{self.path}\t{self.rule}\t{self.hex_value}"


def normalize(value: str) -> str:
    v = value.lower().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return "#" + v


def _rgb(value: str):
    v = normalize(value)[1:]
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def chroma(value: str) -> int:
    r, g, b = _rgb(value)
    return max(r, g, b) - min(r, g, b)


def hue(value: str) -> float:
    r, g, b = _rgb(value)
    return colorsys.rgb_to_hls(r / 255, g / 255, b / 255)[0] * 360.0


def hue_distance(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def suppression_reason(lines: List[str], idx: int) -> Optional[str]:
    """A suppression on this line or the one above. Returns the reason, or None."""
    for probe in (idx, idx - 1):
        if 0 <= probe < len(lines):
            m = SUPPRESS.search(lines[probe])
            if m:
                return m.group("reason")
    return None


def brand_role_hexes(lines: List[str]) -> Set[str]:
    """
    Every hex literal this file puts in a brand role — the reference points
    BRAND-ADJACENT measures against. Collected from literals AND from the
    `default()` fallbacks, so a file that is already half-migrated still
    declares its hue.
    """
    found = set()
    for line in lines:
        if BRAND_ROLE_PROPERTY.search(line) or BRAND_ROLE_VARIABLE.search(line):
            for m in HEX.finditer(line):
                found.add(normalize(m.group("v")))
    return found


def _display(path: pathlib.Path) -> str:
    """Repo-relative where possible; absolute when a path outside the repo is
    linted deliberately (e.g. a `git archive` of another revision, which is how
    this rule was checked against main before any template was touched)."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def lint_file(path: pathlib.Path) -> List[Finding]:
    rel = _display(path)
    lines = path.read_text().split("\n")
    roles = brand_role_hexes(lines)
    brand_hues = [hue(h) for h in roles if chroma(h) >= CHROMA_FLOOR]

    findings: List[Finding] = []
    for i, line in enumerate(lines):
        matches = list(HEX.finditer(line))
        if not matches:
            continue
        reason = suppression_reason(lines, i)
        if reason:
            continue
        is_role = bool(BRAND_ROLE_PROPERTY.search(line) or BRAND_ROLE_VARIABLE.search(line))
        is_status_ctx = bool(STATUS_CONTEXT.search(line))
        for m in matches:
            h = normalize(m.group("v"))
            if is_role:
                findings.append(Finding(rel, i + 1, "BRAND-ROLE", h, line))
                continue
            if is_status_ctx or h in STATUS_HEXES:
                continue
            if chroma(h) < CHROMA_FLOOR:
                continue
            if any(hue_distance(hue(h), bh) <= HUE_WINDOW for bh in brand_hues):
                findings.append(Finding(rel, i + 1, "BRAND-ADJACENT", h, line))
    return findings


def bare_suppressions(path: pathlib.Path) -> List[Finding]:
    """`lint-allow-hex` with no reason after it."""
    rel = _display(path)
    out = []
    for i, line in enumerate(path.read_text().split("\n")):
        if "lint-allow-hex" in line and not SUPPRESS.search(line):
            out.append(Finding(rel, i + 1, "BARE-SUPPRESSION", "", line))
    return out


def template_files(roots: Iterable[str]) -> List[pathlib.Path]:
    out: List[pathlib.Path] = []
    for root in roots:
        p = (REPO / root) if not pathlib.Path(root).is_absolute() else pathlib.Path(root)
        if p.is_file():
            out.append(p)
        else:
            out.extend(sorted(f for f in p.rglob("*") if f.is_file()))
    return out


def run(roots: Iterable[str]) -> List[Finding]:
    findings: List[Finding] = []
    for f in template_files(roots):
        findings.extend(lint_file(f))
        findings.extend(bare_suppressions(f))
    return findings


def read_baseline(path: pathlib.Path = BASELINE_PATH) -> Counter:
    """{key: tolerated count}. Comments and blanks ignored."""
    out: Counter = Counter()
    if not path.exists():
        return out
    for line in path.read_text().split("\n"):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        out[line] += 1
    return out


def write_baseline(findings: List[Finding], path: pathlib.Path = BASELINE_PATH) -> None:
    header = [
        "# Brand hex literals in templates that predate the lint rule.",
        "# Format: path<TAB>rule<TAB>colour, one line per occurrence, sorted.",
        "#",
        "# This file may only SHRINK. `--check-baseline` fails on any finding not",
        "# listed here; retiring one means deleting its line. Regenerate with",
        "#     python3 scripts/lint_template_colors.py --write-baseline",
        "# and never to make a failing check pass — a new violation is the point.",
        "",
    ]
    body = sorted(f.key for f in findings)
    path.write_text("\n".join(header + body) + "\n")


def check_baseline(findings: List[Finding], baseline: Counter) -> Counter:
    """Findings in excess of what the baseline tolerates."""
    current = Counter(f.key for f in findings)
    new: Counter = Counter()
    for key, n in current.items():
        excess = n - baseline.get(key, 0)
        if excess > 0:
            new[key] = excess
    return new


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("paths", nargs="*", default=None)
    ap.add_argument("--summary", action="store_true", help="counts only")
    ap.add_argument("--write-baseline", action="store_true",
                    help="record the current findings as tolerated")
    ap.add_argument("--check-baseline", action="store_true",
                    help="fail only on findings not in the baseline (this is what CI runs)")
    args = ap.parse_args(argv)

    roots = args.paths or list(TEMPLATE_ROOTS)
    findings = run(roots)

    if args.write_baseline:
        write_baseline(findings)
        print(f"wrote {BASELINE_PATH.relative_to(REPO)} with {len(findings)} entries")
        return 0

    if args.check_baseline:
        baseline = read_baseline()
        new = check_baseline(findings, baseline)
        retired = sum(baseline.values()) - (len(findings) - sum(new.values()))
        for key, n in sorted(new.items()):
            print(f"NEW  {key}" + (f"  (x{n})" if n > 1 else ""))
        print(f"{len(findings)} findings, {sum(baseline.values())} baselined, "
              f"{sum(new.values())} new, {retired} retired")
        if new:
            print("\nA template gained a brand hex literal. Use the derived token "
                  "(worker.themes.derive_theme) or, if it genuinely is not a brand "
                  "value, annotate it: lint-allow-hex: <reason>.")
            return 1
        return 0

    if not args.summary:
        for f in findings:
            print(f)
        if findings:
            print()

    by_rule = Counter(f.rule for f in findings)
    by_file = Counter(f.path for f in findings)
    scanned = len(template_files(roots))
    print(f"scanned {scanned} template files in {len(list(roots))} root(s)")
    for rule, n in sorted(by_rule.items()):
        print(f"  {rule}: {n}")
    print(f"  files with findings: {len(by_file)}")
    print(f"  TOTAL: {len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
