"""The render harness's route list, checked against the product.

WHY THIS EXISTS AT ALL
----------------------
Because the list is the part that goes wrong, and a wrong list is invisible.
The first draft of this manifest — written up as a finished result and never
run — contained `/app/contacts` and `/app/templates`, neither of which has ever
been a route in this repository, and expected `/app/admin` to render under a
token with `is_platform_admin: false`, where a 404 is the correct answer and
`middleware.ts:72` says so.

A harness is only as honest as its list. Four routes reported as 404ing read as
four defects; they were two names that never existed, one route that works, and
one gate doing its job. So every path here is resolved against the filesystem
and every `blocked` expectation against the middleware's own conditions.
"""
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "apps/web"
MANIFEST = REPO / "scripts/render-routes.json"
HARNESS = REPO / "scripts/render_routes.mjs"
MIDDLEWARE = WEB / "middleware.ts"

#: Names that were invented, reported as results, and must not come back
#: without someone noticing. Not a style rule — a record.
NEVER_EXISTED = ("/app/contacts", "/app/templates")


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _entries(m):
    return list(m["routes"]) + list(m.get("blocked", []))


def _page_for(url_path):
    """Resolve a URL path to its `page.tsx`, ignoring route groups."""
    rel = url_path.strip("/")
    direct = WEB / "app" / rel / "page.tsx" if rel else WEB / "app/page.tsx"
    if direct.is_file():
        return direct
    # A route group — `(auth)/login` serves `/login`.
    for candidate in (WEB / "app").rglob("page.tsx"):
        served = re.sub(r"\([^)]*\)/?", "",
                        candidate.relative_to(WEB / "app").parent.as_posix())
        served = "/" + served.strip("/")
        if served == url_path or (served == "/" and url_path == "/"):
            return candidate
    return None


def test_there_are_routes_to_check(manifest):
    """The guard. Every assertion below loops over the manifest, so an empty
    one would make them all vacuously true."""
    assert len(manifest["routes"]) >= 15
    assert manifest.get("blocked"), \
        "no blocked routes declared — the gates are untested"


def test_every_path_in_the_manifest_resolves_to_a_real_page(manifest):
    missing = [e["path"] for e in _entries(manifest) if _page_for(e["path"]) is None]
    assert missing == [], (
        f"the harness would request routes that do not exist: {missing}. "
        f"A 404 from one of these is the list being wrong, not the product."
    )


def test_the_invented_routes_have_not_come_back(manifest):
    """Checked against the PATHS, not against the file's text.

    The first version of this read the raw JSON and failed immediately — the
    manifest's own `_why` block names both routes in order to explain why they
    are wrong. A substring standing in for a construct, in the test written to
    stop exactly that; the fourth time in a week. A declared route is an entry
    with a `path`, so that is what is compared.
    """
    paths = {e["path"] for e in _entries(manifest)}
    present = sorted(paths & set(NEVER_EXISTED))
    assert present == [], (
        f"{present} are declared routes in the manifest. Neither has ever been "
        f"a route here — Contacts is /app/people. See the module docstring."
    )


def test_contacts_is_still_at_app_people(manifest):
    """The route the invented list got wrong, asserted positively so the
    manifest cannot drift back by omission."""
    paths = [e["path"] for e in manifest["routes"]]
    assert "/app/people" in paths
    assert _page_for("/app/people") is not None
    layout = (WEB / "app/app-layout.tsx").read_text(encoding="utf-8")
    assert 'href: "/app/people"' in layout, (
        "the sidebar no longer links Contacts to /app/people — if it moved, "
        "this manifest and D-193's notes both need updating"
    )


def test_every_token_referenced_is_defined(manifest):
    names = set(manifest["tokens"])
    used = {e["token"] for e in _entries(manifest)}
    assert used <= names, f"undefined token claim sets: {sorted(used - names)}"


def test_each_blocked_route_matches_a_real_gate_in_the_middleware(manifest):
    """`blocked` is an assertion about `middleware.ts`, so it is read there.

    If a gate is removed the route starts rendering for everyone, and the
    harness reports `UNEXPECTEDLY-RENDERED` — but only while the gate it is
    asserting about is the one that exists.
    """
    src = MIDDLEWARE.read_text(encoding="utf-8")
    gates = {
        "/app/admin": 'pathname.startsWith("/app/admin")',
        "/app/company": 'pathname.startsWith("/app/company")',
        "/app/affiliate": 'pathname.startsWith("/app/affiliate")',
    }
    for entry in manifest["blocked"]:
        needle = gates.get(entry["path"])
        assert needle, (
            f"{entry['path']} is declared blocked but this test knows no gate "
            f"for it — add the condition or drop the entry"
        )
        assert needle in src, (
            f"{entry['path']} is declared blocked and {needle!r} is no longer "
            f"in middleware.ts, so nothing refuses it"
        )
    assert "ADMIN_CLOAK_404" in src, (
        "the cloak that makes /app/admin a 404 rather than a redirect is gone; "
        "the manifest's note about a 404 being correct is now wrong"
    )


def test_declared_redirects_point_at_pages_that_exist(manifest):
    for e in _entries(manifest):
        target = e.get("expectFinal")
        if not target:
            continue
        assert _page_for(target) is not None, (
            f"{e['path']} is declared to redirect to {target}, which has no page"
        )


def test_the_harness_refuses_to_screenshot_an_unhealthy_route():
    """The property the whole file is for, asserted against the source.

    An unhealthy route that produces a plausible image is worse than one that
    produces none: in a batch of twenty nobody checks whether page nine
    rendered.
    """
    src = HARNESS.read_text(encoding="utf-8")
    assert "result.screenshot = false;   // a broken route gets NO image" in src

    # THE DECISION, not the word. The first version of this looped over
    # `("THE SENTINEL", "degraded", …)` asserting each appeared somewhere in
    # the file — and `scripts/regressions/render_harness.json` R5 replaced the
    # whole health decision with `result.health = 'ok';` and the test still
    # passed, because "degraded" survives in the docstring, the comparator and
    # the summary. DID NOT FIRE, reported by the harness this project built for
    # exactly that; substring-is-not-a-construct, fifth instance this week.
    assert "result.health = contentMissing ? 'degraded' : 'ok';" in src, (
        "the harness no longer separates a rendered page from one whose "
        "content never arrived, so a skeleton's computed styles would go into "
        "a before/after table as if they were the page's"
    )
    assert "result.health = (redirected || result.status === 404) ? " \
           "'blocked-as-expected' : 'UNEXPECTEDLY-RENDERED';" in src, (
        "the harness no longer distinguishes a route that correctly refused "
        "from one that should have refused and did not"
    )
    for needed in ("THE SENTINEL", "skeletons"):
        assert needed in src, f"the harness no longer implements {needed!r}"


# ─────────────────────────────────────────────────────────────────────────────
# B0.5 — the local stack, and the honesty of its coverage note
# ─────────────────────────────────────────────────────────────────────────────

STACK = REPO / "scripts/local_stack.sh"
FIXTURE = REPO / "scripts/seed_render_fixture.py"

#: Every external dependency the stack cannot stand in for. Named here so a
#: later batch cannot discover one of them by being surprised mid-review.
UNCOVERED = ("SimplyRETS", "PDFShift", "SiteX", "Stripe", "Resend", "Twilio",
             "worker")


def test_the_stack_script_says_what_it_does_not_cover():
    """A harness that can see some content is more dangerous than one that can
    see none, because the gap moves from obvious to assumed.

    So the list of what is NOT behind the local stack is part of the script,
    and this asserts it stays there. Scoping a content batch against a stack
    with no PDF renderer is fine; discovering that halfway through is not.
    """
    src = STACK.read_text(encoding="utf-8")
    missing = [name for name in UNCOVERED if name not in src]
    assert missing == [], (
        f"scripts/local_stack.sh no longer names {missing} among the things it "
        f"cannot stand in for. If one of them became available, say so there "
        f"and drop it from UNCOVERED; if the note was trimmed, put it back."
    )
    assert "WHAT IT DOES NOT COVER" in src


def test_the_fixture_seeds_volume_rather_than_one_of_each():
    """An empty page that renders is not a rendered page.

    This project has measured page fit on an empty page twice. A Contacts list
    with one row cannot show a filter pill row, a table rule, a status pill or
    a detail drawer — which is most of what Design's steps 5-7 change.
    """
    src = FIXTURE.read_text(encoding="utf-8")
    # Counted from the data, not from a sentence about the data.
    reports = src.count('("completed",') + src.count('("processing",') \
        + src.count('("failed",') + src.count('("queued",')
    assert reports >= 12, f"only {reports} seeded reports — a list needs to scroll"
    first_names = re.search(r"first = \[(.*?)\]", src, re.S)
    assert first_names and first_names.group(1).count(",") >= 14, \
        "fewer than 15 seeded contacts; the list page cannot show a long list"
    assert "AN EMPTY PAGE THAT RENDERS IS NOT A RENDERED PAGE" in src


def test_the_fixture_raises_the_rate_limit_it_would_otherwise_trip():
    """The rate limiter throttles a measurement tool, and silently.

    60 requests per minute per account against 25 routes of several calls each
    returns 429s, and the pages then render skeletons that the harness
    honestly reports as `degraded` — which reads as "this page has no data".
    """
    src = FIXTURE.read_text(encoding="utf-8")
    # The STATEMENT, not the constant's name. The first version asserted
    # `"HARNESS_ACCOUNTS" in src`, and regression R3 narrowed the UPDATE to a
    # single account while leaving the constant defined above it — DID NOT
    # FIRE. Sixth instance of the same family this week; see §0.6.
    assert "api_rate_limit=100000 WHERE id = ANY(%s::uuid[])" in src, (
        "the rate limit is no longer raised across a list of accounts"
    )
    assert "(list(HARNESS_ACCOUNTS),)" in src, (
        "the UPDATE no longer receives HARNESS_ACCOUNTS, so the four personas "
        "the manifest logs in as besides the regular one will 429"
    )
    assert src.count("HARNESS_ACCOUNTS = (") == 1


def test_the_fixture_marks_onboarding_done_or_app_is_not_the_dashboard():
    """`/app` redirects to `/app/get-started` while onboarding is incomplete.

    Correct product behaviour, and it meant the harness's `/app` entry was
    measuring the onboarding wizard. The sentinel caught it as BROKEN — final
    path != requested path — rather than producing a plausible table for the
    wrong page.
    """
    src = FIXTURE.read_text(encoding="utf-8")
    assert "onboarding_progress" in src
    # BOTH accounts, counted. The first version asserted each step name
    # appeared somewhere in the file, and once the bare variant added a second
    # identical loop the regression that deleted the CONTENT account's loop
    # stopped firing — the strings were still there, supplied by the other
    # block. Eighth instance of substring-is-not-a-construct this week; see
    # §0.6. Two seeding loops is the construct.
    loops = src.count('for step in ("profile_complete", "branding_setup", "first_report",')
    assert loops == 2, (
        f"{loops} onboarding-seeding loop(s), expected 2 — one for the account "
        f"with content and one for the bare account. Whichever is missing, "
        f"/app redirects to /app/get-started for it and that dashboard is "
        f"never rendered."
    )


# ─────────────────────────────────────────────────────────────────────────────
# The bare variant — the dashboard's absence rules
# ─────────────────────────────────────────────────────────────────────────────

DASHBOARD = WEB / "components/dashboard/dashboard-content.tsx"

#: Design's constraint #4: "show '—' or 'Nothing scheduled', never 0 as a fake
#: value". Each of these is the words a real account sees on day one.
#: Design's App v3 dashboard (2026-10-22) rewrote the empty-state copy: "No new
#: leads" became "No one to call yet", and "Nothing scheduled" moved from a
#: text node into the Next-send row's string. The rule is unchanged — a phrase,
#: never a zero — so the phrases are the new ones.
ABSENCE_COPY = ("Nothing sent yet", "Nothing scheduled", "No one to call yet")


def _without_comments(src: str) -> str:
    """Strip `//`, `/* */` and `{/* */}` comments, so a phrase quoted in a
    comment explaining the rule cannot satisfy the rule."""
    src = re.sub(r"\{/\*.*?\*/\}", "", src, flags=re.S)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"(?m)//.*$", "", src)


def test_the_manifest_renders_the_dashboard_as_an_account_with_nothing_on_it(manifest):
    """Every absence rule is a day-one state on the first page an account is
    shown, and a fixture built to have content never reaches one. The empty-page
    measurement inverted: we had been checking only the full case."""
    bare = [r for r in manifest["routes"]
            if r["path"] == "/app" and r["token"] == "bare"]
    assert len(bare) == 1, (
        "the manifest no longer renders /app as the bare account, so the "
        "dashboard's absence rules are unverified"
    )
    assert "bare" in manifest["tokens"]


def test_the_bare_account_is_on_a_plan_with_no_finite_limit():
    """The null sentence title only happens when `remaining` cannot be
    computed. On a plan with a finite limit the fallback is never exercised,
    and an unlimited plan is NOT "0 reports left" — D-195's mistake in prose."""
    src = FIXTURE.read_text(encoding="utf-8")
    assert 'BARE_PLAN = "team"' in src, (
        "the bare account's plan changed; `team` was chosen because its "
        "market_reports_limit is 99999, which the product reads as unlimited"
    )
    assert "BARE_ACCOUNT" in src and "bare account: a plan, onboarding done" in src


def test_the_bare_account_gets_onboarding_too():
    """Without it /app redirects to /app/get-started and the absence rules are
    never reached. "New account" means new to the product, not new to
    onboarding."""
    src = FIXTURE.read_text(encoding="utf-8")
    seeded = src[src.index("BARE_ACCOUNT ="):]
    assert "onboarding_progress" in seeded


def test_the_dashboard_says_words_rather_than_zeros_when_there_is_nothing():
    """Matched as RENDERED TEXT — `>Nothing scheduled<` — not as a substring.

    The first version checked `phrase in src`, and the regression that
    replaced the rendered phrase with "0 scheduled" DID NOT FIRE, because the
    comment directly above it quotes the phrase in order to explain the rule.
    Seventh instance of substring-is-not-a-construct in a week, in a test
    written against that family, caught by the harness again. A JSX text node
    is the construct; a comment cannot satisfy `>…<`.
    """
    src = _without_comments(DASHBOARD.read_text(encoding="utf-8"))
    # Rendered: a JSX text node (">Nothing sent yet." is fine — punctuation
    # may follow) or a string literal the JSX renders. Comments are gone, so
    # neither form can be satisfied by an explanation of the rule.
    missing = [c for c in ABSENCE_COPY
               if not re.search(r">\s*" + re.escape(c), src) and f'"{c}' not in src]
    assert missing == [], (
        f"the dashboard no longer RENDERS {missing} (the phrase may still be "
        f"in a comment). Design's constraint #4: show '—' or a phrase, never "
        f"0 as a fake value."
    )
    # The fallback itself, not the word "Overview" somewhere in the file.
    assert ': "Overview"' in src, (
        "the sentence title no longer falls back to the page name, so an "
        "account whose state cannot be computed gets a sentence with a hole "
        "in it (constraint #6)"
    )
    assert "limit < 999" in src, (
        "the sentence title no longer excludes an unlimited plan, so it will "
        "render a number for an allowance that has none"
    )
