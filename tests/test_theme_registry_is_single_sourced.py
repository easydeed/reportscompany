"""
D-163. One statement of the theme id <-> name pairing, and gates on the copies.

WHAT D-163 WAS
--------------
Five independent copies of the pairing existed. The renderer said
{1: classic, 2: modern, 3: elegant, 4: teal, 5: bold}; the market wizard and
the onboarding flow both said {1: teal, 2: bold, 3: classic, 4: elegant,
5: modern} — wrong on every id, not shifted by one. 41 of 44 accounts had
`default_theme_id = 4`, so for almost every customer the wizard pre-selected
`elegant` and the PDF arrived in teal. Nothing compared the copies, so
nothing failed.

WHY THERE ARE STILL THREE STATEMENTS AND NOT ONE
------------------------------------------------
`apps/worker/src/worker/themes.json` is canonical. The worker reads it at
runtime. The API and the browser cannot: the API and the worker are separate
services whose runtimes are not guaranteed to contain each other's packages
(`branding_tools._load_market_report_builder` caches the ImportError and
carries on without the worker), and a bundled React component cannot read a
Python package's data file at all. So each gets one GENERATED file and this
module fails if either has drifted.

WHAT THIS FILE IS AND IS NOT
----------------------------
It is a STRUCTURAL gate. It reads source and configuration; it renders
nothing. It cannot tell you that bold looks right — `test_property_production_render.py`
does that. What it can tell you, which no render test can, is that a SIXTH
copy of the mapping has appeared somewhere, or that a retired theme's name
has come back in a live code path. That is the failure D-163 actually was.

Parsed with Python's and JSON's own parsers, and for TypeScript with a
brace-matched scan rather than a line regex — the four web theme lists are
written four different ways (one line an entry in the branding pages, eleven
in the wizard types) and a regex over them would have to guess where an entry
ends. §0.6, a substring is not a construct.
"""
import ast
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "apps/worker/src/worker/themes.json"
GENERATOR = REPO / "scripts/gen_theme_registries.py"
API_GENERATED = REPO / "apps/api/src/api/theme_registry.py"
WEB_GENERATED = REPO / "apps/web/lib/themes.generated.ts"
TEMPLATES = REPO / "apps/worker/src/worker/templates/property"
MIGRATION = REPO / "db/migrations/0058_theme_cut_to_three.sql"

ALL_NAMES = ("teal", "bold", "classic", "modern", "elegant")

#: Source trees worth scanning. `output/` holds generated HTML and PDFs and
#: `_intake/` holds a vendored starter app; neither ships.
#:
#: `apps/worker/tests` AND `apps/api/tests` WERE MISSING, and that was not a
#: judgement call — it was an oversight, and it cost exactly what the gate
#: exists to prevent. Seven call sites in the worker's own tests still said
#: `report_data("teal")` and `render(theme="teal")` after the cut. They did
#: not fail: `theme_registry.resolve()` quietly returns the default for a
#: retired name, so seven tests claimed to measure teal and measured bold.
#: `tests` matched only the ROOT suite, which is why a gate whose message is
#: "a retired theme's name in code is a path that can still ask the renderer
#: for a template that was deleted" said nothing about seven such paths.
TREES = ("apps/api/src", "apps/api/tests", "apps/web", "apps/worker/src",
         "apps/worker/scripts", "apps/worker/tests", "scripts",
         "db/migrations", "tests")
SKIP_PARTS = ("node_modules", ".next", "dist", "build", "__pycache__", ".git")


def registry():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def generator():
    spec = importlib.util.spec_from_file_location("_gen_theme_registries", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: Comment markers that start a line comment in any language scanned here.
#: A TRAILING comment counts. The first version only skipped lines that
#: STARTED with a marker, and so reported
#:   key: string;  // Theme name for API: "classic", ...
#: as retired-theme code. `{/*` is JSX's, which is neither obvious form.
_LINE_COMMENT_START = ("#", "//", "--", "/*", "{/*", "*", '"""', "'''")
_LINE_COMMENT_INLINE = ("#", "//", "/*", "{/*", "--")


def _without_comment(line: str) -> str:
    """`line` with a trailing comment removed, or "" if it is all comment.

    Crude on purpose: it does not know a `//` inside a string literal from a
    real comment, so a quoted URL loses its tail. Acceptable here because the
    only thing read out of the result is whether a QUOTED theme name appears,
    and cutting early can only produce a false NEGATIVE — in a line that
    would have to hold both a URL and a quoted theme name.
    """
    if line.strip().startswith(_LINE_COMMENT_START):
        return ""
    cut = len(line)
    for marker in _LINE_COMMENT_INLINE:
        at = line.find(marker)
        if at != -1:
            cut = min(cut, at)
    return line[:cut]


def source_files(*suffixes):
    for tree in TREES:
        for path in (REPO / tree).rglob("*"):
            if path.suffix in suffixes and not any(s in path.parts for s in SKIP_PARTS):
                yield path


# ── the canonical file is internally coherent ─────────────────────────────

def test_the_registry_says_one_thing():
    reg = registry()
    live = {t["id"]: t["name"] for t in reg["themes"]}
    retired = {t["id"]: t["name"] for t in reg["retired"]}
    assert live, "no live themes"
    assert reg["default_id"] in live, (
        f"default_id {reg['default_id']} is not a live theme: {sorted(live)}"
    )
    assert not set(live) & set(retired), (
        f"ids both live and retired: {sorted(set(live) & set(retired))} — ids "
        f"are never reused, because property_reports.theme holds historical values"
    )
    assert len(set(live.values())) == len(live), "two live themes share a name"
    assert set(live.values()) | set(retired.values()) == set(ALL_NAMES), (
        "the registry has gained or lost a theme name this gate does not know "
        "about; add it to ALL_NAMES and re-read the retired-name exemptions below"
    )


def test_every_live_theme_has_the_template_it_names():
    for theme in registry()["themes"]:
        path = TEMPLATES / theme["template"]
        assert path.exists(), (
            f"{theme['name']} (id {theme['id']}) points at {theme['template']}, "
            f"which does not exist"
        )


def test_no_retired_theme_still_has_a_template():
    """Otherwise the cut is a config change that left the code behind."""
    present = sorted(
        t["name"] for t in registry()["retired"]
        if (TEMPLATES / t["name"]).exists()
    )
    assert not present, (
        f"retired themes still have template directories: {present}. A "
        f"retired theme with a template is one a hand-written id map can "
        f"still reach."
    )


# ── the generated copies are current ──────────────────────────────────────

def test_the_generated_registries_are_not_stale():
    """The whole single-source claim rests on this one assertion.

    Regenerates in memory and compares. If this fails, run
    `python3 scripts/gen_theme_registries.py` — do not hand-edit either file.
    """
    gen = generator()
    themes, retired, default = gen.load()
    for path, text in ((API_GENERATED, gen.render_api(themes, retired, default)),
                       (WEB_GENERATED, gen.render_web(themes, retired, default))):
        assert path.exists(), f"{path.relative_to(REPO)} has not been generated"
        assert path.read_text(encoding="utf-8") == text, (
            f"{path.relative_to(REPO)} differs from what themes.json generates. "
            f"Run: python3 scripts/gen_theme_registries.py"
        )


def test_the_generator_check_mode_agrees():
    """`--check` is what CI would run; a `--check` that cannot fail is no gate."""
    done = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr


def test_the_generated_files_say_they_are_generated():
    """A reader who edits one by hand loses the edit on the next regen."""
    for path in (API_GENERATED, WEB_GENERATED):
        head = path.read_text(encoding="utf-8")[:400]
        assert "DO NOT EDIT" in head, f"{path.relative_to(REPO)} has no banner"
        assert "themes.json" in head, f"{path.relative_to(REPO)} does not name its source"


# ── no sixth copy ─────────────────────────────────────────────────────────

#: Files allowed to state the pairing. Everything else must ask one of them.
SANCTIONED = {
    "apps/worker/src/worker/themes.json",
    "apps/api/src/api/theme_registry.py",
    "apps/web/lib/themes.generated.ts",
    "scripts/gen_theme_registries.py",
    # The cut itself: the migration names the retired ids because it moves
    # rows off them, and this gate names them because it is this gate.
    "db/migrations/0058_theme_cut_to_three.sql",
    "tests/test_theme_registry_is_single_sourced.py",
}

#: An int key whose value is a theme name, or the reverse. This is the shape
#: the five copies all had, so it is the shape that is forbidden.
PY_PAIR = re.compile(
    r"(?:(\d)\s*:\s*[\"'](" + "|".join(ALL_NAMES) + r")[\"']"
    r"|[\"'](" + "|".join(ALL_NAMES) + r")[\"']\s*:\s*(\d))"
)
TS_PAIR = re.compile(
    r"(?:(\d)\s*:\s*[\"'](" + "|".join(ALL_NAMES) + r")[\"']"
    r"|\b(" + "|".join(ALL_NAMES) + r")\s*:\s*(\d)\b)"
)

#: Two pairs is a mapping; one is a lookup. The threshold is 2 because a
#: single `{5: "bold"}`-shaped line is as likely to be a test fixture.
PAIR_THRESHOLD = 2


@pytest.mark.parametrize(
    "path",
    sorted(source_files(".py", ".ts", ".tsx", ".json", ".sql")),
    ids=lambda p: str(p.relative_to(REPO)),
)
def test_no_file_restates_the_id_to_name_pairing(path):
    rel = str(path.relative_to(REPO))
    if rel in SANCTIONED:
        pytest.skip("canonical or generated")
    text = path.read_text(encoding="utf-8", errors="ignore")
    pattern = PY_PAIR if path.suffix in (".py", ".json", ".sql") else TS_PAIR
    pairs = {
        (m.group(1) or m.group(4), m.group(2) or m.group(3))
        for m in pattern.finditer(text)
    }
    assert len(pairs) < PAIR_THRESHOLD, (
        f"{rel} states {len(pairs)} id/name theme pairings: {sorted(pairs)}. "
        f"This is a sixth copy of the map D-163 is about. Import the pairing "
        f"from the registry — worker/theme_registry.py, api/theme_registry.py "
        f"or web/lib/themes.generated.ts — or add this file to SANCTIONED with "
        f"the reason it has to restate it."
    )


# ── the web theme lists agree with the registry ──────────────────────────

#: The lists that carry per-theme PRESENTATION (fonts, gradients, copy). They
#: legitimately hold more than the pairing, so they are checked on their id
#: SET rather than forbidden. Four existed and no two agreed on what a theme
#: looked like; that divergence is the Design rewire's problem, but an id set
#: that disagrees with the renderer is this gate's.
WEB_THEME_LISTS = (
    ("apps/web/lib/wizard-types.ts", "export const THEMES"),
    ("apps/web/components/property-wizard/types.ts", "export const THEMES"),
    ("apps/web/lib/property-report-assets.ts", "export const THEMES"),
    ("apps/web/app/app/settings/branding/page.tsx", "const THEMES"),
    ("apps/web/app/app/company/branding/page.tsx", "const THEMES"),
)


def _ts_array_ids(path: Path, decl: str) -> set:
    """The `id:` of every top-level object literal in a TS array.

    Brace-matched, not line-matched. `s.index("[", ...)` from the declaration
    would find the `[]` in a `Theme[]` type annotation, which is how the first
    version of this scan came back with no elements at all.
    """
    s = path.read_text(encoding="utf-8")
    i = s.index(decl)
    eq = s.index("=", i)
    open_at = s.index("[", eq)
    depth, close_at = 0, None
    for j in range(open_at, len(s)):
        if s[j] == "[":
            depth += 1
        elif s[j] == "]":
            depth -= 1
            if depth == 0:
                close_at = j
                break
    assert close_at is not None, f"{path}: unterminated array after {decl!r}"
    body = s[open_at + 1 : close_at]
    spans, depth, start = [], 0, None
    for k, ch in enumerate(body):
        if ch == "{":
            if depth == 0:
                start = k
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                spans.append((start, k + 1))
    ids = set()
    for a, b in spans:
        m = re.search(r"\bid:\s*(\d+)", body[a:b])
        assert m, f"{path}: theme entry with no numeric id:\n{body[a:b][:140]}"
        ids.add(int(m.group(1)))
    assert ids, f"{path}: parsed {decl!r} and found no themes — the scan is broken"
    return ids


@pytest.mark.parametrize("rel,decl", WEB_THEME_LISTS, ids=lambda v: v)
def test_every_web_theme_list_offers_exactly_the_live_themes(rel, decl):
    live = {t["id"] for t in registry()["themes"]}
    found = _ts_array_ids(REPO / rel, decl)
    assert found == live, (
        f"{rel} offers themes {sorted(found)}; the renderer has "
        f"{sorted(live)}. A picker offering a theme the renderer retired "
        f"produces a report in the default with nothing saying so (D-163); "
        f"one missing a live theme hides it from every customer."
    )


# ── the retired names, where they are allowed to remain ──────────────────

#: Where a retired theme's NAME may still appear, and why. Everywhere else,
#: a retired name in a live path is a path that can still ask for a deleted
#: template.
RETIRED_NAME_ALLOWED = {
    # Historical counts. `property_report_stats.theme_teal` holds the number
    # of teal reports ever generated; the column cannot be dropped without
    # losing that, and the API cannot report it without naming it.
    "db/migrations/0037_property_report_stats.sql":
        "theme_<name> columns counting reports already generated",
    "apps/api/src/api/services/property_stats.py":
        "reads those columns; renaming the keys would break the admin charts",
    # The admin report list labels rows written before the cut. It builds the
    # table from RETIRED_THEME_REGISTRY rather than typing the names.
    "apps/web/lib/themes.generated.ts": "generated; carries the retired set",
    # Documentation of the cut.
    "db/migrations/0058_theme_cut_to_three.sql": "the migration that did it",
    "apps/worker/src/worker/themes.json": "canonical; carries the retired set",
    "apps/worker/src/worker/theme_registry.py": "explains what D-163 was",
    "scripts/gen_theme_registries.py": "generates the retired set",
    "apps/api/src/api/theme_registry.py": "generated; carries the retired set",
    "scripts/derive_theme_name_scope.py":
        "measures how many places name a theme, so it has to name them all",
    "tests/test_theme_registry_is_single_sourced.py": "this file",
}

RETIRED_WORD = None  # built in the test, from the registry


def test_no_live_code_path_names_a_retired_theme():
    """A name, not a comment: matched outside comments only.

    The templates' own CSS custom properties were named after their theme
    (`--teal`, 39 of them), so this would have been a wall of noise before
    the cut — it is the cut that makes the gate affordable.
    """
    retired = [t["name"] for t in registry()["retired"]]
    word = re.compile(r"\b(" + "|".join(retired) + r")\b", re.I)
    offenders = {}
    for path in source_files(".py", ".ts", ".tsx", ".sql"):
        rel = str(path.relative_to(REPO))
        if rel in RETIRED_NAME_ALLOWED:
            continue
        hits = []
        for n, line in enumerate(
            path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
        ):
            bare = _without_comment(line)
            if not bare.strip():
                continue
            # `bold` is a font weight far more often than a theme. Only a
            # QUOTED occurrence can be a theme name in code.
            for m in word.finditer(bare):
                before = bare[: m.start()].rstrip()
                after = bare[m.end() :].lstrip()
                quoted = before.endswith(('"', "'", "`")) and after.startswith(
                    ('"', "'", "`")
                )
                if quoted:
                    hits.append((n, bare.strip()[:110]))
        if hits:
            offenders[rel] = hits
    assert not offenders, (
        "retired theme names in live code:\n"
        + "\n".join(
            f"  {rel}:{n}  {line}" for rel, hs in sorted(offenders.items())
            for n, line in hs
        )
        + "\n\nA retired theme's name in code is a path that can still ask the "
        "renderer for a template that was deleted. If the occurrence is "
        "historical (a stats column, an admin label), add the file to "
        "RETIRED_NAME_ALLOWED with the reason."
    )


# ── the database default matches the registry default ────────────────────

def test_the_migration_sets_the_default_the_registry_states():
    """Three places said what the default was and they said 1, 4 and 4."""
    default = registry()["default_id"]
    sql = MIGRATION.read_text(encoding="utf-8")
    assert re.search(
        rf"ALTER COLUMN default_theme_id SET DEFAULT {default}\b", sql
    ), f"0058 does not set the column default to {default}"
    retired = sorted(t["id"] for t in registry()["retired"])
    joined = ", ".join(str(i) for i in retired)
    assert f"IN ({joined})" in sql, (
        f"0058 does not move rows off the retired ids ({joined})"
    )
    assert f"SET default_theme_id = {default}" in sql


def test_no_python_fallback_names_a_theme_id_the_registry_does_not():
    """Every integer theme fallback in the worker and the API, parsed.

    `theme_id or 1`, `default_theme_id = 4`, `COALESCE(default_theme_id, 1)` —
    four fallbacks, three values, none of them agreeing with the column's own
    DEFAULT. Found by reading them, so a fifth cannot be added quietly.
    """
    live = {t["id"] for t in registry()["themes"]}
    pat = re.compile(
        r"(?:theme_id\s+or\s+(\d+)"
        r"|default_theme_id\s*=\s*(\d+)"
        r"|COALESCE\(\s*default_theme_id\s*,\s*(\d+)"
        r"|DEFAULT_THEME_ID\s*[:=]\s*(?:int\s*=\s*)?(\d+))"
    )
    bad = {}
    for path in source_files(".py"):
        rel = str(path.relative_to(REPO))
        if rel in ("tests/test_theme_registry_is_single_sourced.py",):
            continue
        for n, line in enumerate(
            path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
        ):
            if line.strip().startswith("#"):
                continue
            for m in pat.finditer(line):
                value = next(g for g in m.groups() if g)
                if int(value) not in live:
                    bad[f"{rel}:{n}"] = line.strip()[:120]
    assert not bad, (
        "theme fallbacks naming an id the registry does not have:\n"
        + "\n".join(f"  {k}  {v}" for k, v in sorted(bad.items()))
    )


def test_the_worker_registry_and_the_api_registry_agree():
    """Two runtimes, one pairing. Imported, not grepped."""
    sys.path.insert(0, str(REPO / "apps/worker/src"))
    sys.path.insert(0, str(REPO / "apps/api/src"))
    from api import theme_registry as api_reg
    from worker import theme_registry as worker_reg

    assert worker_reg.THEME_NUMBER_MAP == api_reg.THEME_NUMBER_MAP
    assert worker_reg.RETIRED_NUMBER_MAP == api_reg.RETIRED_NUMBER_MAP
    assert worker_reg.DEFAULT_THEME_ID == api_reg.DEFAULT_THEME_ID
    assert sorted(worker_reg.THEME_NUMBER_MAP) == api_reg.SELECTABLE_THEME_IDS


def test_no_request_model_defaults_a_theme_field_to_a_retired_id():
    """`test_no_python_fallback_names_a_theme_id_the_registry_does_not` is a
    list of four SPELLINGS, and `theme: Any = Field(default=4)` is a fifth.

    D-174. That regex matches `theme_id or N`, `default_theme_id = N`,
    `COALESCE(default_theme_id, N)` and `DEFAULT_THEME_ID = N` — the four forms
    that existed when it was written. Two Pydantic request models in
    `routes/property.py` declared `default=4`, which is `teal`, retired by the
    cut three weeks earlier; one of them also carried `ge=1, le=5`, a
    CONTIGUOUS range over a set the cut made non-contiguous. Both were
    invisible to the regex, and neither broke anything, because
    `theme_registry.resolve` sends every retired and unknown value to the
    default — which is precisely why nothing noticed.

    §0.6: a selector named after one instance describes that instance. So this
    one PARSES instead: every assignment to a theme-named field in every
    class, whatever the spelling, with the value read out of the AST.
    """
    live = {t["id"] for t in registry()["themes"]}
    bad = {}

    def theme_named(name: str) -> bool:
        return "theme" in name.lower()

    def int_literal(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, int) \
                and not isinstance(node.value, bool):
            return node.value
        return None

    for path in source_files(".py"):
        rel = str(path.relative_to(REPO))
        if rel == "tests/test_theme_registry_is_single_sourced.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            for stmt in cls.body:
                target = None
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    target = stmt.target.id
                elif isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                        and isinstance(stmt.targets[0], ast.Name):
                    target = stmt.targets[0].id
                if target is None or not theme_named(target) or stmt.value is None:
                    continue
                where = f"{rel}:{stmt.lineno} ({cls.name}.{target})"

                # `theme: int = 4`
                direct = int_literal(stmt.value)
                if direct is not None and direct not in live:
                    bad[where] = f"= {direct}, not a live id"
                    continue

                # `theme: int = Field(default=4, ge=1, le=5)`
                if isinstance(stmt.value, ast.Call):
                    for kw in stmt.value.keywords:
                        value = int_literal(kw.value)
                        if value is None:
                            continue
                        if kw.arg == "default" and value not in live:
                            bad[where] = f"Field(default={value}), not a live id"
                        elif kw.arg in ("ge", "le", "gt", "lt"):
                            bad[where] = (
                                f"Field({kw.arg}={value}) — a contiguous bound "
                                f"over {sorted(live)}, which has gaps"
                            )

    assert not bad, (
        "theme fields whose declared value or bound disagrees with the "
        "registry:\n"
        + "\n".join(f"  {k}  {v}" for k, v in sorted(bad.items()))
        + "\n\nDerive it: `DEFAULT_THEME_ID` for the value, "
        "`SELECTABLE_THEME_IDS` (or a field_validator against it) for the set. "
        "A range cannot express the gaps ids-are-never-reused leaves behind."
    )
