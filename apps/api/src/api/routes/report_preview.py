"""
Report previews — the first page of a market report, rendered by the worker.

Every report image in the web app (the landing carousel and hero, the
wizard's kind grid and right panel, the dashboard's tilted page, the report
rows' thumbnails) is this route in an iframe. Before it, they were a React
redraw of the report (`components/shared/pdf-preview`) that nothing tied to
the worker's templates: seven kinds moved to Design's `_v2` page on
2026-10-07/08 and the redraw kept showing the page they had left.

So the preview is not a picture of the report. It IS the report — the same
`MarketReportBuilder.render_html()` production sends — on the canned data
`services/sample_report_data.py` already keeps for the branding page's sample
PDF. A template change shows up here with nothing else to regenerate.

PUBLIC, because the landing page has no session. That is safe for what it
serves and only because of what it accepts:

  * The data is the canned sample, always. No account, no MLS, no person.
  * Every parameter is checked against a closed shape before it reaches the
    builder (a hex colour, a lookback from the wizard's own five, a city of
    letters and spaces). Jinja autoescapes as well; this does not rely on it.
  * `ai_insights` is supplied by the sample, so the builder makes no OpenAI
    call. A public route that paid per request would be the problem.
  * The response forbids scripts (CSP), and the web app frames it with an
    empty `sandbox`, so nothing in it could run on either origin.
"""

import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from ..services.sample_report_data import SUPPORTED_SAMPLE_REPORT_TYPES, get_sample_data
from .branding_tools import _load_market_report_builder

router = APIRouter(prefix="/v1/report-preview", tags=["report-preview"])

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
#: Letters (any script), spaces, and the punctuation real city names carry —
#: or up to five ZIPs, which is the other thing the wizard's area can be.
_CITY = re.compile(
    r"^(?:[^\W\d_][^\W\d_ .'\-]*(?:[ .'\-]+[^\W\d_]+)*\.?|\d{5}(?:, ?\d{5}){0,4})$", re.UNICODE
)
_LOOKBACKS = {7, 14, 30, 60, 90}

#: The previews render in iframes; a preview is not a document to script.
_CSP = (
    "default-src 'none'; img-src https: data:; style-src 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com data:; frame-ancestors *"
)


@router.get("/{kind}/facts")
def report_preview_facts(kind: str):
    """The sample's figures, for a page that quotes the preview beside it.

    The landing page's monthly-email card states the Snapshot's median and
    counts next to the Snapshot's page. Kept anywhere but here, they are a copy
    of the sample, and a copy is what disagreed with the page before (D-228).
    """
    if kind not in SUPPORTED_SAMPLE_REPORT_TYPES:
        raise HTTPException(status_code=404, detail=f"No preview for {kind!r}")
    data = get_sample_data(kind)
    return {
        "lookback_days": data.get("lookback_days"),
        "counts": data.get("counts") or {},
        "metrics": data.get("metrics") or {},
    }


@router.get("/{kind}", response_class=HTMLResponse)
def report_preview(
    kind: str,
    primary: Optional[str] = Query(None),
    accent: Optional[str] = Query(None),
    city: Optional[str] = Query(None, max_length=40),
    days: int = Query(30),
):
    if kind not in SUPPORTED_SAMPLE_REPORT_TYPES:
        raise HTTPException(status_code=404, detail=f"No preview for {kind!r}")
    for name, value in (("primary", primary), ("accent", accent)):
        if value is not None and not _HEX.match(value):
            raise HTTPException(status_code=422, detail=f"{name} must be #rrggbb")
    city = (city or "").strip() or "Irvine"
    if not _CITY.match(city):
        raise HTTPException(status_code=422, detail="city must be a city name or up to five ZIPs")
    if days not in _LOOKBACKS:
        raise HTTPException(status_code=422, detail=f"days must be one of {sorted(_LOOKBACKS)}")

    Builder = _load_market_report_builder()
    if Builder is None:
        raise HTTPException(status_code=503, detail="Report renderer unavailable")

    data = dict(get_sample_data(kind, city=city, lookback_days=days))
    data["branding"] = {"primary_color": primary, "accent_color": accent}
    data["accent_color"] = accent
    html = Builder(data).render_html()

    return HTMLResponse(
        html,
        headers={
            "Content-Security-Policy": _CSP,
            # Same parameters, same page, until the next deploy.
            "Cache-Control": "public, max-age=3600",
        },
    )
