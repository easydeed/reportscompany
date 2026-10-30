"""D-109 and D-086: a number nobody has is not 0.

D-109. The property context wrote `sitex_data.get("bedrooms") or 0` (and the
same for bathrooms, sq ft, lot and year), and the subject's stats used
`_safe_num(..., 0)`. The v2 page prints a 0-bedroom home as "Studio" — so
every house the county has no bedroom count for was a "Studio", and a home
with no year on record was "Built 0". A real 0 must stay a real 0.

D-086. `report_builders._median` and `_average` returned `0.0` for an empty
list, and the close-to-list ratio defaulted to `100.0`: a $0 median and
"sold at asking" for a market that had no sales to measure. Empty is None.
"""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker import report_builders  # noqa: E402
from worker.property_builder import PropertyReportBuilder  # noqa: E402

from test_property_production_render import report_data  # noqa: E402

THEMES = ("harbor", "linen", "atlas")
UNKNOWN = ("bedrooms", "bathrooms", "sqft", "lot_size", "year_built")


def _render(theme, **sitex):
    d = report_data(theme)
    d["sitex_data"] = {**d["sitex_data"], **sitex}
    return PropertyReportBuilder(d).render_html()


def _text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


@pytest.mark.parametrize("theme", THEMES)
def test_a_home_with_no_counts_on_record_is_not_a_studio_built_in_year_zero(theme):
    text = _text(_render(theme, **{k: None for k in UNKNOWN}))
    assert "Studio" not in text, "an unknown bedroom count printed as Studio"
    assert not re.search(r"\bBuilt\s+0\b|\b0\s+Built\b", text), "an unknown year printed as 0"
    assert not re.search(r"(?<![\d,.$])0 sq ft", text), "an unknown size printed as 0 sq ft"


@pytest.mark.parametrize("theme", THEMES)
def test_a_real_zero_bedroom_home_is_still_a_studio(theme):
    """POSITIVE CONTROL: 0 is a value; only absence is a dash."""
    assert "Studio" in _text(_render(theme, bedrooms=0))


def test_the_property_context_carries_absence_through():
    d = report_data("harbor")
    d["sitex_data"] = {**d["sitex_data"], **{k: None for k in UNKNOWN}, "bedrooms": 0}
    prop = PropertyReportBuilder(d)._build_property_context()
    assert prop["bedrooms"] == 0, "a real 0 was lost"
    for k in ("bathrooms", "sqft", "lot_size", "year_built"):
        assert prop[k] is None, f"{k}: unknown became {prop[k]!r}"


def test_the_subject_stats_carry_absence_through():
    d = report_data("harbor")
    d["sitex_data"] = {**d["sitex_data"], **{k: None for k in UNKNOWN}}
    piq = PropertyReportBuilder(d)._build_stats_context()["piq"]
    for k in UNKNOWN:
        assert piq[k] is None, f"subject {k}: unknown became {piq[k]!r}"


# ── D-086 ─────────────────────────────────────────────────────────────────

def test_an_empty_median_or_average_is_none_not_zero():
    assert report_builders._median([]) is None
    assert report_builders._average([]) is None
    assert report_builders._median([3, 1, 2]) == 2 and report_builders._average([1, 3]) == 2


def test_a_market_with_no_sales_has_no_close_price_and_no_ratio():
    """The snapshot with active listings and no closings: no median close,
    no close-to-list ratio, no days on market — never $0, 100% or 0 days."""
    active = [{"list_price": 900000, "days_on_market": 12, "price_per_sqft": 500, "status": "Active",
               "property_type": "RES", "sqft": 1800, "close_price": None, "city": "Anytown"}]
    res = report_builders.build_market_snapshot_result(active, {"city": "Anytown", "lookback_days": 30})
    m = res["metrics"]
    for key in ("median_close_price", "close_to_list_ratio", "avg_dom"):
        assert m.get(key) is None, f"{key} = {m.get(key)!r} for a market with no sales"
    assert m["median_list_price"] == 900000, "POSITIVE CONTROL: the active side still measures"
