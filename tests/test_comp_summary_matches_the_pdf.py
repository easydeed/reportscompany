"""The /r page and the PDF read the same comps the same way (D-350, D-351).

`api/services/comp_summary.py` restates the PDF builder's rules because the API
cannot import the worker. A restatement drifts, so this runs the property
fixture's comps through both and compares what each prints: the range, the
median sale price, the median $/sq ft, the window and the radius. It also
holds the worker's stored range (`consumer_comps_range`) to the same answer.
"""
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for p in ("apps/api/src", "apps/worker/src", "apps/worker/tests"):
    sys.path.insert(0, str(REPO / p))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")

from api.services.comp_summary import RANGE_METHOD, summarize  # noqa: E402
from worker.property_builder import PropertyReportBuilder, THEME_TEMPLATES  # noqa: E402
from worker.tasks import consumer_comps_range  # noqa: E402
from test_property_production_render import COMPS, report_data  # noqa: E402

PropertyReportBuilder._fetch_market_trends = lambda self: None


def _pdf():
    # Any live theme: the numbers do not depend on it. Taken from the registry,
    # not named here (tests/test_rename_scope_numbers_are_current.py).
    html = PropertyReportBuilder(report_data(sorted(THEME_TEMPLATES)[0])).render_html()
    return re.sub(r"\s+", " ", html.split("</style>", 1)[1])


def test_the_range_is_the_pdfs():
    s = summarize(COMPS)
    body = _pdf()
    low, high = s["range"]["low"], s["range"]["high"]
    # The compare table prints the low and high sale in full.
    assert f"${low:,}" in body and f"${high:,}" in body
    assert RANGE_METHOD in body


def test_the_medians_are_the_pdfs():
    s = summarize(COMPS)
    body = _pdf()
    def cells(label):
        row = re.search(rf'class="compare-label">{label}</span>(.*?)</div>', body)
        assert row, f"no compare row {label!r}"
        return re.findall(r'class="compare-cell">([^<]*)<', row.group(1))
    low, mid, high = cells("Sale price")
    assert mid == f"${s['median_price']:,}"
    assert cells("Price per sq ft")[1] == f"${s['median_price_per_sqft']:,}"


def test_the_window_and_radius_are_the_pdfs():
    s = summarize(COMPS)
    aside = re.search(r"within ([\d.]+) mi · last (\d+) months", _pdf())
    assert aside, "the PDF's comps page heading did not match"
    assert float(aside.group(1)) == s["radius_miles"]
    assert int(aside.group(2)) == s["window_months"]


def test_the_worker_stores_the_same_range_and_no_estimate():
    stored = consumer_comps_range(COMPS)
    s = summarize(COMPS)
    assert stored == {"low": s["range"]["low"], "high": s["range"]["high"], "count": s["range"]["count"]}
    assert "mid" not in stored and "confidence" not in stored


def test_an_asking_price_is_not_a_sale():
    comps = [{"price": 500000, "status": "Closed", "sqft": 1000},
             {"price": 900000, "status": "Active", "sqft": 1000}]
    assert summarize(comps)["range"]["high"] == 500000
    assert consumer_comps_range(comps)["high"] == 500000


def test_no_closed_sales_gives_no_range():
    assert summarize([{"price": 900000, "status": "Active"}])["range"] is None
    assert consumer_comps_range([]) == {}
