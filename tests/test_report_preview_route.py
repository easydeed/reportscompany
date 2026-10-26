"""`GET /v1/report-preview/{kind}` — every report image in the web app.

The route is public (the landing page has no session) and returns HTML the
browser frames, so what it accepts is the whole of its safety. These pin the
closed shapes, that the page is the worker's own render, and that the figures
`/facts` hands the landing page are the ones that page is drawn from.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
for p in (REPO / "apps/api/src", REPO / "apps/worker/src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from api.routes.report_preview import router  # noqa: E402
from api.services.sample_report_data import SUPPORTED_SAMPLE_REPORT_TYPES  # noqa: E402

app = fastapi.FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.mark.parametrize("kind", SUPPORTED_SAMPLE_REPORT_TYPES)
def test_every_kind_renders_the_worker_page(kind):
    r = client.get(f"/v1/report-preview/{kind}")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "script-src" not in r.headers["content-security-policy"]
    assert r.headers["content-security-policy"].startswith("default-src 'none'")
    assert "<script" not in r.text.lower()


def test_a_zip_list_is_an_area_too():
    r = client.get("/v1/report-preview/closed", params={"city": "92618, 92620"})
    assert r.status_code == 200 and "92618, 92620" in r.text


def test_colours_and_city_reach_the_page():
    r = client.get("/v1/report-preview/closed", params={"primary": "#7F1D1D", "city": "La Verne"})
    assert r.status_code == 200
    assert "La Verne" in r.text
    assert "#7f1d1d" in r.text.lower()


@pytest.mark.parametrize(
    "params",
    [
        {"primary": "red"},
        {"accent": "#fff"},
        {"primary": "#7F1D1D;background:url(x)"},
        {"city": "<script>alert(1)</script>"},
        {"city": 'Irvine" onload="x'},
        {"city": "x" * 41},
        {"city": "92618, 9262"},
        {"days": 45},
    ],
)
def test_anything_outside_the_shapes_is_refused(params):
    assert client.get("/v1/report-preview/closed", params=params).status_code == 422


def test_an_unknown_kind_is_a_404():
    assert client.get("/v1/report-preview/nope").status_code == 404
    assert client.get("/v1/report-preview/nope/facts").status_code == 404


def test_facts_are_the_sample_the_page_is_drawn_from():
    facts = client.get("/v1/report-preview/market_snapshot/facts").json()
    page = client.get("/v1/report-preview/market_snapshot").text
    median = facts["metrics"]["median_close_price"]
    # As the page prints it. Since D-255 the snapshot is Design's page, whose
    # big number is the short form ("$1.4M") through the shared filter — not
    # the legacy page's "$1,385,000".
    from worker.template_filters import format_currency_short
    assert format_currency_short(median, upper=True) in page
