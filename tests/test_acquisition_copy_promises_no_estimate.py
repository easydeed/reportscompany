"""LR-025 (D-383): acquisition copy promises only what the report delivers.

The homeowner report shows comparable sales and the range they support
(D-350, D-134), drawn from the past six months (twelve when six find too few).
It does not estimate a value. Before this ticket, the live Home Value Page
asked "What's your home worth today?", the landing page's mock of it offered
"Get my estimate", the agent's default page title was "What's Your Home
Worth?", the property-report card printed an "estimated value", and both
pages said the numbers came from "this month's" sales.

Jerry approved the replacement wording (DECISIONS_AND_LANES.md, Acquisition
wording): "See what homes like yours sold for" and "Get my report"; and on
2026-11-11: "Based on the last 6 months of sales" for the window line, and on
the property-report card "last 6 months" and "range of comparable sales".
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APPROVED_HEADING = "See what homes like yours sold for"
APPROVED_CTA = "Get my report"
APPROVED_WINDOW = "Based on the last 6 months of sales"
APPROVED_CARD = ("range of comparable sales", "last 6 months")

#: Every live surface that asks a homeowner (or tells an agent what a homeowner
#: gets) for a report. Historical Design samples under docs/ are not live.
SURFACES = {
    "home value page": "apps/web/app/cma/[code]/cma-funnel.tsx",
    "landing mock of it": "apps/web/components/marketing/lead-capture.tsx",
    "property-report card": "apps/web/components/marketing/property-reports.tsx",
    "lead-page settings": "apps/web/app/app/lead-page/lead-page-client.tsx",
    "page title default (account)": "apps/api/src/api/services/agent_code.py",
    "page title default (route)": "apps/api/src/api/routes/lead_pages.py",
    "home-value email": "apps/worker/src/worker/templates/email/home_value.jinja2",
}

#: Promises the report does not keep. Comments are stripped first, so a note
#: explaining the old wording does not trip this.
PROMISES = [
    (r"home(?:&apos;|'|’)?s? worth", "asks what the home is worth"),
    (r"get my estimate", "offers an estimate"),
    (r"estimated value", "names an estimated value"),
    (r"\ban estimate from\b", "calls the report an estimate"),
    (r"this month(?:&apos;|'|’)s (?:closed )?sales", "claims this month's sales (the window is 6 or 12 months)"),
    (r"last 90 days", "claims a 90-day window (the window is 6 or 12 months)"),
]


def _live_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        text = re.sub(r"(?m)#.*$", "", text)
        text = re.sub(r'"""[\s\S]*?"""', "", text)
    elif path.suffix == ".jinja2":
        text = re.sub(r"\{#[\s\S]*?#\}", "", text)
        text = re.sub(r"<!--(?!\[if)[\s\S]*?-->", "", text)
    else:
        text = re.sub(r"/\*[\s\S]*?\*/", "", text)
        text = re.sub(r"(?m)^\s*//.*$", "", text)
        text = re.sub(r"\{/\*[\s\S]*?\*/\}", "", text)
    return text


def test_no_live_surface_promises_an_estimate():
    found = []
    for name, rel in SURFACES.items():
        text = _live_text(ROOT / rel)
        for pattern, why in PROMISES:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                line = text.count("\n", 0, m.start()) + 1
                found.append(f"{name} ({rel}, live line {line}): {why}: {m.group(0)!r}")
    assert not found, "\n".join(found)


def test_the_home_value_page_and_its_mock_use_the_approved_heading():
    for rel in (SURFACES["home value page"], SURFACES["landing mock of it"]):
        assert APPROVED_HEADING in _live_text(ROOT / rel), rel


def test_the_mock_offers_the_approved_button():
    text = _live_text(ROOT / SURFACES["landing mock of it"])
    assert re.search(rf">\s*{APPROVED_CTA}\s*<", text), "the mock's button is not the approved label"


def test_the_default_page_title_is_the_approved_heading():
    """An agent who never set a headline gets it as the page title and the
    link-preview title (cma/[code]/page.tsx generateMetadata)."""
    for rel in (SURFACES["page title default (account)"], SURFACES["page title default (route)"]):
        assert f'"{APPROVED_HEADING}"' in _live_text(ROOT / rel), rel


def test_the_window_line_says_six_months():
    for rel in (SURFACES["home value page"], SURFACES["landing mock of it"]):
        assert APPROVED_WINDOW in _live_text(ROOT / rel).replace("&apos;", "'"), rel


def test_the_property_card_shows_a_range_of_comparable_sales_over_six_months():
    text = _live_text(ROOT / SURFACES["property-report card"]).lower()
    for phrase in APPROVED_CARD:
        assert phrase in text, phrase
