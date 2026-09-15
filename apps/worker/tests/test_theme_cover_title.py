"""
The agent's role on a report cover, rendered through the path production uses.

WHAT D-067 SAID, AND WHAT RENDERING IT SHOWED
---------------------------------------------
D-067 was filed as "the theme cover blocks leak the literal string 'None'",
read off five template lines that use Jinja's plain `default()` — which fires
only on *undefined*, so a key holding NULL renders "None".

The templates do say that. It cannot happen. `PropertyReportBuilder
._build_agent_context` substitutes the title **before** the template runs, and
it uses `or`, which catches None. Every one of the five per-theme fallback
strings is dead code.

That is D-066's own lesson, arriving from the other direction: the Python
layer is load-bearing and the template is not. D-066 nearly shipped a fix that
changed nothing because it edited only the template; D-067 nearly filed a bug
that could not happen because it read only the template. **Both were settled by
rendering, not by reading** — so every case here renders through
`_build_agent_context`, never against a template line in isolation.

WHAT WAS ACTUALLY WRONG
-----------------------
Two things, both reachable, neither in the filed report:

  whitespace-only title   `"   "` is truthy, so it sailed past the `or` and
                          every theme printed a blank line in cover-sized type.

  dangling separator      classic and bold render `{{ title }} • {{ license }}`
                          with the bullet OUTSIDE any condition, and `license`
                          is `""` for any agent who has not entered a licence
                          number. Those covers read "Real Estate Agent • ".
                          Not an edge case — it is every unlicensed-in-profile
                          agent, which is the default state of a new account.

STILL A DECISION, NOT FIXED HERE
--------------------------------
Because the Python default wins, all five themes print "Real Estate Agent"
regardless of the per-theme copy ("Luxury Property Specialist" for elegant,
"Real Estate Specialist" for modern). The theme voice was designed and has
never rendered. Making it work means moving the fallback out of Python, which
is a design call. Teal, which has no string of its own, is given no invented
one: its slot renders only when there is something to put in it.
"""
import pathlib
import sys

import pytest
from jinja2 import Environment, DictLoader, select_autoescape

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from worker.property_builder import PropertyReportBuilder  # noqa: E402

TEMPLATES = pathlib.Path(__file__).resolve().parents[1] / "src" / "worker" / "templates" / "property"

# Located by content rather than by line number: a line number is a selector
# that retargets silently the moment anything above it moves (§0.6).
THEMES = {
    "classic": "classic/classic_report.jinja2",
    "bold": "bold/bold_report.jinja2",
    "elegant": "elegant/elegant_report.jinja2",
    "modern": "modern/modern_report.jinja2",
    "teal": "teal/teal_report.jinja2",
}
COVER_CLASSES = ("cover-agent-title", "agent-role")


def _cover_line(theme):
    """The one cover title line in this theme, asserted unique."""
    path = TEMPLATES / THEMES[theme]
    hits = [
        line for line in path.read_text().splitlines()
        if "agent.title" in line and any(c in line for c in COVER_CLASSES)
    ]
    assert len(hits) == 1, (
        f"{THEMES[theme]}: expected exactly one cover title line, found {len(hits)}"
    )
    return hits[0].strip()


def _render_cover(theme, agent_row):
    """
    Render the theme's cover line against the context production builds.

    `agent_row` is what the database join hands over, NOT the template context
    — the whole point is that something happens in between.
    """
    builder = PropertyReportBuilder.__new__(PropertyReportBuilder)
    builder.report_data = {"agent": dict(agent_row), "branding": {}}
    context = builder._build_agent_context()
    env = Environment(loader=DictLoader({}),
                      autoescape=select_autoescape(["html", "xml", "jinja2"]))
    return env.from_string(_cover_line(theme)).render(agent=context)


def _text(html):
    """Crude tag strip — enough to see what a reader sees."""
    out, depth = [], 0
    for ch in html:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out).strip()


@pytest.mark.parametrize("theme", sorted(THEMES))
@pytest.mark.parametrize(
    "agent_row,why",
    [
        ({}, "key absent"),
        ({"title": None}, "column exists holding NULL"),
        ({"title": ""}, "agent cleared the field"),
        ({"title": "   "}, "whitespace only — truthy, so it passed the `or`"),
    ],
)
def test_a_missing_title_renders_something_a_person_would_accept(agent_row, why, theme):
    rendered = _render_cover(theme, agent_row)
    text = _text(rendered)
    assert "None" not in rendered, f"{theme} ({why}): leaked the literal string None"
    assert text, f"{theme} ({why}): cover role line rendered empty"
    assert "Realtor" not in rendered, f"{theme} ({why}): asserts the REALTOR® mark (D-066)"


@pytest.mark.parametrize("theme", sorted(THEMES))
def test_an_agents_own_title_is_never_overridden(theme):
    assert "Broker Associate" in _render_cover(theme, {"title": "Broker Associate"})
    # A member who legitimately holds the mark typed it themselves; nothing here
    # may substitute it away.
    assert "REALTOR®" in _render_cover(theme, {"title": "REALTOR®"})


@pytest.mark.parametrize("theme", ["classic", "bold"])
def test_no_separator_is_printed_beside_an_absent_licence(theme):
    """
    THE REACHABLE DEFECT. The bullet sat outside any condition, and `license`
    is the empty string for every agent without a licence number on file — so
    these two covers read "Real Estate Agent • " with nothing after it.
    """
    text = _text(_render_cover(theme, {"title": "Broker Associate"}))
    assert not text.endswith("•"), f"{theme}: dangling separator on the cover: {text!r}"
    assert "•" not in text, f"{theme}: separator printed with no licence to separate: {text!r}"


@pytest.mark.parametrize("theme", ["classic", "bold"])
def test_the_licence_still_appears_when_there_is_one(theme):
    """The guard above must not have deleted the feature it was guarding."""
    text = _text(_render_cover(theme, {"title": "Broker Associate",
                                       "license_number": "01234567"}))
    assert "CA BRE#01234567" in text
    assert "•" in text, "the separator disappeared along with the empty case"


@pytest.mark.parametrize("theme", sorted(THEMES))
def test_every_cover_uses_the_boolean_default_or_an_explicit_condition(theme):
    """
    `default(x)` fires only on undefined; `default(x, true)` fires on any falsy
    value. The difference is one argument and invisible at a glance, which is
    exactly how five templates came to carry it. Teal has no fallback string of
    its own and is not given an invented one, so it guards with `{% if %}`
    instead — both forms are acceptable, a bare `{{ agent.title }}` is not.
    """
    line = _cover_line(theme)
    boolean_default = "default(" in line and ", true)" in line.replace(" ,", ",")
    explicit_condition = "{% if" in line
    assert boolean_default or explicit_condition, (
        f"{THEMES[theme]}: cover title has no falsy-safe fallback: {line}"
    )


def test_the_per_theme_fallback_strings_are_currently_unreachable():
    """
    Not a defect — a fact, pinned so it is noticed if it changes.

    Every theme's own copy is dead while `_build_agent_context` substitutes a
    title first. If someone moves that fallback out of Python to make the theme
    voice work, this test fails and points at the decision rather than letting
    it happen quietly.
    """
    distinct = {_text(_render_cover(theme, {"title": None})) for theme in THEMES}
    assert distinct == {"Real Estate Agent"}, (
        "the per-theme cover copy has become reachable (or diverged): "
        f"{sorted(distinct)} — see D-067, this is a design decision, not a bug"
    )
