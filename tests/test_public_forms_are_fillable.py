"""The forms a stranger fills: a reserved placeholder domain, and autofill.

WHY THESE TWO LIVE TOGETHER
---------------------------
Both are properties of the same thing — a form someone who is not a customer
is asked to type into — and both are invisible to every gate this repository
has. The jest suite would be the natural home and it has never passed (D-211),
so a guard put there would be a guard nobody reads. These run in Backend
Tests, which is green.

WHY A PARSER AND NOT A GREP
---------------------------
`grep -c 'autoComplete'` counts LINES, not occurrences, and a JSX attribute
list spans many lines — so a file with two inputs, one covered, reads as
covered. Worse, a naive `<input[^>]*>` stops at the first `>` it meets, and
`onChange={e => setPhone(...)}` contains one: every input with an arrow
handler looks like it has no attributes at all. A first pass of this check
written that way reported 25 uncovered inputs where there are 24, and listed
two that had just been fixed.

So `elements()` walks forward from the tag name tracking quote state and brace
depth, and stops at the first `>` that is really the end of the tag. The
question is "does this element carry the attribute", and the scanner answers
that question rather than a cheaper one that resembles it.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "apps/web"

#: RFC 2606 §3 reserves these for documentation and examples. The point is not
#: style: a placeholder on an unreserved domain is an address that someone,
#: somewhere, can receive mail at. `admin@pacificcoasttitle.com` sat on the
#: admin "new company" form, and Pacific Coast Title is a real firm — the same
#: family as M1-T4's invented agent at a real brokerage.
RESERVED = ("example.com", "example.org", "example.net")

#: The routes a person who is not yet a customer, or is not yet signed in,
#: fills in. Admin and in-app forms are deliberately out: this is about the
#: first form someone ever meets, not about every input in the product.
PUBLIC_PREFIXES = (
    "app/p/", "app/cma/", "app/login", "app/register", "app/welcome",
    "app/forgot-password", "app/reset-password", "app/blog",
)

#: One exception, and it is a pointer to a defect rather than a decision.
#: `/blog`'s newsletter input sits in a <form> with no action, no onSubmit and
#: no "use client" — submitting it navigates to /blog? and the address is
#: discarded (D-221). Giving it an autocomplete attribute would make it easier
#: to fill in a box that throws the answer away, which is worse than leaving
#: it. The exception is asserted to still be NECESSARY below, so it cannot
#: outlive the defect it names.
EXCEPTED = {("app/blog/page.tsx", "email")}

FILLABLE = ("email", "tel", "password")


def sources():
    return sorted(p for p in WEB.rglob("*.tsx") if "node_modules" not in str(p))


def rel(p):
    return str(p)[len(str(WEB)) + 1:]


def elements(src, names=("input", "Input")):
    """Yield (attrs, offset) for each JSX element with one of these tag names.

    Quote- and brace-aware: `>` inside a string or inside an expression
    container (`{...}`) does not end the tag.
    """
    for m in re.finditer(r"<(" + "|".join(names) + r")\b", src):
        i, depth, quote = m.end(), 0, None
        while i < len(src):
            c = src[i]
            if quote:
                if c == quote and src[i - 1] != "\\":
                    quote = None
            elif c in "\"'`":
                quote = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c == ">" and depth == 0:
                break
            i += 1
        yield src[m.end():i], m.start()


def fillable_inputs():
    """Every email/tel/password input under a public route, with coverage."""
    out = []
    for p in sources():
        r = rel(p)
        if not r.startswith(PUBLIC_PREFIXES):
            continue
        src = p.read_text(encoding="utf-8")
        for attrs, off in elements(src):
            t = re.search(r"type=\{?[\"']?(\w+)", attrs)
            kind = t.group(1) if t else None
            if kind not in FILLABLE:
                # A type chosen by an expression — `type={sms ? "tel" : "email"}`,
                # as the home value funnel's contact field is. Without this the
                # scanner read the type as "sms" and the field fell out of scope:
                # #238 lost its autofill coverage and nothing said so.
                expr = re.search(r"type=\{([^}]*)\}", attrs)
                quoted = re.findall(r"[\"'](\w+)[\"']", expr.group(1)) if expr else []
                kind = next((q for q in quoted if q in FILLABLE), None)
            if kind is None:
                continue
            out.append((r, kind, src[:off].count("\n") + 1,
                        "autoComplete" in attrs))
    return out


def placeholder_emails():
    out = []
    for p in sources():
        src = p.read_text(encoding="utf-8")
        for m in re.finditer(r'placeholder="([^"]*@[^"]*)"', src):
            out.append((rel(p), src[:m.start()].count("\n") + 1, m.group(1)))
    return out


def test_the_scans_find_something():
    """The guard both assertions below need.

    Each one loops over a derivation. A derivation that goes quiet — a renamed
    attribute, a moved directory, a regex that stops matching — makes them
    vacuously true, which is the shape this board keeps filing.
    """
    assert len(fillable_inputs()) >= 8, "the public-form scan found almost nothing"
    assert len(placeholder_emails()) >= 15, "the placeholder scan found almost nothing"


def test_the_scan_sees_the_home_value_contact_field():
    """
    A count floor cannot tell which field went missing. #238 rewrote the home
    value funnel and its contact field dropped out of this scan — no `type=`,
    then a type the scanner could not read — with the floor still met. The one
    field every homeowner fills is named here, so losing it is a failure.
    """
    kinds = {(path, kind) for path, kind, _line, _ok in fillable_inputs()}
    assert ("app/cma/[code]/cma-funnel.tsx", "tel") in kinds, (
        "the scan no longer sees the home value page's phone/email field")


def test_every_placeholder_email_uses_a_reserved_domain():
    bad = [f"{f}:{n}  {v}" for f, n, v in placeholder_emails()
           if not v.lower().endswith(RESERVED)]
    assert bad == [], (
        "a placeholder email on an unreserved domain is an address somebody "
        "can receive mail at, and a reader cannot tell it is an example:\n  "
        + "\n  ".join(bad)
    )


def test_every_public_form_input_a_browser_could_fill_says_how():
    missing = [f"{f}:{n} type={t}" for f, t, n, has in fillable_inputs()
               if not has and (f, t) not in EXCEPTED]
    assert missing == [], (
        "a form a person can submit but the browser cannot autofill is "
        "friction for no reason, and these are the forms filled by people who "
        "are not customers yet:\n  " + "\n  ".join(missing)
    )


@pytest.mark.parametrize("path,kind", sorted(EXCEPTED))
def test_each_exception_is_still_needed(path, kind):
    """The other direction, which is the half that goes stale.

    D-207 was a baseline that only failed when a row was MISSING, so a row
    describing something that no longer existed sat there indefinitely. An
    exception list has the same failure mode: when `/blog`'s form is wired or
    removed, this exception must go with it, and nothing but this assertion
    would notice.
    """
    present = [(f, t) for f, t, _, has in fillable_inputs() if not has]
    assert (path, kind) in present, (
        f"{path} ({kind}) is listed as an exception but no longer needs one — "
        f"delete it from EXCEPTED. If D-221 was fixed, this is the reminder."
    )
