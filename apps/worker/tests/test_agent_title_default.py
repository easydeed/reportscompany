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
    # The TEMPLATE half of this went with the templates: the six contact
    # blocks carrying `default('Real Estate Agent', true)` were all in the
    # nine-page property tree (D-131), deleted 2026-10-26. The live page does
    # not print an agent title, and the default that reaches every report is
    # the builder's, asserted here.
    assert EXPECTED_DEFAULT in (WORKER_SRC / "property_builder.py").read_text()

    # NOT `tasks.py` by name. This asserted the string was in that file until
    # D-140 moved the consumer branch's `report_data` into
    # `consumer_report_data.py` — a refactor that changed nothing about the
    # default and broke the test anyway. A guard pinned to a FILE PATH fails
    # on a move and passes on a deletion elsewhere; what it should assert is
    # that the default exists somewhere on the path that builds a report.
    # docs/TEST_DURABILITY.md, and §0.6's accidental-selector rule with a
    # filename as the selector.
    modules = [f for f in WORKER_SRC.rglob("*.py")
               if EXPECTED_DEFAULT in f.read_text(encoding="utf-8")]
    assert modules, (
        f"no module under {WORKER_SRC.name}/ supplies the "
        f"{EXPECTED_DEFAULT!r} default for a report's agent title"
    )


# ── the None leak, by render — RETIRED WITH ITS TEMPLATES ──────────────────
#
# Five tests here rendered the contact-block title expression and checked that
# a missing or NULL title fell back to the default rather than printing
# "None". Every copy of that expression was in the nine-page property tree
# (D-131) and the old self-contained theme files, which rendered nowhere and
# were deleted on 2026-10-26 after a byte-identical render of every surface.
# The live property page prints no agent title, so there is no expression left
# to render. `test_every_template_uses_the_boolean_default_form` below still
# holds any template that brings one back.


#: The contact-block default, matched WITH the quotes: the old cover expression
#: 'Licensed Real Estate Agent' contained "Real Estate Agent" as a substring.
OWNED = "'Real Estate Agent'"


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
