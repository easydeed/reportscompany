"""The consumer CMA's `report_data`, in one place both the task and its gate use.

WHY THIS MODULE EXISTS (D-140)
------------------------------
This dict used to be a literal inside `tasks.py`'s consumer branch, ~350 lines
into a Celery task with DB access woven around it. It was the **third** place
the consumer path drops fields, and the worst of the three: `apn`, `county`,
`legal_description` and `property_type` were already stored on
`consumer_reports.property_data` and simply never forwarded. The data survived
the whole pipeline and was discarded at the last hop, which is why every model
in the chain agreed and nothing caught it (D-139).

The gate that now catches that — `test_consumer_and_agent_reports_agree.py` —
could not import the literal, so it **mirrored** it. A gate that goes quiet
when somebody edits the thing it guards is worse than no gate, because it
reports green. Extracting the literal converts that mirroring into a real
import, so the gate reaches the fourth place by construction.

WHY IT IS PURE
--------------
Every input is a local the task already has by the time the literal is built:
`property_data` is fetched above, the brand row is unpacked above, and the
comparables are computed above. **No database access is inside the literal**,
so nothing had to move to make this a function — which is the whole reason the
extraction stayed the size of one ticket.

WHY THE ARGUMENTS ARE FLAT AND KEYWORD-ONLY
-------------------------------------------
Fifteen parameters is a lot. Grouping them into `brand` and `agent` dicts at
the call site would be tidier and would hand the caller two more small shapes
to assemble by hand — which is the exact defect this path has produced three
times (D-116, D-138, D-139). Keyword-only makes a mis-ordering impossible and
keeps every field the report needs visible in one signature.
"""
from typing import Any, Dict, List, Optional

#: The consumer CMA's page set.
#:
#: D-141. This diverged from the agent default by ACCIDENT, not by decision —
#: `git log -S` on every distinguishing string traces it to commit 182 of 182,
#: the squashed base, whose message is about Market Snapshot gallery rows. The
#: divergence dropped `analysis`, and with it the only page that places the
#: subject property against its comps: the comparison table, the sales chart,
#: and the last-sale price row. A homeowner who asked what their house is
#: worth received four neighbours' sale prices and nothing about their own.
#:
#: `analysis` restored 2026-09-30. `market_trends` and `overview` stay — they
#: suit this reader — but they were additions and were never a reason to
#: exclude the analysis.
#:
#: `contents` RESTORED 2026-10-01, D-121 fixed. It was held out because the
#: block was hardcoded and unguarded — it would have listed pages this set
#: does not contain and numbered them wrongly, and this set is exactly where
#: that shows, since it differs from the default on four pages. The rows are
#: now derived from the page set and the numbers counted at render time, so
#: the contents of a consumer report describes a consumer report.
#:
#: BEWARE: `market_trends` needs a live SimplyRETS fetch and `overview` needs
#: an OpenAI key, and `render_html` drops either without a word when its data
#: does not arrive (D-142). So this list is the MAXIMUM, not the guarantee —
#: six pages when both services answer, four when neither does. `analysis`
#: renders unconditionally, which is half of why it belongs here.
CONSUMER_PAGES = [
    "cover", "contents", "aerial", "property", "analysis",
    "comparables", "range",
    "market_trends", "overview",
]

DEFAULT_PRIMARY = "#1B365D"
DEFAULT_ACCENT = "#B8860B"
DEFAULT_THEME_ACCENT = "#34d1c3"
DEFAULT_THEME_ID = 4


def build_consumer_report_data(
    *,
    property_data: Dict[str, Any],
    prop_address: str,
    prop_city: str,
    prop_state: str,
    prop_zip: str,
    comparables: List[Dict[str, Any]],
    theme_id: Optional[int] = None,
    primary_color: str = "",
    secondary_color: str = "",
    brand_logo: Optional[str] = None,
    account_name: str = "",
    agent_name: str = "",
    agent_phone: str = "",
    agent_email: str = "",
    job_title: str = "",
    license_number: str = "",
    agent_photo: str = "",
    company_name: str = "",
) -> Dict[str, Any]:
    """`report_data` for `PropertyReportBuilder`, from a consumer lead capture.

    `property_data` is the JSON column on `consumer_reports`, written by
    `routes/lead_pages.request_report`. Every property fact the report shows
    must be read out of it here — a key present in the row and absent from
    this function is invisible everywhere downstream (D-139).
    """
    return {
        "report_type": "seller",
        "theme": theme_id or DEFAULT_THEME_ID,
        "accent_color": secondary_color or primary_color or DEFAULT_THEME_ACCENT,
        "property_address": prop_address,
        "property_city": prop_city,
        "property_state": prop_state,
        "property_zip": prop_zip,
        # D-116/D-157: NOT FORWARDED AT ALL, which is stronger than "read and
        # not rendered". The templates now CAN render an owner block — the
        # agent path carries one — so the consumer path's protection can no
        # longer be "no template does this". It is "this path does not have
        # the data", plus a rendered-output test for all five themes.
        #
        # `audience` is what the templates gate on; this omission is what
        # makes the gate unnecessary on this path rather than load-bearing.
        "audience": "consumer",
        # WHO ASKED, from the lead form. Absent when the form supplied none —
        # no line on the cover, and never the owner's name as a substitute.
        "prepared_for": property_data.get("requester_name", ""),
        # D-139: stored on the row and previously never forwarded.
        "apn": property_data.get("apn", ""),
        "property_county": property_data.get("county", ""),
        "legal_description": property_data.get("legal_description", ""),
        "property_type": property_data.get("property_type", ""),
        "sitex_data": {
            "latitude": property_data.get("latitude"),
            "longitude": property_data.get("longitude"),
            "bedrooms": property_data.get("bedrooms"),
            "bathrooms": property_data.get("bathrooms"),
            "sqft": property_data.get("sqft"),
            "lot_size": property_data.get("lot_size"),
            "year_built": property_data.get("year_built"),
            # D-139: `assessed_value` was the literal `0`, which renders "$0"
            # — a number, not a gap — in the field telling a homeowner what
            # their property is assessed at. The rest of the family was
            # absent entirely.
            "assessed_value": property_data.get("assessed_value"),
            "land_value": property_data.get("land_value"),
            "improvement_value": property_data.get("improvement_value"),
            "tax_amount": property_data.get("tax_amount"),
            "tax_year": property_data.get("tax_year"),
            # D-118: the same figure the agent path gets, or None — never a
            # substitute. This path reaches a stranger.
            "last_sale_price": property_data.get("last_sale_price"),
            "last_sale_date": property_data.get("last_sale_date"),
            "last_sale_price_per_sqft": property_data.get("last_sale_price_per_sqft"),
        },
        "comparables": comparables[:6],
        "agent": {
            "name": agent_name,
            "title": job_title or "Real Estate Agent",
            "phone": agent_phone or "",
            "email": agent_email or "",
            "license_number": license_number or "",
            "photo_url": agent_photo or "",
            "company_name": company_name or account_name or "",
            "logo_url": brand_logo or "",
        },
        "branding": {
            "display_name": account_name or "",
            "logo_url": brand_logo or "",
            "primary_color": primary_color or DEFAULT_PRIMARY,
            "accent_color": secondary_color or DEFAULT_ACCENT,
        },
        "selected_pages": list(CONSUMER_PAGES),
    }
