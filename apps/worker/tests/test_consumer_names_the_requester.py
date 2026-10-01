"""
D-155/D-156/D-157 — the report stopped naming the record owner; the envelope
carrying it did not.

D-116 removed the owner block from all five property templates because an
assessor-roll name under a heading calling the reader a "prospect", on a
report anyone can request for any address, reads as surveillance. That fixed
the document. Three sites outside it kept using the same name:

  * `tasks.py` greeted the requester with `owner_name`'s first name, so a
    neighbour who asked for a report on 123 Oak St received **"Hi Gerardo,"**
    — a third party's name, from public record, in an unsolicited email;
  * the agent notification SMS named the record owner as the lead, so the
    agent chased the wrong person;
  * `lead_pages.py` wrote `payload.name or payload.owner_name` into the CRM,
    recording the person who OWNS the house as the person who ASKED.

WHAT IS DELIBERATE NOW, AND WHY IT NEEDS A TEST
-------------------------------------------------
The two paths now differ ON PURPOSE for the first time: an agent running a
report on a property knowingly may see the owner of record; a stranger on a
lead page may not, and is addressed by the name they typed instead.

Every previous divergence between these paths was ACCIDENTAL — D-138 through
D-141 were four field crossings in one month. So this one is asserted against
the rendered document rather than trusted, in both directions: the consumer
report must not contain the owner, and the agent report must. A test for only
the first would pass if the block were dead everywhere, which is the state
D-116 left and this change deliberately ends.
"""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.consumer_report_data import build_consumer_report_data  # noqa: E402
from worker.property_builder import THEME_TEMPLATES, PropertyReportBuilder  # noqa: E402
from worker.tasks import requester_first_name, requester_name  # noqa: E402

from test_property_production_render import COMPS, report_data  # noqa: E402

THEMES = sorted(THEME_TEMPLATES)

OWNER = "HERNANDEZ GERARDO J"
SECOND = "HERNANDEZ MARIA E"
REQUESTER = "Dana Ortiz"


def consumer_html(theme, *, requester=REQUESTER):
    """The consumer path, through its own builder — not a hand-made dict."""
    property_data = {
        "address": "1358 5th Street", "city": "La Verne", "state": "CA",
        "zip": "91750", "apn": "8381-021-001", "county": "LOS ANGELES",
        "owner_name": OWNER, "secondary_owner": SECOND,
        "bedrooms": 2, "bathrooms": 1.0, "sqft": 786, "year_built": 1947,
        "last_sale_price": 369000, "last_sale_date": "2015-12-23",
    }
    if requester:
        property_data["requester_name"] = requester
    data = build_consumer_report_data(
        property_data=property_data, prop_address="1358 5th Street",
        prop_city="La Verne", prop_state="CA", prop_zip="91750",
        comparables=COMPS, theme_id=THEMES.index(theme) + 1,
        agent_name="Zoe Noelle", agent_phone="(213) 555-0100",
        agent_email="zoe@example.com", account_name="TrendyReports",
    )
    data["theme"] = theme
    return PropertyReportBuilder(data).render_html()


def agent_html(theme):
    data = dict(report_data(theme))
    data["owner_name"] = OWNER
    data["sitex_data"] = {**data["sitex_data"], "secondary_owner": SECOND}
    return PropertyReportBuilder(data).render_html()


# ── the consumer document ──────────────────────────────────────────────────

@pytest.mark.parametrize("theme", THEMES)
def test_no_assessor_owner_name_reaches_a_consumer_report(theme):
    """THE GATE. Asserted on the rendered document, because the templates now
    CAN render an owner block — so "no template does this" stopped being
    true, and inspecting templates would prove nothing."""
    html = consumer_html(theme)
    for name in (OWNER, SECOND, "HERNANDEZ", "GERARDO"):
        assert name not in html.upper(), (
            f"{theme}: the consumer report contains {name!r}, a name from the "
            f"assessor roll, on a document a stranger can request"
        )


@pytest.mark.parametrize("theme", THEMES)
def test_the_consumer_report_is_addressed_to_whoever_asked(theme):
    html = consumer_html(theme)
    assert f"Prepared for {REQUESTER}" in html, (
        f"{theme}: the requester's name is not on the cover"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_with_no_name_on_the_form_there_is_no_line_and_no_substitute(theme):
    """The failure mode this exists to prevent is not an empty line — it is a
    fallback. "Prepared for HERNANDEZ GERARDO J" would be worse than nothing
    by a wide margin."""
    html = consumer_html(theme, requester=None)
    assert "Prepared for" not in html, f"{theme}: an empty 'Prepared for' rendered"
    assert "HERNANDEZ" not in html.upper(), (
        f"{theme}: with no requester name, the report fell back to the owner"
    )


# ── the agent document, so the gate is not passing on a dead block ────────

@pytest.mark.parametrize("theme", THEMES)
def test_the_agent_report_does_carry_the_owner_of_record(theme):
    html = agent_html(theme)
    assert OWNER in html, (
        f"{theme}: the agent report has no owner of record — the consumer "
        f"gate above would pass whether or not the block exists"
    )
    assert "Owner of Record" in html
    assert "Prospective Property Owner" not in html, (
        f"{theme}: the old heading came back with the block"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_the_mailing_address_is_on_neither_path(theme):
    for html in (agent_html(theme), consumer_html(theme)):
        assert "mailing_address" not in html.lower()
        assert "Mailing Address" not in html


# ── the envelope ───────────────────────────────────────────────────────────

def test_the_greeting_names_the_requester():
    assert requester_first_name({"requester_name": "Dana Ortiz"}) == "Dana"


@pytest.mark.parametrize("row", [
    {"owner_name": OWNER},
    {"owner_name": OWNER, "requester_name": ""},
    {"owner_name": OWNER, "requester_name": "   "},
    {},
    None,
])
def test_an_unnamed_requester_is_never_given_the_owners_name(row):
    """Every shape the row arrives in. The old code read `owner_name` and
    would have answered "Gerardo" to all five of these."""
    assert requester_first_name(row) == ""
    assert requester_name(row) == ""


def test_nothing_in_the_worker_reads_an_owner_name_off_a_report_row():
    """The structural half. Both delivery sites looked perfectly ordinary
    while being wrong, and a third would too.

    Source-level because the greeting and the SMS are built inside a
    300-line Celery task with nothing importable at the point of use — the
    same wall D-140 hit. The helpers are importable; the sites that call
    them are not.
    """
    src = (Path(__file__).resolve().parents[1] / "src/worker/tasks.py").read_text(
        encoding="utf-8")
    offenders = [
        (n, line.strip()) for n, line in enumerate(src.split("\n"), 1)
        if 'property_data.get("owner_name")' in line
        or "property_data.get('owner_name')" in line
    ]
    assert not offenders, (
        "the worker reads an owner name off a report row:\n  "
        + "\n  ".join(f"tasks.py:{n}  {t}" for n, t in offenders)
        + "\nUse `requester_name()` — the person who asked is not the person "
          "on the deed."
    )


# ── the two defences, tested apart ─────────────────────────────────────────
#
# THERE ARE TWO, AND EITHER ALONE IS SUFFICIENT TODAY — which means removing
# either alone is INVISIBLE to a test that only renders the real consumer
# path. Found by trying it: dropping the `_audience` condition from a
# template changed nothing, because the consumer builder does not forward the
# owner name, so `property.owner_name` is `""` either way.
#
#   1. the consumer builder does not carry `owner_name` at all
#   2. the templates render the block only when `audience == "agent"`
#
# `test_no_assessor_owner_name_reaches_a_consumer_report` exercises them
# together and catches the realistic failure — a refactor reuniting the paths,
# which loses the audience flag AND restores the field, and which is what
# D-138 through D-141 each were. These two isolate them, so a change that
# quietly removes one defence is not waved through by the other.


@pytest.mark.parametrize("theme", THEMES)
def test_the_template_gate_holds_on_its_own(theme):
    """Defence 2, with defence 1 deliberately removed.

    The data is put in front of the templates exactly as an agent report
    would, and only `audience` says not to render it. If this passes while
    the gate is gone, the gate is decoration.
    """
    data = dict(report_data(theme))
    data["owner_name"] = OWNER
    data["sitex_data"] = {**data["sitex_data"], "secondary_owner": SECOND}
    data["audience"] = "consumer"
    html = PropertyReportBuilder(data).render_html()
    assert OWNER not in html, (
        f"{theme}: `audience=consumer` did not stop the owner block — the "
        f"only thing protecting the consumer path is that its builder omits "
        f"the field, and one refactor away that is nothing"
    )
    assert SECOND not in html


def test_the_builder_omission_holds_on_its_own():
    """Defence 1, stated as what it is: the consumer context has no owner.

    Asserted on the CONTEXT rather than the render, because the render is
    where defence 2 would mask it.
    """
    data = build_consumer_report_data(
        property_data={"address": "1358 5th Street", "owner_name": OWNER,
                       "secondary_owner": SECOND, "requester_name": REQUESTER},
        prop_address="1358 5th Street", prop_city="La Verne",
        prop_state="CA", prop_zip="91750", comparables=COMPS,
    )
    flat = repr(data).upper()
    assert OWNER not in flat and "HERNANDEZ" not in flat, (
        "the consumer builder forwards an owner name; the templates' audience "
        "gate is then the only thing between it and the page"
    )
    assert data.get("audience") == "consumer"
    assert data.get("prepared_for") == REQUESTER
