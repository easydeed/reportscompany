"""
Mobile Report Viewer API Routes

Public endpoints for consumer report viewing.
No authentication required for viewing, tracks analytics.
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import json
import logging

from ..db import db_conn, fetchone_dict, fetchall_dicts
from ..services.comp_summary import summarize as summarize_comps
from ..services import comp_summary
from ..services.report_theme import consumer_report_color, resolve_theme_id, tokens_for
from ..services import consumer_pdf
from .leads import get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/r", tags=["mobile-reports"])


# =============================================
# SCHEMAS
# =============================================

class PropertyData(BaseModel):
    address: str
    city: str
    state: str
    zip: str
    # No `owner_name` (D-304). This response is public and goes to whoever
    # requested the report, who is often not the owner; D-116 and D-155 took
    # the assessor-roll name off the PDF and the email for the same reason.
    # The name stays in `property_data` for the agent path.
    apn: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[int] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tax_assessed_value: Optional[int] = None
    last_sale_date: Optional[str] = None
    last_sale_price: Optional[int] = None


def _present(value):
    """A positive number as the record has it, else None (D-168).

    For comp fields where 0 cannot be real: bedrooms, bathrooms, living area,
    price per sq ft, distance. Comps stored before D-168 carry 0 for absent;
    this is the rule the PDF applies to them (`V2_ZERO_IS_ABSENT`).
    """
    try:
        return value if value is not None and float(value) > 0 else None
    except (TypeError, ValueError):
        return None


class Comparable(BaseModel):
    address: str
    city: str
    state: str
    zip: str
    sold_price: int
    sold_date: str
    # D-168: None when the record has no value. These were required ints filled
    # with `or 0`, so a comp with no bedroom count showed "0 Beds" to the
    # homeowner. The viewer prints a dash for None.
    days_ago: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[int] = None
    year_built: Optional[int] = None
    price_per_sqft: Optional[int] = None
    distance_miles: Optional[float] = None
    photo_url: Optional[str] = None


class CompsRange(BaseModel):
    """The lowest and highest closed comparable sale, and the line the PDF
    prints beside them. Not an estimate: there is no point inside it, and no
    figure derived from the home's size (owner decision; see comp_summary)."""
    low: int
    high: int
    count: int
    method: str


class MarketStats(BaseModel):
    """The comps page of the PDF, in numbers: closed sales only, upper medians,
    the window and radius the comps actually cover."""
    median_price: Optional[int] = None
    median_price_per_sqft: Optional[int] = None
    avg_days_on_market: Optional[int] = None
    homes_sold: int = 0
    window_months: Optional[int] = None
    radius_miles: Optional[float] = None


class AgentInfo(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    photo_url: Optional[str] = None
    company_name: Optional[str] = None
    license_number: Optional[str] = None
    website: Optional[str] = None


class MobileReportResponse(BaseModel):
    id: str
    property: PropertyData
    comparables: List[Comparable]
    comps_range: Optional[CompsRange] = None
    market_stats: MarketStats
    agent: AgentInfo
    branding: Optional[dict] = None
    # The consumer PDF's theme and derived tokens (services/report_theme.py).
    theme: Optional[int] = None
    theme_tokens: Optional[dict] = None
    has_pdf: bool
    created_at: datetime


class AnalyticsEvent(BaseModel):
    event_type: str  # 'tab_change', 'agent_click', 'share', 'pdf_request'
    event_data: Optional[dict] = {}
    session_id: Optional[str] = None


# =============================================
# PUBLIC ENDPOINTS
# =============================================

@router.get("/{report_id}/data", response_model=MobileReportResponse)
async def get_report_data(
    report_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Get report data as JSON for client-side rendering.
    Tracks view analytics.
    """
    with db_conn() as (conn, cur):
        cur.execute(
            """
            SELECT 
                cr.*,
                CONCAT(u.first_name, ' ', u.last_name) as agent_name,
                u.phone as agent_phone,
                u.email as agent_email,
                u.avatar_url as agent_photo,
                u.company_name
            FROM consumer_reports cr
            JOIN users u ON cr.agent_id = u.id
            WHERE cr.id = %s AND cr.status IN ('ready', 'sent', 'processing', 'pending', 'needs_review', 'sending')
            """,
            (str(report_id),)
        )
        report = fetchone_dict(cur)
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    # Track view in background
    background_tasks.add_task(
        track_view,
        str(report_id),
        request.client.host if request.client else None,
        request.headers.get("user-agent"),
        detect_device_type(request.headers.get("user-agent", ""))
    )
    
    # Parse JSON fields
    property_data = report.get("property_data") or {}
    if isinstance(property_data, str):
        property_data = json.loads(property_data)
    
    comparables = report.get("comparables") or []
    if isinstance(comparables, str):
        comparables = json.loads(comparables)
    
    # `value_estimate` and `market_stats` on the row are not read. The first
    # was sqft x the comps' average $/sqft +/-8% with a "most likely" price,
    # an estimate the owner decided against; the second disagreed with the PDF
    # on window, radius and median. Both are recomputed from the stored comps
    # by the PDF's rules, which also corrects every report already sent.
    # LR-018: the list and the summary are built from the same usable comps.
    comparables = comp_summary.usable([c for c in comparables if isinstance(c, dict)])
    summary = summarize_comps(comparables)
    
    # Build property data with fallbacks
    prop = PropertyData(
        address=property_data.get("address") or report.get("property_address", ""),
        city=property_data.get("city") or report.get("property_city", ""),
        state=property_data.get("state") or report.get("property_state", ""),
        zip=property_data.get("zip") or report.get("property_zip", ""),
        apn=property_data.get("apn"),
        bedrooms=property_data.get("bedrooms"),
        bathrooms=property_data.get("bathrooms"),
        sqft=property_data.get("sqft"),
        lot_size=property_data.get("lot_size"),
        year_built=property_data.get("year_built"),
        property_type=property_data.get("property_type"),
        latitude=property_data.get("latitude"),
        longitude=property_data.get("longitude"),
        # D-133/D-135: `tax_assessed_value` was read and `assessed_value`
        # written — a naming mismatch, so this returned null since the
        # endpoint was written. Both spellings accepted; the one the producer
        # uses is second so a future rename does not silently win.
        tax_assessed_value=(property_data.get("tax_assessed_value")
                            or property_data.get("assessed_value")),
        # D-118: SiteX carries these in SaleLoanInfo and the parser now reads
        # them. Until this branch nothing wrote either, so this endpoint has
        # returned null for both since it was written.
        last_sale_date=property_data.get("last_sale_date"),
        last_sale_price=property_data.get("last_sale_price")
    )
    
    # Build comparables list
    # Handles BOTH old format (sold_price, sold_date, days_ago)
    # and new normalized format (price, close_price, close_date, days_on_market)
    comp_list = []
    for c in comparables:
        try:
            # LR-018: a sale shows what it sold for, by the same rule as the
            # range above; a sale with no recorded price is not a comparable.
            if comp_summary.is_sale(c):
                recorded = comp_summary.sale_price(c)
                if recorded is None:
                    continue
                sold_price = int(recorded)
            else:
                sold_price = c.get("sold_price") or c.get("price") or c.get("close_price") or 0
            # D-168: absent stays absent (see `_present`).
            sqft_val = _present(c.get("sqft"))

            # price_per_sqft: compute if not stored
            ppsf = _present(c.get("price_per_sqft") or c.get("pricePerSqft"))
            if ppsf is None and sold_price and sqft_val:
                ppsf = int(sold_price / sqft_val)

            # sold_date: prefer stored, else format from close_date ISO string
            sold_date_str = c.get("sold_date") or ""
            close_date_raw = c.get("close_date") or ""
            if not sold_date_str and close_date_raw:
                try:
                    raw_d = str(close_date_raw).split("T")[0]
                    sold_date_str = datetime.strptime(raw_d, "%Y-%m-%d").strftime("%b %d, %Y")
                except (ValueError, AttributeError):
                    sold_date_str = close_date_raw[:10]

            # days_ago: compute from close_date if not stored
            days_ago_val = c.get("days_ago") if c.get("days_ago") is not None else c.get("daysAgo")
            if days_ago_val is None and close_date_raw:
                try:
                    close_dt = datetime.fromisoformat(str(close_date_raw).replace("Z", "+00:00"))
                    days_ago_val = max(0, (datetime.now(close_dt.tzinfo) - close_dt).days)
                except (ValueError, AttributeError):
                    pass

            dist = _present(c.get("distance_miles") or c.get("distanceMiles"))

            comp_list.append(Comparable(
                address=c.get("address", ""),
                city=c.get("city", ""),
                state=c.get("state", ""),
                zip=c.get("zip") or c.get("zip_code", ""),
                sold_price=sold_price,
                sold_date=sold_date_str,
                days_ago=days_ago_val,
                bedrooms=_present(c.get("bedrooms")),
                bathrooms=_present(c.get("bathrooms")),
                sqft=int(sqft_val) if sqft_val is not None else None,
                lot_size=c.get("lot_size") or c.get("lotSize"),
                year_built=c.get("year_built") or c.get("yearBuilt"),
                price_per_sqft=ppsf,
                distance_miles=round(float(dist), 1) if dist is not None else None,
                photo_url=c.get("photo_url") or c.get("photoUrl")
            ))
        except Exception as e:
            logger.warning(f"Error parsing comparable: {e}")
            continue
    
    comps_range = CompsRange(**summary["range"]) if summary["range"] else None
    mkt_stats = MarketStats(
        median_price=summary["median_price"],
        median_price_per_sqft=summary["median_price_per_sqft"],
        avg_days_on_market=summary["avg_days_on_market"],
        homes_sold=summary["homes_sold"],
        window_months=summary["window_months"],
        radius_miles=summary["radius_miles"],
    )
    
    # Build agent info
    agent = AgentInfo(
        name=report.get("agent_name") or "",
        phone=report.get("agent_phone"),
        email=report.get("agent_email"),
        photo_url=report.get("agent_photo"),
        company_name=report.get("company_name")
    )
    
    # Fetch branding for viewer
    branding_data = None
    with db_conn() as (conn, cur):
        cur.execute("""
            SELECT a.primary_color, a.secondary_color, a.logo_url, a.default_theme_id
            FROM accounts a
            JOIN users u ON u.account_id = a.id
            WHERE u.id = %s
            LIMIT 1
        """, (str(report.get("agent_id")),))
        brand_row = cur.fetchone()
        # The consumer PDF: the account's primary, on its default theme
        # (consumer_report_data.build_consumer_report_data).
        theme_id = resolve_theme_id(brand_row[3] if brand_row else None)
        theme_tokens = tokens_for(consumer_report_color(brand_row[0] if brand_row else None))
        if brand_row:
            branding_data = {
                "primary_color": brand_row[0] or "#6366f1",
                "accent_color": brand_row[1] or "#8b5cf6",
                "logo_url": brand_row[2],
            }
    
    return MobileReportResponse(
        id=str(report["id"]),
        property=prop,
        comparables=comp_list,
        comps_range=comps_range,
        market_stats=mkt_stats,
        agent=agent,
        branding=branding_data,
        theme=theme_id,
        theme_tokens=theme_tokens,
        has_pdf=report.get("pdf_url") is not None,
        created_at=report["created_at"]
    )


# LR-022. What the download button is told, in words a homeowner can act on.
# The stored `pdf_error` is for operators and is never returned here.
PDF_MESSAGES = {
    "generating": "Your PDF is being prepared. This usually takes under a minute.",
    "failed": "We couldn't prepare your PDF. Please try again in a minute.",
    "unavailable": "The PDF will be available once your report has been delivered.",
    "rate_limited": "Too many PDF requests from this device. Please try again later.",
}

_PDF_ROW = """
    SELECT id, status, pdf_url, pdf_object_key, pdf_status, consumer_sms_sent_at,
           consumer_email_sent_at,
           (pdf_claimed_at IS NULL
            OR pdf_claimed_at < NOW() - make_interval(mins => %s)) AS pdf_claim_stale
    FROM consumer_reports WHERE id = %s
"""


def _queue_pdf_generation(report_id: str) -> None:
    """Queue the worker's render of a missing PDF. Raises if the queue is unreachable."""
    from celery import current_app
    current_app.send_task("generate_consumer_report_pdf", args=[report_id])


def _pdf_answer(state: str, row: dict) -> JSONResponse:
    if state == "ready":
        return JSONResponse({"status": "ready",
                             "pdf_url": consumer_pdf.download_link(row.get("pdf_object_key"),
                                                                   row.get("pdf_url"))})
    code = {"unavailable": 409, "rate_limited": 429}.get(state, 200)
    return JSONResponse({"status": state, "message": PDF_MESSAGES[state]}, status_code=code)


@router.post("/{report_id}/pdf")
async def generate_pdf_on_demand(report_id: UUID, request: Request):
    """
    The download button (LR-022, D-380).

    An existing PDF: a freshly signed link to it, every time (stored presigned
    URLs expire after 7 days). A delivered report with no PDF: one generation
    job, however many clicks, at most 20 requests an hour per visitor.
    Anything else: an honest status the page can show.
    """
    rid = str(report_id)
    with db_conn() as (conn, cur):
        cur.execute(_PDF_ROW, (consumer_pdf.PDF_CLAIM_WINDOW_MINUTES, rid))
        row = fetchone_dict(cur)
        if not row:
            raise HTTPException(404, "Report not found")
        state = consumer_pdf.pdf_state(row)
        if state == "ready":
            cur.execute("UPDATE consumer_reports SET pdf_requested_count = pdf_requested_count + 1 "
                        "WHERE id = %s", (rid,))
            conn.commit()
            return _pdf_answer("ready", row)
        if state in ("unavailable", "generating"):
            return _pdf_answer(state, row)

        # missing, failed, or a stale claim: a request to generate it.
        # The visitor's limit is checked and counted under its own lock, held
        # until the commit below, so concurrent requests cannot overshoot it.
        if not consumer_pdf.admit_generate_request(cur, rid, get_client_ip(request),
                                                   request.headers.get("user-agent")):
            logger.warning("PDF generation rate limit reached for a visitor on report %s", rid)
            return _pdf_answer("rate_limited", row)
        queued = consumer_pdf.queue_missing_pdf(cur, rid)
        conn.commit()
        if not queued:
            # Another click queued it a moment ago.
            return _pdf_answer("generating", row)
        try:
            _queue_pdf_generation(rid)
        except Exception:
            logger.exception("could not queue the PDF generation for report %s", rid)
            consumer_pdf.mark_queue_failed(cur, rid, "the generation job could not be queued")
            conn.commit()
            return _pdf_answer("failed", row)
    return _pdf_answer("generating", row)


@router.get("/{report_id}/pdf/status")
async def check_pdf_status(report_id: UUID):
    """Where the PDF stands, for polling. Never queues anything (LR-022)."""
    with db_conn() as (conn, cur):
        cur.execute(_PDF_ROW, (consumer_pdf.PDF_CLAIM_WINDOW_MINUTES, str(report_id)))
        row = fetchone_dict(cur)
    if not row:
        raise HTTPException(404, "Report not found")
    state = consumer_pdf.pdf_state(row)
    if state == "missing":
        # A delivered report with no PDF and no job: the page asks with POST.
        return JSONResponse({"status": "missing", "message": PDF_MESSAGES["failed"]})
    return _pdf_answer(state, row)


@router.post("/{report_id}/analytics")
async def track_analytics(
    report_id: UUID,
    event: AnalyticsEvent,
    request: Request
):
    """
    Track user interactions (tab changes, agent clicks, etc.)
    """
    with db_conn() as (conn, cur):
        # Validate report exists
        cur.execute(
            "SELECT 1 FROM consumer_reports WHERE id = %s",
            (str(report_id),)
        )
        if not cur.fetchone():
            raise HTTPException(404, "Report not found")
    
    # Track event
    await track_event(
        str(report_id),
        event.event_type,
        event.event_data or {},
        request.client.host if request.client else None,
        request.headers.get("user-agent"),
        event.session_id
    )
    
    # Update report record for quick stats
    with db_conn() as (conn, cur):
        if event.event_type == "agent_click":
            cur.execute(
                """
                UPDATE consumer_reports 
                SET agent_contact_clicked = true, 
                    agent_contact_type = %s
                WHERE id = %s
                """,
                (event.event_data.get("contact_type"), str(report_id))
            )
            conn.commit()
        elif event.event_type == "tab_change":
            cur.execute(
                """
                UPDATE consumer_reports 
                SET tabs_viewed = tabs_viewed || %s::jsonb
                WHERE id = %s
                """,
                (json.dumps([event.event_data.get("tab")]), str(report_id))
            )
            conn.commit()
    
    return {"success": True}


# =============================================
# HELPER FUNCTIONS
# =============================================

async def track_view(report_id: str, ip: str, user_agent: str, device_type: str):
    """Track page view and update counters."""
    try:
        with db_conn() as (conn, cur):
            cur.execute(
                """
                UPDATE consumer_reports SET
                    view_count = view_count + 1,
                    first_viewed_at = COALESCE(first_viewed_at, NOW()),
                    last_viewed_at = NOW(),
                    device_type = COALESCE(device_type, %s)
                WHERE id = %s
                """,
                (device_type, report_id)
            )
            conn.commit()
            
            cur.execute(
                """
                INSERT INTO report_analytics (report_id, event_type, ip_address, user_agent, device_type)
                VALUES (%s, 'view', %s, %s, %s)
                """,
                (report_id, ip, user_agent, device_type)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to track view: {e}")


async def track_event(report_id: str, event_type: str, event_data: dict, 
                      ip: str = None, user_agent: str = None, session_id: str = None):
    """Track analytics event."""
    try:
        with db_conn() as (conn, cur):
            cur.execute(
                """
                INSERT INTO report_analytics (report_id, event_type, event_data, ip_address, user_agent, session_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (report_id, event_type, json.dumps(event_data), ip, user_agent, session_id)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to track event: {e}")


def detect_device_type(user_agent: str) -> str:
    """Simple device detection from user agent."""
    ua = user_agent.lower()
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        return 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        return 'tablet'
    return 'desktop'

