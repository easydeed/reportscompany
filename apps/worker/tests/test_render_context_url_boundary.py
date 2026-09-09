"""
An unchecked URL must not be able to reach a PDF template.

WHY THIS TEST EXISTS RATHER THAN MORE CALL-SITE TESTS
-----------------------------------------------------
D-058 closed the URL scheme hole on the PDF surfaces by calling `safe_url()` at
the seven context-building sites a grep found. That guarantee is only as good
as the grep: it says "the sites I could see are checked", not "an unchecked URL
cannot reach a template". A new context field added next month inherits nothing.

`sanitize_context_urls()` inverts it. The sweep runs at the render boundary —
the one place a context can become HTML — so the property is structural. These
tests assert the *inverted* property: values that never passed through any
call-site guard are still clean by the time they render.

WHY IT SANITISES INSTEAD OF RAISING
-----------------------------------
An assertion that raised would convert an injection into an outage, which is
exactly what D-059 was: a render that stops is worse for the account than a
logo that fails to load. A rejected URL becomes None, the surrounding markup
collapses, and the drop is logged.

WHAT THIS DOES NOT COVER
------------------------
HTML injection on these surfaces — that is already handled by Jinja autoescape
(`property_builder.py`, `market_builder.py`, both with select_autoescape and no
`|safe` filters anywhere under templates/). Scheme is the part autoescape does
nothing about, and a PDF is rendered by a real browser, so it is the part that
matters most here.
"""
import pytest

from worker.property_builder import safe_url, sanitize_context_urls


DISALLOWED = [
    "javascript:alert(document.domain)",
    "JaVaScRiPt:alert(1)",
    "java\tscript:alert(1)",
    "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
    "vbscript:msgbox(1)",
    "file:///etc/passwd",
]

ALLOWED = [
    "https://cdn.example.test/a.jpg",
    "http://cdn.example.test/a.jpg",
    "//cdn.example.test/a.jpg",
    "/local/a.png",
    "https://cdn.example.test/a.jpg?w=800&h=600",
]


# ── the inverted guarantee ──────────────────────────────────────────────────

@pytest.mark.parametrize("bad", DISALLOWED)
def test_a_disallowed_url_cannot_survive_the_sweep(bad):
    """Top-level, exactly as a context field would carry it."""
    out = sanitize_context_urls({"logo_url": bad})
    assert out["logo_url"] is None


@pytest.mark.parametrize("bad", DISALLOWED)
def test_a_disallowed_url_nested_in_a_listing_cannot_survive(bad):
    """
    Vendor data arrives inside lists of dicts — listings, comparables. The
    sweep is recursive precisely so those are not a separate thing to remember.
    """
    context = {
        "listings": [
            {"address": "123 Main", "photo_url": bad, "price": 800000},
            {"address": "456 Oak", "photo_url": "https://cdn.example.test/ok.jpg"},
        ]
    }
    out = sanitize_context_urls(context)
    assert out["listings"][0]["photo_url"] is None
    assert out["listings"][1]["photo_url"] == "https://cdn.example.test/ok.jpg"


def test_a_url_field_nobody_guarded_is_still_cleaned():
    """
    THE POINT OF THE INVERSION. `some_new_field_url` passes through no
    call-site guard anywhere in the codebase — it does not exist. The sweep
    catches it anyway, which a per-site approach structurally cannot.
    """
    out = sanitize_context_urls({"some_new_field_url": "javascript:alert(1)"})
    assert out["some_new_field_url"] is None


def test_deeply_nested_urls_are_reached():
    context = {"agent": {"company": {"logo_url": "javascript:alert(1)"}}}
    assert sanitize_context_urls(context)["agent"]["company"]["logo_url"] is None


@pytest.mark.parametrize("good", ALLOWED)
def test_legitimate_urls_pass_through_unchanged(good):
    """
    Including the query-string case: the sweep must not HTML-escape, or `&`
    would become `&amp;` and then be escaped again by Jinja autoescape.
    """
    assert sanitize_context_urls({"photo_url": good})["photo_url"] == good


def test_non_url_keys_are_untouched():
    """
    A key not ending in _url is left completely alone — including strings that
    happen to look like URLs, and every numeric, which the templates format
    with numeric specs.
    """
    context = {
        "address": "123 Main St",
        "description": "See https://example.test for details",
        "price": 825000,
        "beds": 3,
        "ratio": 99.2,
        "active": True,
        "missing": None,
    }
    assert sanitize_context_urls(context) == context


def test_empty_and_missing_values_are_left_as_they_are():
    """An absent logo must stay absent, not become the empty string."""
    out = sanitize_context_urls({"logo_url": None, "photo_url": ""})
    assert out["logo_url"] is None
    assert out["photo_url"] == ""


def test_the_attribute_breakout_is_truncated_not_deleted():
    """
    A scheme check alone passes this. Truncation leaves a usable prefix;
    deleting the illegal characters would splice the payload onto the path.
    """
    out = sanitize_context_urls(
        {"photo_url": 'https://cdn.example.test/a.jpg" onerror="alert(1)'}
    )
    assert out["photo_url"] == "https://cdn.example.test/a.jpg"
    assert "onerror" not in out["photo_url"]


def test_the_sweep_agrees_with_safe_url():
    """
    The sweep must not develop its own opinion about what is allowed — it is
    the same rule applied at a different place.
    """
    for value in DISALLOWED + ALLOWED:
        assert sanitize_context_urls({"x_url": value})["x_url"] == (safe_url(value) or None)


def test_tuples_keep_their_type():
    """Contexts occasionally carry tuples; rebuilding them as lists would
    change template behaviour for no reason."""
    out = sanitize_context_urls({"items": ({"photo_url": "javascript:alert(1)"},)})
    assert isinstance(out["items"], tuple)
    assert out["items"][0]["photo_url"] is None
