"""
The product must not assert a trademarked professional designation on an
agent's behalf.

THE DEFECT THIS EXISTS TO PREVENT (D-066)
-----------------------------------------
Every property report defaulted an agent's title to `Realtor®` when they had
not set one. REALTOR® is a registered collective membership mark owned by the
National Association of REALTORS® and usable only by its members. Roughly a
third of licensed US agents are not members, and nothing in this product asks.

So a licensee who left "job title" blank at signup had a claim of NAR
membership printed on a document they hand to clients, under their own name and
photo — a trademark exposure created by a default value, not by anything they
did.

`Real Estate Agent` is accurate for every licensee and asserts nothing. An agent
who *is* a member can type REALTOR® themselves, which is the only way the mark
should ever appear.

WHAT THE FIRST READ MISSED
--------------------------
This was scoped as one line (`_base/_macros.jinja2:70`). It is eight: six Jinja
sites and two Python ones — and the Python ones are the ones that matter, because
`property_builder.py` supplies the string before the template is reached, which
makes the Jinja `default()` dead code on that path. Changing only the templates
would have changed nothing while looking like a fix.

AND A SEPARATE BUG IN THE SAME EXPRESSION
-----------------------------------------
Jinja's `default(x)` fires only on *undefined*. `agent.get("title", …)` returns
None when the key exists holding a null, and `{{ None | default('…') }}` renders
the literal string **"None"** into a customer-facing PDF. The boolean form,
`default(x, true)`, fires on any falsy value and fixes that as well as the empty
string that otherwise left a bare " · " separator.
"""
import re
from pathlib import Path

import pytest
from jinja2 import Environment, DictLoader, select_autoescape


WORKER_SRC = Path(__file__).resolve().parents[1] / "src" / "worker"
TEMPLATES = sorted((WORKER_SRC / "templates").rglob("*.jinja2"))

EXPECTED_DEFAULT = "Real Estate Agent"


# ── the mark must not be asserted anywhere ──────────────────────────────────

def test_no_template_defaults_a_title_to_the_realtor_mark():
    offenders = [
        f"{p.relative_to(WORKER_SRC)}:{i}"
        for p in TEMPLATES
        for i, line in enumerate(p.read_text().splitlines(), 1)
        if re.search(r"realtor", line, re.I)
    ]
    assert not offenders, f"REALTOR® asserted in templates: {offenders}"


@pytest.mark.parametrize("module", ["property_builder.py", "tasks.py"])
def test_no_python_default_asserts_the_realtor_mark(module):
    """
    The Python defaults are the load-bearing ones: property_builder supplies
    the title before the template runs, so a template-only fix changes nothing.
    """
    offenders = [
        f"{module}:{i}  {line.strip()[:70]}"
        for i, line in enumerate((WORKER_SRC / module).read_text().splitlines(), 1)
        if re.search(r"realtor|\\u00ae", line, re.I) and not line.strip().startswith("#")
    ]
    assert not offenders, f"REALTOR® asserted in code: {offenders}"


def test_the_replacement_is_actually_present():
    """A test that only forbids the old value passes if someone deletes the
    default entirely, which would ship a blank title."""
    found = [p for p in TEMPLATES if EXPECTED_DEFAULT in p.read_text()]
    assert found, f"no template supplies the {EXPECTED_DEFAULT!r} default"
    assert EXPECTED_DEFAULT in (WORKER_SRC / "property_builder.py").read_text()
    assert EXPECTED_DEFAULT in (WORKER_SRC / "tasks.py").read_text()


# ── the None leak, by render ────────────────────────────────────────────────

# The expression this branch owns: the contact block, where the REALTOR® default
# lived. The theme COVER blocks are a separate expression with per-theme copy
# ("Luxury Property Specialist" for elegant, and so on) — deliberate design, not
# a trademark claim, and not this branch's to flatten. They carry the same
# None-leak bug; that is filed as D-067.
# Matched WITH the quotes: the cover expression 'Licensed Real Estate Agent'
# contains "Real Estate Agent" as a substring, so a bare substring test silently
# picks up the very sites this branch is not touching.
OWNED = "'Real Estate Agent'"


def _render_title(agent):
    """Render the exact expression the contact-block templates use."""
    src = next(
        line for p in TEMPLATES for line in p.read_text().splitlines()
        if "agent.title" in line and OWNED in line
    )
    expr = re.search(r"\{\{[^}]*agent\.title[^}]*\}\}", src).group(0)
    env = Environment(loader=DictLoader({"t.jinja2": expr}),
                      autoescape=select_autoescape(["html", "xml", "jinja2"]))
    return env.get_template("t.jinja2").render(agent=agent)


@pytest.mark.parametrize(
    "agent,why",
    [
        ({}, "key absent"),
        ({"title": None}, "key present holding NULL — rendered the string 'None'"),
        ({"title": ""}, "agent left it blank — rendered nothing beside a bare separator"),
        ({"title": "   "}, "whitespace only"),
    ],
)
def test_a_missing_title_falls_back_rather_than_leaking(agent, why):
    out = _render_title(agent)
    assert out.strip(), f"{why}: rendered empty"
    assert out.strip() != "None", f"{why}: leaked the literal string None into the PDF"
    assert "Realtor" not in out


def test_an_agents_own_title_is_never_overridden():
    """The default must not touch someone who set a title — including a member
    who legitimately uses the mark."""
    assert "Broker Associate" in _render_title({"title": "Broker Associate"})
    assert "REALTOR®" in _render_title({"title": "REALTOR®"})


def test_every_template_uses_the_boolean_default_form():
    """
    `default(x)` fires only on undefined. `default(x, true)` fires on any falsy
    value, which is what catches the None and the empty string. Pinned because
    the difference is one argument and invisible at a glance.
    """
    for p in TEMPLATES:
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if "agent.title" in line and OWNED in line:
                assert re.search(r"default\([^)]*,\s*true\s*\)", line), (
                    f"{p.relative_to(WORKER_SRC)}:{i} uses the plain default form, "
                    f"which lets None through as the string 'None': {line.strip()}"
                )
