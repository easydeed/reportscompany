"""Design's 2026-10-19 answer on tints, recomputed against the source.

WHY THIS IS GATED
-----------------
Design answered the ask in `docs/TINT_RAMP_FOR_DESIGN_2026-10-15.md` with a
rule, not a palette: **no tinted surfaces on chrome at all**, the semantic
status pairs excepted, plus one sanctioned exception for the initials circle.
A rule stated in a document and applied once by hand is a rule that holds until
the next person writes `bg-indigo-50`, so the sweep is re-derived here rather
than asserted to have happened.

The authenticated surface is computed as an **import closure** from the `/app`
routes, not as a list of directories. A tinted component pulled into the app
from `components/` is exactly the shape this is meant to catch, and a hand-kept
list of twenty-odd files would not have caught it.

THE WORD BOUNDARY IS NOT DECORATION
-----------------------------------
`bg-indigo-(50|100|200)` without `\\b` matches `bg-indigo-500`, which is a solid
colour and not a tint. Written without it during this very sweep, the check
reported three surviving hits that did not exist — the same
substring-is-not-a-construct family as D-123, D-168 and the three the CI
reporter work produced. Every pattern here is anchored.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
WEB = REPO / "apps/web"
DOC = REPO / "docs/TINT_RAMP_FOR_DESIGN_2026-10-15.md"
GLOBALS_CSS = WEB / "app/globals.css"
MIDDLEWARE = WEB / "middleware.ts"

#: The grep target Design's answer names. Anchored — see the module docstring.
TARGET = re.compile(r"bg-indigo-(?:50|100|200)\b|border-indigo-200\b")

#: `@/x` and relative imports, the two forms this app uses.
IMPORT = re.compile(r"""from\s+["']([^"']+)["']""")

#: The four places the answer records as out of scope, keyed by the doc's own
#: row order. A hit anywhere else is a surface nobody has ruled on.
OUT_OF_SCOPE = {
    "marketing": ("app/about/", "app/docs/", "app/security/", "app/careers/", "app/blog/"),
    "dead-admin": ("app/admin/",),
    "branding-form": ("components/branding-form.tsx",),
    "report-viewer": ("components/mobile-report/MobileReportViewer.tsx",),
}


def _resolve(spec: str, importer: Path):
    if spec.startswith("@/"):
        base = WEB / spec[2:]
    elif spec.startswith("."):
        base = (importer.parent / spec).resolve()
    else:
        return None
    for cand in (base.with_suffix(".tsx"), base.with_suffix(".ts"),
                 base / "index.tsx", base / "index.ts"):
        if cand.is_file():
            return cand
    return None


def _closure():
    """Every local module reachable from an authenticated `/app` route."""
    roots = sorted((WEB / "app/app").rglob("*.tsx")) + [WEB / "app/app-layout.tsx"]
    seen, queue = set(), list(roots)
    while queue:
        f = queue.pop()
        if f in seen or not f.is_file():
            continue
        seen.add(f)
        for spec in IMPORT.findall(f.read_text(encoding="utf-8")):
            dep = _resolve(spec, f)
            if dep is not None and dep not in seen:
                queue.append(dep)
    return seen


def _hits(paths):
    out = {}
    for f in paths:
        n = len(TARGET.findall(f.read_text(encoding="utf-8")))
        if n:
            out[f.relative_to(WEB).as_posix()] = n
    return out


@pytest.fixture(scope="module")
def doc():
    return DOC.read_text(encoding="utf-8")


def test_the_closure_is_not_empty_before_anything_is_concluded_from_it():
    """A resolver that silently resolves nothing makes every assertion below
    vacuous — the no-op-mutation trap, one level up."""
    closure = _closure()
    assert len(closure) > 150, (
        f"the import closure from /app resolved {len(closure)} files, which is "
        f"fewer than the route files alone. The resolver is broken, and a green "
        f"run below would mean nothing."
    )
    assert WEB / "components/v0-styling/AffiliateDashboardShell.tsx" in closure


def test_no_tinted_surface_survives_on_authenticated_chrome():
    hits = _hits(_closure())
    assert hits == {}, (
        f"Design's answer is that chrome carries no tinted surfaces. These are "
        f"reachable from an authenticated /app route and still tinted: {hits}"
    )


def test_every_remaining_hit_is_one_the_answer_accounted_for():
    """Zero on chrome is not zero app-wide, and the doc says which 37 remain
    and why each is out of scope. A hit outside those four is a surface nobody
    has ruled on — it should fail here rather than be discovered later."""
    all_tsx = sorted(p for p in WEB.rglob("*.tsx") if "node_modules" not in p.parts)
    hits = _hits(all_tsx)
    unaccounted = {
        path: n for path, n in hits.items()
        if not any(path.startswith(p) for ps in OUT_OF_SCOPE.values() for p in ps)
    }
    assert unaccounted == {}, (
        f"tinted surfaces in files the tint answer does not cover: {unaccounted}"
    )


def test_the_answer_quotes_the_counts_the_source_still_has(doc):
    all_tsx = sorted(p for p in WEB.rglob("*.tsx") if "node_modules" not in p.parts)
    hits = _hits(all_tsx)
    derived = {
        group: sum(n for path, n in hits.items() if path.startswith(prefixes))
        for group, prefixes in OUT_OF_SCOPE.items()
    }
    stated = {
        "marketing": int(re.search(r"`app/blog` \| (\d+) \|", doc).group(1)),
        "dead-admin": int(re.search(r"`app/admin/\(dashboard\)/\*\*` \| (\d+) \|", doc).group(1)),
        "branding-form": int(re.search(r"`components/branding-form\.tsx` \| (\d+) \|", doc).group(1)),
        "report-viewer": int(re.search(r"MobileReportViewer\.tsx` \| (\d+) \|", doc).group(1)),
    }
    assert derived == stated, (
        f"the answer document states {stated}; the source has {derived}"
    )
    total = sum(derived.values())
    assert f"{total} hits remain" in doc, (
        f"the document's total is stale — {total} hits remain app-wide"
    )


def test_the_dead_admin_tree_the_answer_relies_on_is_actually_unreachable():
    """14 of the 37 are excused because nothing can render them. That is a
    claim about `middleware.ts`, so it is read there and not taken on trust."""
    src = MIDDLEWARE.read_text(encoding="utf-8")
    redirect = src.index('pathname.replace(/^\\/admin/, "/app/admin")')
    reads_token = src.index('req.cookies.get("mr_token")')
    assert redirect < reads_token, (
        "the /admin -> /app/admin redirect no longer precedes the token read, "
        "so app/admin/(dashboard)/** may now be reachable and its 14 tinted "
        "surfaces are live"
    )
    assert '"/admin/:path*"' in src and '"/admin"' in src, (
        "the middleware matcher no longer covers /admin, so the redirect that "
        "makes app/admin/** dead does not run"
    )


def test_branding_form_is_still_imported_by_nothing():
    """4 of the 46 are excused as dead code.

    Deadness is read by RESOLVING each import to a file, not by looking for the
    string `BrandingForm` — a mention in a comment is not a consumer, and a
    substring standing in for a construct is the single most common defect on
    this board."""
    target = WEB / "components/branding-form.tsx"
    importers = []
    for f in sorted(WEB.rglob("*.ts*")):
        if "node_modules" in f.parts or f == target:
            continue
        for spec in IMPORT.findall(f.read_text(encoding="utf-8")):
            if _resolve(spec, f) == target:
                importers.append(f.relative_to(WEB).as_posix())
                break
    assert importers == [], (
        f"branding-form.tsx is no longer dead — imported by {importers} — so "
        f"its 4 tinted surfaces are live and the answer's table is wrong"
    )


def test_selection_is_structure_and_the_one_exception_is_written_down():
    css = GLOBALS_CSS.read_text(encoding="utf-8")
    assert "--surface-selected: #FFFFFF;" in css
    assert "--border-selected: #0F172A;" in css
    assert "ONLY tinted fills permitted on" in css, (
        "the constraint Design's answer turns on is not stated beside the tokens"
    )
    assert "ONE EXCEPTION" in css and "--agent-primary" in css, (
        "the avatar exception is not written beside the constraint it breaks, "
        "so the next reader sees a filled circle on chrome and an absolute rule "
        "forbidding it"
    )


def test_no_usage_bar_draws_a_fraction_of_an_undefined_whole():
    """D-195. Five copies of `UsageBar`, one of which painted 20% of a track
    against an unlimited allowance. The other four already guarded it; nothing
    could report the divergence, because there is nothing shared to diff."""
    defs = sorted(
        p for p in WEB.rglob("*.tsx")
        if "node_modules" not in p.parts
        and "function UsageBar(" in p.read_text(encoding="utf-8")
    )
    assert len(defs) == 5, (
        f"UsageBar is defined {len(defs)} times, not 5. D-195's point is that "
        f"the count is the mechanism; re-read the entry before editing this."
    )
    unguarded = []
    for f in defs:
        src = f.read_text(encoding="utf-8")
        if "style={{ width:" not in src:
            continue  # a copy that draws no track at all
        if "{!isUnlimited && (" not in src:
            unguarded.append(f.relative_to(WEB).as_posix())
    assert unguarded == [], (
        f"these draw a usage track without excluding an unlimited allowance, "
        f"which renders as a partly-consumed quota of nothing: {unguarded}"
    )
