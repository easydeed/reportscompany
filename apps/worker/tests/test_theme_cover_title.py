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

  dangling separator      bold renders `{{ title }} • {{ license }}` (so did
                          classic, until the theme cut deleted it)
                          with the bullet OUTSIDE any condition, and `license`
                          is `""` for any agent who has not entered a licence
                          number. Those covers read "Real Estate Agent • ".
                          Not an edge case — it is every unlicensed-in-profile
                          agent, which is the default state of a new account.

STILL A DECISION, NOT FIXED HERE
--------------------------------
Because the Python default wins, every theme prints "Real Estate Agent"
regardless of the per-theme copy ("Luxury Property Specialist" for elegant,
"Real Estate Specialist" for modern). The theme voice was designed and has
never rendered. Making it work means moving the fallback out of Python, which
is a design call.

AFTER THE THEME CUT
-------------------
Three themes, not five. This file named classic and teal in a dict and in two
`parametrize` lists; the themes now come from the renderer's registry and the
separator cases are FOUND by parsing the cover line for a `license`
reference, rather than listed. A list of theme names in a test is a copy of
the registry, which is the defect D-163 is about.
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
from worker.theme_registry import THEME_TEMPLATES as THEMES  # noqa: E402
from _template_chain import chain  # noqa: E402
COVER_CLASSES = ("cover-agent-title", "agent-role")


#: Themes whose cover carries an agent role line at all.
#:
#: DESIGN'S PACKAGE DROPS IT. The redesigned cover is report kind, brand,
#: street, city, four stats, hero photo, "Prepared for" and "In short" — and
#: no agent role. The agent appears on page 6 as name, brand and licence. So
#: `agent.title` renders NOWHERE on a theme using the shared architecture,
#: while `_build_agent_context` still computes it and still defaults it to
#: "Real Estate Agent" (D-169).
#:
#: FOUND by looking for the line, not by listing which themes are on which
#: architecture — a theme that regains a role line is covered without this
#: file being edited, and that is the case that needs covering, because
#: reintroducing the line reintroduces D-066 and D-067 with it.
def _has_cover_line(theme) -> bool:
    return bool(_cover_lines(theme))


def _cover_lines(theme):
    return [
        line
        for path in chain(theme)
        for line in path.read_text(encoding="utf-8").splitlines()
        if "agent.title" in line and any(c in line for c in COVER_CLASSES)
    ]


def _cover_line(theme):
    """The one cover title line rendering this theme, asserted unique.

    SEARCHES THE CHAIN, not the entry file. A theme on the shared
    architecture (`_v2/report.jinja2`) has an entry file of nothing but
    `{% set %}`, and reading that file alone found zero cover lines and took
    the whole worker suite down at COLLECTION — hiding every other result
    until it was fixed. See `_template_chain`.
    """
    hits = _cover_lines(theme)
    assert len(hits) == 1, (
        f"{theme}: expected exactly one cover title line across "
        f"{[p.name for p in chain(theme)]}, found {len(hits)}"
    )
    return hits[0].strip()


#: The themes this file's structural half can speak about.
COVER_LINE_THEMES = sorted(t for t in THEMES if _has_cover_line(t))
NO_COVER_LINE_THEMES = sorted(t for t in THEMES if not _has_cover_line(t))


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


@pytest.mark.parametrize("theme", COVER_LINE_THEMES)
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


@pytest.mark.parametrize("theme", COVER_LINE_THEMES)
def test_an_agents_own_title_is_never_overridden(theme):
    assert "Broker Associate" in _render_cover(theme, {"title": "Broker Associate"})
    # A member who legitimately holds the mark typed it themselves; nothing here
    # may substitute it away.
    assert "REALTOR®" in _render_cover(theme, {"title": "REALTOR®"})


#: Themes whose cover line puts the licence beside the title. FOUND, not
#: listed: the two `parametrize(["classic", "bold"])` lists this replaces both
#: went stale the moment classic was deleted, and a theme that GAINS a
#: separator would not have been added to either.
SEPARATOR_THEMES = sorted(
    t for t in COVER_LINE_THEMES if "agent.license" in _cover_line(t))


def test_no_cover_line_carries_an_unconditional_separator():
    """THE DEFECT ITSELF, asserted directly rather than through its surface.

    The reachable half of D-067 was `{{ title }} • {{ license }}` with the
    bullet outside any condition, so every agent without a licence number on
    file got a cover reading "Real Estate Agent • ". Classic and bold were
    the two themes with that form.

    Both are gone now — classic was retired by the theme cut and bold moved
    to an architecture with no cover role line at all — so `SEPARATOR_THEMES`
    is empty and the two tests below have nothing to run on. The previous
    guard said so by FAILING, with a message telling the reader to delete
    those tests. That is the right instinct and the wrong mechanism: deleting
    them removes the only thing that would notice the form coming back.

    So the guard is inverted. Instead of "some theme must have a licence on
    its cover", this asserts the thing that must never be true of any cover
    line on any theme — a separator glyph that is not inside a condition —
    and it holds whether zero themes or all of them print a licence.
    """
    import re as _re

    def _literal_text(line: str) -> str:
        """The line with every Jinja expression and tag removed.

        `|` IS JINJA'S FILTER PIPE. The first version of this check looked for
        it as a separator glyph and reported elegant and modern as offenders
        on `{{ (agent.title or '') | trim | default(...) }}` — a gate matching
        an operator inside the construct it was meant to be reading. Tenth
        outing for substring-is-not-a-construct in this project, and the first
        one in a test written the same hour.

        `{% if %}` blocks are kept as markers so the conditional test below
        still sees them; only their contents go.
        """
        line = _re.sub(r"\{\{.*?\}\}", "", line)
        line = _re.sub(r"\{%\s*if\b.*?%\}", "{%if%}", line)
        return _re.sub(r"\{%.*?%\}", "", line)

    offenders = {}
    for theme in COVER_LINE_THEMES:
        literal = _literal_text(_cover_line(theme))
        for glyph in ("•", "·", "—", "–"):
            if glyph not in literal:
                continue
            # The glyph must sit after a `{% if %}` on the same line. Crude,
            # and that is the point: a separator split across lines is not a
            # form this project has produced, and widening the check to the
            # whole template would match the running head's own bullets.
            if "{%if%}" not in literal.split(glyph)[0]:
                offenders.setdefault(theme, []).append(glyph)
    assert not offenders, (
        f"cover lines with a separator outside any condition: {offenders}. "
        f"`license` is the empty string for every agent who has not entered "
        f"one, so this renders a trailing glyph with nothing after it (D-067)."
    )


@pytest.mark.skipif(not SEPARATOR_THEMES,
                    reason="no theme puts the licence on the cover; "
                           "test_no_cover_line_carries_an_unconditional_separator "
                           "is what guards the form coming back")
def test_the_licence_tests_below_have_a_subject():
    """Named, so the skip above is visible as a result rather than a silence."""
    assert SEPARATOR_THEMES


@pytest.mark.parametrize("theme", SEPARATOR_THEMES)
def test_no_separator_is_printed_beside_an_absent_licence(theme):
    """
    THE REACHABLE DEFECT. The bullet sat outside any condition, and `license`
    is the empty string for every agent without a licence number on file — so
    those covers read "Real Estate Agent • " with nothing after it.
    """
    text = _text(_render_cover(theme, {"title": "Broker Associate"}))
    assert not text.endswith("•"), f"{theme}: dangling separator on the cover: {text!r}"
    assert "•" not in text, f"{theme}: separator printed with no licence to separate: {text!r}"


@pytest.mark.parametrize("theme", SEPARATOR_THEMES)
def test_the_licence_still_appears_when_there_is_one(theme):
    """The guard above must not have deleted the feature it was guarding."""
    text = _text(_render_cover(theme, {"title": "Broker Associate",
                                       "license_number": "01234567"}))
    assert "CA BRE#01234567" in text
    assert "•" in text, "the separator disappeared along with the empty case"


def test_a_theme_without_a_cover_role_line_does_not_print_one_anyway():
    """The other side of the architecture change, asserted on the RENDER.

    A theme whose template has no `agent.title` must also not have the title
    reach the page some other way — through the narrative, the footer, or a
    context key a later edit wires up. Checked by rendering and looking for
    the value, because the structural half above can only say the line is not
    in the template.

    `agent.title` defaults to "Real Estate Agent" in `_build_agent_context`,
    so this asserts on a DISTINCTIVE title rather than the default: finding
    the words "Real Estate Agent" would prove nothing, since the disclaimer
    and the explainers are full of ordinary prose.
    """
    if not NO_COVER_LINE_THEMES:
        pytest.skip("every theme still carries a cover role line")
    from test_property_production_render import report_data
    for theme in NO_COVER_LINE_THEMES:
        # THE WHOLE DOCUMENT, not `_render_cover` — that helper renders the
        # cover LINE, and a theme with no cover line has none to render. The
        # first version of this test called it and failed with "expected
        # exactly one cover title line, found 0", which is the helper
        # reporting the premise of the test it was being used to run.
        data = dict(report_data(theme))
        data["agent"] = {**(data.get("agent") or {}), "title": "Broker Associate"}
        rendered = PropertyReportBuilder(data).render_html()
        assert "Broker Associate" not in rendered, (
            f"{theme} has no cover role line in its templates and still "
            f"renders the agent's title. If that is intended, the line has "
            f"come back and D-066's REALTOR mark rule applies to it again."
        )


@pytest.mark.parametrize("theme", COVER_LINE_THEMES)
def test_every_cover_uses_the_boolean_default_or_an_explicit_condition(theme):
    """
    `default(x)` fires only on undefined; `default(x, true)` fires on any falsy
    value. The difference is one argument and invisible at a glance, which is
    exactly how five templates came to carry it. A theme with no fallback
    string of its own is given no invented one and guards with `{% if %}`
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
    if not COVER_LINE_THEMES:
        pytest.skip("no theme carries a cover role line any more")
    distinct = {_text(_render_cover(theme, {"title": None}))
                for theme in COVER_LINE_THEMES}
    assert distinct == {"Real Estate Agent"}, (
        "the per-theme cover copy has become reachable (or diverged): "
        f"{sorted(distinct)} — see D-067, this is a design decision, not a bug"
    )
