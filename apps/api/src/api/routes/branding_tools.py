"""
Branding tools routes - Sample PDF generation and test email.

Pass B4: Download & Test Send

V3.1: Unified with worker email template for single source of truth.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import io
import os
import httpx
import logging
import sys

from .reports import require_account_id
from ..db import db_conn
from ..services.affiliates import verify_affiliate_account
from ..services.brand_resolver import resolve_brand
from ..services.sample_report_data import (
    get_sample_data,
    SUPPORTED_SAMPLE_REPORT_TYPES,
)

# Import the unified email template
# Try shared package first, then worker path, then fallback
schedule_email_html = None
UNIFIED_TEMPLATE_AVAILABLE = False

# Option 1: Try shared package (ideal for local dev with poetry install)
try:
    from shared.email import schedule_email_html as _shared_template
    schedule_email_html = _shared_template
    UNIFIED_TEMPLATE_AVAILABLE = True
    print("[Branding Tools] ✅ Unified email template loaded from shared package")
except ImportError:
    pass

# Option 2: Try worker path (works when repo is deployed together)
if not UNIFIED_TEMPLATE_AVAILABLE:
    try:
        import importlib.util
        worker_template_path = os.path.join(
            os.path.dirname(__file__), 
            "../../../../worker/src/worker/email/template.py"
        )
        if os.path.exists(worker_template_path):
            spec = importlib.util.spec_from_file_location("email_template", worker_template_path)
            email_template_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(email_template_module)
            schedule_email_html = email_template_module.schedule_email_html
            UNIFIED_TEMPLATE_AVAILABLE = True
            print(f"[Branding Tools] ✅ Unified email template loaded from worker path")
    except Exception as e:
        print(f"[Branding Tools] ⚠️ Worker path import failed: {e}")

if not UNIFIED_TEMPLATE_AVAILABLE:
    print("[Branding Tools] ⚠️ Using fallback template (update shared package for full features)")


# ─────────────────────────────────────────────────────────────────────────────
# Worker MarketReportBuilder loader (Sample PDF Rewire — Issue 7)
#
# Sample PDFs now render via the worker's MarketReportBuilder so they go
# through the EXACT same code path as production reports (multi-page support,
# section labels, "+ N more" callouts, Outfit font, AI narrative section).
#
# The API process imports the worker package lazily on first use. The worker
# uses absolute imports like `from worker.template_filters import ...`, so we
# add the worker `src/` directory to sys.path before importing.
# ─────────────────────────────────────────────────────────────────────────────

_MarketReportBuilder = None  # cached class reference
_WORKER_IMPORT_ERROR: Optional[str] = None


def _load_market_report_builder():
    """
    Lazily import `worker.market_builder.MarketReportBuilder`.

    Returns the class on success, or None if the worker package or its
    transitive deps (jinja2, etc.) aren't available in the API runtime.
    Failure is cached so we don't retry on every request.
    """
    global _MarketReportBuilder, _WORKER_IMPORT_ERROR
    if _MarketReportBuilder is not None:
        return _MarketReportBuilder
    if _WORKER_IMPORT_ERROR is not None:
        return None

    try:
        worker_src = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "../../../../worker/src",
            )
        )
        if worker_src not in sys.path:
            sys.path.insert(0, worker_src)

        from worker.market_builder import MarketReportBuilder as _Cls
        _MarketReportBuilder = _Cls
        print(f"[Branding Tools] ✅ MarketReportBuilder loaded from {worker_src}")
        return _MarketReportBuilder
    except Exception as e:
        _WORKER_IMPORT_ERROR = f"{type(e).__name__}: {e}"
        print(f"[Branding Tools] ⚠️ MarketReportBuilder import failed: {_WORKER_IMPORT_ERROR}")
        return None


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/branding", tags=["branding-tools"])

# PDFShift configuration
PDFSHIFT_API_KEY = os.getenv("PDF_API_KEY", "")
PDFSHIFT_URL = "https://api.pdfshift.io/v3/convert/pdf"

# SendGrid configuration (optional - for test emails)
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "reports@trendyreports.io")
DEFAULT_FROM_NAME = os.getenv("DEFAULT_FROM_NAME", "TrendyReports")


class SamplePdfRequest(BaseModel):
    """Request model for sample PDF generation."""
    report_type: str = "market_snapshot"
    city: Optional[str] = None
    theme_id: Optional[int] = None


class SampleJpgRequest(BaseModel):
    """Request model for sample social image (JPG) generation."""
    report_type: str = "market_snapshot"
    city: Optional[str] = None
    theme_id: Optional[int] = None


def _build_agent_branding_ctx(cur, account_id: str, user_id: Optional[str]) -> dict:
    """
    Build the `branding` sub-dict that MarketReportBuilder expects.

    Pulls agent identity from the requesting user's profile (so the sample PDF
    shows the requester's name/phone/email in the agent card) and brand
    identity from `brand_resolver` (so title-rep inheritance applies).
    Falls back to sensible placeholders if no user is available.
    """
    resolved = resolve_brand(cur, account_id)

    agent = {
        "agent_name": "Your Name",
        "agent_title": "Real Estate Professional",
        "agent_phone": "",
        "agent_email": "",
        "agent_photo_url": None,
    }
    if user_id:
        try:
            cur.execute(
                """
                SELECT first_name, last_name, job_title, phone, email,
                       COALESCE(photo_url, avatar_url)
                FROM users
                WHERE id = %s::uuid AND is_active = TRUE
                """,
                (user_id,),
            )
            urow = cur.fetchone()
            if urow:
                full_name = f"{urow[0] or ''} {urow[1] or ''}".strip()
                agent = {
                    "agent_name": full_name or "Your Name",
                    "agent_title": urow[2] or "Real Estate Professional",
                    "agent_phone": urow[3] or "",
                    "agent_email": urow[4] or "",
                    "agent_photo_url": urow[5],
                }
        except Exception as e:
            logger.warning(f"[Sample PDF] Could not load user profile: {e}")

    return {
        **agent,
        "company_name": resolved["display_name"],
        "logo_url": resolved["logo_url"],
        "primary_color": resolved["primary_color"],
        "accent_color": resolved["accent_color"],
    }


def _render_sample_html(
    cur,
    account_id: str,
    user_id: Optional[str],
    report_type: str,
    city: Optional[str],
    theme_id: Optional[int],
) -> str:
    """
    Render the same HTML production uses, for the given account + report type.

    Raises HTTPException(503) if MarketReportBuilder cannot be imported.
    """
    Builder = _load_market_report_builder()
    if Builder is None:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Sample report renderer unavailable: {_WORKER_IMPORT_ERROR}. "
                "The worker package must be importable from the API runtime."
            ),
        )

    branding_ctx = _build_agent_branding_ctx(cur, account_id, user_id)

    sample = get_sample_data(report_type, city=city or "Irvine")

    builder_data = dict(sample)
    builder_data["branding"] = branding_ctx
    # accent_color at the top level lets the builder skip the branding lookup
    # path — mirrors how worker/tasks.py merges accent.
    builder_data["accent_color"] = branding_ctx.get("accent_color")
    if theme_id is not None:
        builder_data["theme_id"] = theme_id

    builder = Builder(builder_data)
    return builder.render_html()


class TestEmailRequest(BaseModel):
    """Request model for test email."""
    email: EmailStr
    report_type: str = "market_snapshot"


def get_branding_for_account(cur, account_id: str) -> dict:
    """
    Get branding data for an account (affiliate or regular).

    Uses the centralized brand_resolver so title reps inherit their parent
    company's logo/colors/display_name (unless branding_override=true). The
    rep-specific extras (rep_photo_url, contact lines, email_logo_url,
    website_url) always come from the rep's own row so the contact card
    still identifies the rep, not the parent company.

    Return shape is preserved for downstream consumers (sample PDF preview,
    test email rendering).
    """
    resolved = resolve_brand(cur, account_id)

    # Rep-level extras come from the rep's own affiliate_branding row when
    # present. These never inherit from the parent because the contact card
    # should identify the rep, not the company.
    rep_extras = {
        "email_logo_url": None,
        "rep_photo_url": None,
        "contact_line1": None,
        "contact_line2": None,
        "website_url": None,
    }
    try:
        cur.execute(
            """
            SELECT email_logo_url, rep_photo_url, contact_line1, contact_line2, website_url
            FROM affiliate_branding
            WHERE account_id = %s::uuid
            """,
            (account_id,),
        )
        extras_row = cur.fetchone()
        if extras_row:
            rep_extras = {
                "email_logo_url": extras_row[0],
                "rep_photo_url": extras_row[1],
                "contact_line1": extras_row[2],
                "contact_line2": extras_row[3],
                "website_url": extras_row[4],
            }
    except Exception:
        # email_logo_url may be missing on very old schemas — fall back gracefully.
        try:
            cur.execute(
                """
                SELECT rep_photo_url, contact_line1, contact_line2, website_url
                FROM affiliate_branding
                WHERE account_id = %s::uuid
                """,
                (account_id,),
            )
            extras_row = cur.fetchone()
            if extras_row:
                rep_extras = {
                    "email_logo_url": None,
                    "rep_photo_url": extras_row[0],
                    "contact_line1": extras_row[1],
                    "contact_line2": extras_row[2],
                    "website_url": extras_row[3],
                }
        except Exception:
            pass

    return {
        "brand_display_name": resolved["display_name"],
        "logo_url": resolved["logo_url"],
        "primary_color": resolved["primary_color"],
        "accent_color": resolved["accent_color"],
        **rep_extras,
    }


@router.post("/sample-pdf")
async def generate_sample_pdf(
    body: SamplePdfRequest,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Generate a sample branded PDF for preview/download.

    Renders the SAME HTML production uses (via worker.MarketReportBuilder) with
    canned sample data, then ships the rendered HTML to PDFShift. The output
    is therefore visually identical to a real generated market report —
    multi-page support, "Recent Activity" section labels, "Showing 8 of 50",
    "+ 42 more listings" callouts, Outfit font, AI narrative section, and the
    requesting account's resolved branding (with parent-rep inheritance).
    """
    report_type = body.report_type

    if report_type not in SUPPORTED_SAMPLE_REPORT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid report type: {report_type}")

    if not PDFSHIFT_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="PDF generation service not configured. Please contact support.",
        )

    user = getattr(request.state, "user", None)
    user_id = user.get("id") if user else None

    # Render HTML via the worker's MarketReportBuilder (synchronous — same code
    # path as production, just with canned `report_data`).
    with db_conn() as (conn, cur):
        html_content = _render_sample_html(
            cur,
            account_id=account_id,
            user_id=user_id,
            report_type=report_type,
            city=body.city,
            theme_id=body.theme_id,
        )
    print(f"[Branding PDF] Rendered HTML for {report_type}: {len(html_content)} chars")

    # Ship HTML to PDFShift. `source` accepts raw HTML as well as URLs.
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                PDFSHIFT_URL,
                headers={
                    "X-API-Key": PDFSHIFT_API_KEY,
                    "Content-Type": "application/json",
                    "X-Processor-Version": "142",
                },
                json={
                    "source": html_content,
                    "landscape": False,
                    "use_print": True,
                    "format": "Letter",
                    # Match worker pdf_adapter: margins handled by @page CSS.
                    "margin": {"top": "0", "right": "0", "bottom": "0", "left": "0"},
                    "remove_blank": True,
                    # Stock photos load from Unsplash — give PDFShift time.
                    "delay": 4000,
                    "wait_for_network": True,
                    "lazy_load_images": True,
                    "timeout": 100,
                },
            )

            if response.status_code != 200:
                print(f"[Branding PDF] PDFShift error: {response.status_code} - {response.text[:500]}")
                raise HTTPException(
                    status_code=502,
                    detail="Failed to generate PDF. Please try again.",
                )

            pdf_bytes = response.content
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="PDF generation timed out. Please try again.")
    except Exception as e:
        print(f"[Branding PDF] Error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    filename = f"sample-{report_type.replace('_', '-')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.post("/sample-jpg")
async def generate_sample_jpg(
    body: SampleJpgRequest,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Generate a sample branded JPG (1080x1920) for social media preview.

    Renders the SAME HTML production uses (via worker.MarketReportBuilder) and
    sends it to PDFShift's JPEG endpoint. The output captures the first
    viewport's worth of the report, suitable for Instagram Stories etc.
    """
    report_type = body.report_type

    if report_type not in SUPPORTED_SAMPLE_REPORT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid report type: {report_type}")

    if not PDFSHIFT_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Image generation service not configured. Please contact support.",
        )

    user = getattr(request.state, "user", None)
    user_id = user.get("id") if user else None

    with db_conn() as (conn, cur):
        html_content = _render_sample_html(
            cur,
            account_id=account_id,
            user_id=user_id,
            report_type=report_type,
            city=body.city,
            theme_id=body.theme_id,
        )
    print(f"[Branding JPG] Rendered HTML for {report_type}: {len(html_content)} chars")

    try:
        print(f"[Branding JPG] Calling PDFShift JPEG endpoint")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.pdfshift.io/v3/convert/jpeg",
                headers={
                    "X-API-Key": PDFSHIFT_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "source": html_content,
                    "viewport": "1080x1920",
                    "delay": 4000,
                },
            )
            
            print(f"[Branding JPG] PDFShift response status: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text[:1000]
                print(f"[Branding JPG] PDFShift error response: {error_detail}")
                
                # Try to parse error message
                try:
                    error_json = response.json()
                    error_msg = error_json.get("error", error_json.get("message", "Unknown error"))
                except Exception:
                    error_msg = f"HTTP {response.status_code}"
                
                raise HTTPException(
                    status_code=502,
                    detail=f"Image generation failed: {error_msg}"
                )
            
            jpg_bytes = response.content
            print(f"[Branding JPG] Success! Generated {len(jpg_bytes):,} bytes")
            
    except httpx.TimeoutException:
        print(f"[Branding JPG] Timeout after 120s - source: {preview_url}")
        raise HTTPException(status_code=504, detail="Image generation timed out. Please try again.")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Branding JPG] Unexpected error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")
    
    # Return JPG as downloadable file
    filename = f"sample-{report_type.replace('_', '-')}-social.jpg"
    
    return StreamingResponse(
        io.BytesIO(jpg_bytes),
        media_type="image/jpeg",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(jpg_bytes)),
        }
    )


def _build_fallback_test_email(report_type: str, branding: dict, metrics: dict) -> str:
    """
    Fallback test email template if unified template import fails.
    V6: Updated with mature stone color scheme and font-weight 900.
    """
    brand_name = branding.get("brand_display_name") or "Your Brand"
    primary_color = branding.get("primary_color") or "#7C3AED"
    accent_color = branding.get("accent_color") or "#F26B2B"
    report_type_display = report_type.replace("_", " ").title()
    
    # Format metrics
    total_active = metrics.get("total_active", 127)
    median_price = metrics.get("median_list_price") or metrics.get("median_close_price", 4200000)
    avg_dom = metrics.get("avg_dom", 42)
    
    # Format price
    if median_price >= 1_000_000:
        price_str = f"${median_price / 1_000_000:.1f}M"
    else:
        price_str = f"${median_price:,.0f}"
    
    return f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{brand_name} - {report_type_display} (Test)</title>
</head>
<body style="margin: 0; padding: 40px; background-color: #f5f5f4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
  <table width="600" style="margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden;">
    <tr>
      <td style="background: linear-gradient(135deg, {primary_color}, {accent_color}); padding: 40px; text-align: center; border-radius: 12px 12px 0 0;">
        <h1 style="color: #fff; margin: 0; font-size: 28px; font-weight: 400;">{brand_name}</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 14px;">{report_type_display}</p>
      </td>
    </tr>
    <tr>
      <td style="padding: 40px;">
        <div style="background: #fef3c7; padding: 16px; border-radius: 8px; margin-bottom: 24px;">
          <p style="margin: 0; color: #92400e;"><strong>🧪 This is a test email</strong> — It shows how your branding appears.</p>
        </div>
        <table width="100%" cellpadding="0" cellspacing="8">
          <tr>
            <td style="text-align: center; padding: 16px 8px; border: 1px solid #e7e5e4; border-radius: 8px; background: #ffffff;">
              <p style="font-size: 24px; font-weight: 900; color: {primary_color}; margin: 0 0 4px 0;">{total_active}</p>
              <p style="font-size: 10px; font-weight: 600; color: #78716c; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">Active Listings</p>
            </td>
            <td style="text-align: center; padding: 16px 8px; border: 1px solid #e7e5e4; border-radius: 8px; background: #ffffff;">
              <p style="font-size: 24px; font-weight: 900; color: {primary_color}; margin: 0 0 4px 0;">{price_str}</p>
              <p style="font-size: 10px; font-weight: 600; color: #78716c; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">Median Price</p>
            </td>
            <td style="text-align: center; padding: 16px 8px; border: 1px solid #e7e5e4; border-radius: 8px; background: #ffffff;">
              <p style="font-size: 24px; font-weight: 900; color: {primary_color}; margin: 0 0 4px 0;">{avg_dom}</p>
              <p style="font-size: 10px; font-weight: 600; color: #78716c; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">Avg Days on Market</p>
            </td>
          </tr>
        </table>
        <p style="text-align: center; margin-top: 24px;">
          <a href="#" style="display: inline-block; background: {primary_color}; color: #fff; padding: 14px 32px; border-radius: 6px; text-decoration: none; font-size: 15px; font-weight: 400;">View Full Report →</a>
        </p>
      </td>
    </tr>
    <tr>
      <td style="padding: 24px; background: #f9fafb; text-align: center; border-top: 1px solid #e7e5e4;">
        <p style="margin: 0; font-size: 13px; color: #a8a29e;">Test email from <span style="color: {primary_color};">{brand_name}</span></p>
      </td>
    </tr>
  </table>
</body>
</html>'''


@router.post("/test-email")
async def send_test_email(
    body: TestEmailRequest,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Send a test branded email to the specified address.
    
    Uses sample data (not real MLS data) to show how branding appears in emails.
    
    V3.1: Now uses the UNIFIED template from worker/email/template.py
    This ensures test emails match production emails exactly.
    
    Pass B4.2: Test Email
    """
    # Check if SendGrid is configured
    if not SENDGRID_API_KEY:
        logger.warning("[Test Email] SENDGRID_API_KEY not configured")
        raise HTTPException(
            status_code=503,
            detail="Email service not configured. Please contact support."
        )
    
    # Verify affiliate account and get branding
    with db_conn() as (conn, cur):
        verify_affiliate_account(cur, account_id)
        branding = get_branding_for_account(cur, account_id)
    
    brand_name = branding.get("brand_display_name") or "Your Brand"
    primary_color = branding.get("primary_color") or "#7C3AED"
    report_type_display = body.report_type.replace("_", " ").title()
    
    # Build sample metrics for test email
    # V5: Immaculate test data matching EXACTLY what report builders produce
    # These metrics mirror production scheduled emails for each report type
    
    # Report-specific sample data - matches report_builders.py output structure
    # Each report type has realistic data for its sample city
    report_sample_data = {
        # MARKET SNAPSHOT - Beverly Hills (Luxury Market)
        # Mirrors: build_market_snapshot_result() output
        "market_snapshot": {
            # Core counts (from counts.Active, counts.Closed, counts.Pending)
            "total_active": 89,           # Active inventory
            "total_closed": 42,           # Closed in last 30 days
            "total_pending": 18,          # Under contract
            "new_listings_7d": 23,        # New listings (from counts.NewListings)
            
            # Metrics (from metrics object)
            "median_list_price": 4500000,     # $4.5M median asking
            "median_close_price": 4200000,    # $4.2M median sale
            "avg_dom": 42,                    # 42 days average
            "avg_ppsf": 1250,                 # $1,250/sqft
            "months_of_inventory": 2.8,       # Seller's market
            "close_to_list_ratio": 98.5,      # Strong close-to-list
            "sale_to_list_ratio": 98.5,       # Alias for template compatibility
            
            # Property type breakdown (from by_property_type)
            "sfr_count": 62,              # Single Family homes
            "condo_count": 18,            # Condominiums
            "townhome_count": 9,          # Townhomes
            
            # Price tier breakdown (from price_tiers)
            "entry_tier_count": 28,       # Entry level count
            "entry_tier_range": "Under $2.5M",
            "moveup_tier_count": 34,      # Move-up count
            "moveup_tier_range": "$2.5M - $5M",
            "luxury_tier_count": 27,      # Luxury count
            "luxury_tier_range": "$5M+",
        },
        
        # NEW LISTINGS - Pasadena (Active Market)
        # Mirrors: build_new_listings_result() output
        "new_listings": {
            "total_active": 47,           # New listings in period
            "total_closed": 0,            # N/A for this report
            "total_pending": 0,           # N/A for this report
            "new_listings_7d": 47,        # Same as total for this report
            
            "median_list_price": 1350000, # $1.35M median
            "median_close_price": 0,      # N/A
            "avg_dom": 18,                # Fresh inventory, low DOM
            "avg_ppsf": 625,              # $625/sqft
            "months_of_inventory": 0,     # N/A
            "close_to_list_ratio": 0,     # N/A
            "sale_to_list_ratio": 0,      # N/A
        },
        
        # INVENTORY - Glendale (Balanced Market)
        # Mirrors: build_inventory_result() output
        "inventory": {
            "total_active": 156,          # Total active inventory
            "total_closed": 0,            # N/A
            "total_pending": 0,           # N/A
            "new_listings_7d": 34,        # New this month
            "new_this_month": 34,         # Alias
            
            "median_list_price": 1150000, # $1.15M median
            "median_close_price": 0,      # N/A
            "median_dom": 28,             # Median DOM (not avg)
            "avg_dom": 28,                # For template compatibility
            "months_of_inventory": 3.2,   # Balanced market
            "close_to_list_ratio": 0,     # N/A
            "sale_to_list_ratio": 0,      # N/A
        },
        
        # CLOSED SALES - Burbank (Strong Sales)
        # Mirrors: build_closed_result() output
        "closed": {
            "total_active": 0,            # N/A
            "total_closed": 38,           # Closed in period
            "total_pending": 0,           # N/A
            "new_listings_7d": 0,         # N/A
            
            "median_list_price": 1180000, # Original list price
            "median_close_price": 1150000,# $1.15M median sale
            "avg_dom": 32,                # 32 days to sell
            "avg_ppsf": 585,              # $585/sqft
            "months_of_inventory": 0,     # N/A
            "close_to_list_ratio": 99.2,  # Strong 99.2%
            "sale_to_list_ratio": 99.2,   # Alias
            "total_volume": 43700000,     # $43.7M total volume
        },
        
        # PRICE BANDS - Santa Monica (Premium Market)
        # Mirrors: build_price_bands_result() output
        "price_bands": {
            "total_active": 167,          # Total inventory
            "total_closed": 0,            # N/A
            "total_pending": 0,           # N/A
            "new_listings_7d": 0,         # N/A
            
            "median_list_price": 2800000, # $2.8M median
            "median_close_price": 0,      # N/A
            "avg_dom": 45,                # Average DOM
            "min_price": 895000,          # Lowest listing
            "max_price": 15000000,        # Highest listing
            "months_of_inventory": 0,     # N/A
            "close_to_list_ratio": 0,     # N/A
            "sale_to_list_ratio": 0,      # N/A
            
            # Price bands data
            "bands": [
                {"name": "Entry Level", "range": "Under $1.5M", "count": 42},
                {"name": "Move-Up", "range": "$1.5M - $3M", "count": 58},
                {"name": "Premium", "range": "$3M - $6M", "count": 45},
                {"name": "Luxury", "range": "$6M+", "count": 22},
            ],
        },
        
        # OPEN HOUSES - Manhattan Beach (Weekend Activity)
        # Mirrors: build_inventory_result() (reused)
        "open_houses": {
            "total_active": 24,           # Open houses available
            "total_closed": 0,
            "total_pending": 0,
            "new_listings_7d": 0,
            
            "median_list_price": 3200000, # $3.2M median
            "median_close_price": 0,
            "avg_dom": 0,
            "saturday_count": 15,         # Saturday events
            "sunday_count": 18,           # Sunday events
            "months_of_inventory": 0,
            "close_to_list_ratio": 0,
            "sale_to_list_ratio": 0,
        },
        
        # NEW LISTINGS GALLERY - Redondo Beach
        # Mirrors: build_new_listings_gallery_result() output
        "new_listings_gallery": {
            "total_active": 12,           # Gallery shows 9, but 12 total
            "total_listings": 12,
            "total_closed": 0,
            "total_pending": 0,
            "new_listings_7d": 12,
            
            "median_list_price": 1450000, # $1.45M median
            "median_close_price": 0,
            "avg_dom": 14,
            "min_price": 875000,          # Starting at
            "avg_sqft": 2450,             # Average size
            "months_of_inventory": 0,
            "close_to_list_ratio": 0,
            "sale_to_list_ratio": 0,
        },
        
        # FEATURED LISTINGS - Malibu (Ultra-Luxury)
        # Mirrors: build_featured_listings_result() output
        "featured_listings": {
            "total_active": 6,            # Featured properties
            "total_listings": 6,
            "total_closed": 0,
            "total_pending": 0,
            "new_listings_7d": 0,
            
            "median_list_price": 8500000, # $8.5M median
            "median_close_price": 0,
            "avg_dom": 65,
            "max_price": 12500000,        # Top listing
            "avg_sqft": 4200,             # Large homes
            "months_of_inventory": 0,
            "close_to_list_ratio": 0,
            "sale_to_list_ratio": 0,
        },
    }
    
    # V5: Sample listings for gallery reports and listings tables
    # Gallery reports use placeholder photos - production uses R2-proxied MLS photos
    # Table reports show Address, Beds, Baths, Price
    sample_listings_data = {
        # INVENTORY - 10 properties for table (Glendale)
        "inventory": [
            {"street_address": "1245 N Central Ave", "city": "Glendale", "bedrooms": 4, "bathrooms": 3, "list_price": 1295000},
            {"street_address": "823 E Glenoaks Blvd", "city": "Glendale", "bedrooms": 3, "bathrooms": 2, "list_price": 1150000},
            {"street_address": "456 W Dryden St", "city": "Glendale", "bedrooms": 5, "bathrooms": 4, "list_price": 1575000},
            {"street_address": "2901 Honolulu Ave", "city": "Glendale", "bedrooms": 3, "bathrooms": 2, "list_price": 985000},
            {"street_address": "1678 Grandview Ave", "city": "Glendale", "bedrooms": 4, "bathrooms": 3, "list_price": 1425000},
            {"street_address": "509 E Elk Ave", "city": "Glendale", "bedrooms": 2, "bathrooms": 2, "list_price": 875000},
            {"street_address": "3412 Ocean View Blvd", "city": "Glendale", "bedrooms": 4, "bathrooms": 3, "list_price": 1350000},
            {"street_address": "742 N Brand Blvd", "city": "Glendale", "bedrooms": 3, "bathrooms": 2, "list_price": 1095000},
            {"street_address": "1856 E Chevy Chase Dr", "city": "Glendale", "bedrooms": 5, "bathrooms": 4, "list_price": 1695000},
            {"street_address": "234 W Lexington Dr", "city": "Glendale", "bedrooms": 3, "bathrooms": 2, "list_price": 1025000},
        ],
        
        # CLOSED - Burbank (Recently Sold Properties)
        # Uses list_price field but displays close/sold price
        "closed": [
            {"street_address": "1532 N Niagara St", "city": "Burbank", "bedrooms": 4, "bathrooms": 3, "list_price": 1385000},
            {"street_address": "812 E Angeleno Ave", "city": "Burbank", "bedrooms": 3, "bathrooms": 2, "list_price": 1125000},
            {"street_address": "2415 W Clark Ave", "city": "Burbank", "bedrooms": 3, "bathrooms": 2, "list_price": 975000},
            {"street_address": "3201 W Burbank Blvd", "city": "Burbank", "bedrooms": 4, "bathrooms": 3, "list_price": 1245000},
            {"street_address": "1845 N Pass Ave", "city": "Burbank", "bedrooms": 5, "bathrooms": 4, "list_price": 1695000},
            {"street_address": "456 S Mariposa St", "city": "Burbank", "bedrooms": 2, "bathrooms": 2, "list_price": 825000},
            {"street_address": "2910 N Keystone St", "city": "Burbank", "bedrooms": 3, "bathrooms": 2, "list_price": 1050000},
            {"street_address": "1127 E Olive Ave", "city": "Burbank", "bedrooms": 4, "bathrooms": 3, "list_price": 1325000},
            {"street_address": "3645 W Victory Blvd", "city": "Burbank", "bedrooms": 3, "bathrooms": 2, "list_price": 985000},
            {"street_address": "2201 N Catalina St", "city": "Burbank", "bedrooms": 4, "bathrooms": 3, "list_price": 1195000},
        ],
        
        # NEW LISTINGS GALLERY - 9 properties (3x3 grid)
        "new_listings_gallery": [
            {"hero_photo_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&h=300&fit=crop", "street_address": "2847 Pacific Coast Hwy", "city": "Redondo Beach", "zip_code": "90277", "list_price": 1875000, "bedrooms": 4, "bathrooms": 3, "sqft": 2650},
            {"hero_photo_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=400&h=300&fit=crop", "street_address": "1523 Esplanade", "city": "Redondo Beach", "zip_code": "90277", "list_price": 1450000, "bedrooms": 3, "bathrooms": 2, "sqft": 1920},
            {"hero_photo_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=400&h=300&fit=crop", "street_address": "426 S Broadway", "city": "Redondo Beach", "zip_code": "90277", "list_price": 1295000, "bedrooms": 3, "bathrooms": 2, "sqft": 1750},
            {"hero_photo_url": "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=400&h=300&fit=crop", "street_address": "809 N Lucia Ave", "city": "Redondo Beach", "zip_code": "90277", "list_price": 1650000, "bedrooms": 4, "bathrooms": 3, "sqft": 2340},
            {"hero_photo_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400&h=300&fit=crop", "street_address": "3102 Manhattan Ave", "city": "Redondo Beach", "zip_code": "90266", "list_price": 2150000, "bedrooms": 5, "bathrooms": 4, "sqft": 3100},
            {"hero_photo_url": "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=400&h=300&fit=crop", "street_address": "1847 Prospect Ave", "city": "Redondo Beach", "zip_code": "90277", "list_price": 1125000, "bedrooms": 3, "bathrooms": 2, "sqft": 1540},
            {"hero_photo_url": "https://images.unsplash.com/photo-1600573472591-ee6981cf35e6?w=400&h=300&fit=crop", "street_address": "512 S Catalina Ave", "city": "Redondo Beach", "zip_code": "90277", "list_price": 1375000, "bedrooms": 3, "bathrooms": 3, "sqft": 1850},
            {"hero_photo_url": "https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=400&h=300&fit=crop", "street_address": "2219 Ruhland Ave", "city": "Redondo Beach", "zip_code": "90278", "list_price": 1595000, "bedrooms": 4, "bathrooms": 3, "sqft": 2180},
            {"hero_photo_url": "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=300&fit=crop", "street_address": "715 Knob Hill Ave", "city": "Redondo Beach", "zip_code": "90277", "list_price": 1250000, "bedrooms": 3, "bathrooms": 2, "sqft": 1680},
        ],
        
        # FEATURED LISTINGS - 4 luxury properties (2x2 grid)
        "featured_listings": [
            {"hero_photo_url": "https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=400&h=300&fit=crop", "street_address": "27150 Pacific Coast Hwy", "city": "Malibu", "zip_code": "90265", "list_price": 12500000, "bedrooms": 6, "bathrooms": 8, "sqft": 7850, "days_on_market": 45, "price_per_sqft": 1592},
            {"hero_photo_url": "https://images.unsplash.com/photo-1600566752355-35792bedcfea?w=400&h=300&fit=crop", "street_address": "23456 Malibu Colony Rd", "city": "Malibu", "zip_code": "90265", "list_price": 9750000, "bedrooms": 5, "bathrooms": 6, "sqft": 5400, "days_on_market": 62, "price_per_sqft": 1806},
            {"hero_photo_url": "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=400&h=300&fit=crop", "street_address": "32100 Broad Beach Rd", "city": "Malibu", "zip_code": "90265", "list_price": 8200000, "bedrooms": 5, "bathrooms": 5, "sqft": 4800, "days_on_market": 78, "price_per_sqft": 1708},
            {"hero_photo_url": "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=400&h=300&fit=crop", "street_address": "6543 Zuma Beach Dr", "city": "Malibu", "zip_code": "90265", "list_price": 7100000, "bedrooms": 4, "bathrooms": 5, "sqft": 4200, "days_on_market": 91, "price_per_sqft": 1690},
        ],
    }
    
    # Get metrics for the requested report type
    sample_metrics = report_sample_data.get(body.report_type, report_sample_data["market_snapshot"])
    
    # Get listings for gallery reports
    sample_listings = sample_listings_data.get(body.report_type)
    
    # Build brand dict for template
    brand_dict = {
        "display_name": branding.get("brand_display_name"),
        "logo_url": branding.get("logo_url"),
        "email_logo_url": branding.get("email_logo_url"),
        "primary_color": branding.get("primary_color") or "#7C3AED",
        "accent_color": branding.get("accent_color") or "#F26B2B",
        "rep_photo_url": branding.get("rep_photo_url"),
        "contact_line1": branding.get("contact_line1"),
        "contact_line2": branding.get("contact_line2"),
        "website_url": branding.get("website_url"),
    }
    
    # Sample cities per report type for visual distinction in test emails
    sample_cities = {
        "market_snapshot": "Beverly Hills",
        "new_listings": "Pasadena",
        "inventory": "Glendale",
        "closed": "Burbank",
        "price_bands": "Santa Monica",
        "open_houses": "Manhattan Beach",
        "new_listings_gallery": "Redondo Beach",
        "featured_listings": "Malibu",
    }
    sample_city = sample_cities.get(body.report_type, "Los Angeles")
    
    # Use unified template if available
    if UNIFIED_TEMPLATE_AVAILABLE and schedule_email_html:
        logger.info("[Test Email] Using unified template from worker")
        logger.info(f"[Test Email] Report type: {body.report_type}, City: {sample_city}")
        email_html = schedule_email_html(
            account_name=brand_name,
            report_type=body.report_type,
            city=sample_city,  # Report-specific sample city
            zip_codes=None,
            lookback_days=30,
            metrics=sample_metrics,
            pdf_url="#",  # Placeholder for test
            unsubscribe_url="#",  # Placeholder for test
            brand=brand_dict,
            listings=sample_listings,  # V5: Photo gallery for gallery reports
        )
        
        # Add test email notice banner after the preheader
        test_notice = '''
              <!-- Test Email Notice -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td style="background-color: #fef3c7; border-radius: 10px; padding: 16px 20px; border: 1px solid #fde68a;">
                    <p style="margin: 0; font-size: 14px; color: #92400e; line-height: 1.5;">
                      <strong>🧪 This is a test email</strong> — It shows how your branding appears in scheduled report emails.
                    </p>
                  </td>
                </tr>
              </table>
'''
        # Insert test notice after "MAIN CONTENT" comment
        # V4 templates may not have "Section Label" so try multiple insertion points
        has_v4_insight = '<!-- V4: Insight Paragraph -->' in email_html
        has_v4_hero = '<!-- V4: 4-Metric Hero Row' in email_html
        has_v4_core = '<!-- V4: Core Indicators' in email_html
        logger.info(f"[Test Email] V4 markers - Insight: {has_v4_insight}, Hero: {has_v4_hero}, Core: {has_v4_core}")
        
        if has_v4_insight:
            # V4: Insert before the insight paragraph
            logger.info("[Test Email] Using V4 template layout")
            email_html = email_html.replace(
                '<!-- V4: Insight Paragraph -->',
                test_notice + '\n              <!-- V4: Insight Paragraph -->'
            )
        elif '<!-- Section Label' in email_html:
            # V3 fallback: Insert before Section Label
            logger.info("[Test Email] Using V3 template layout (Section Label found)")
            email_html = email_html.replace(
                '<!-- Section Label',
                test_notice + '\n              <!-- Section Label'
            )
        else:
            # Ultimate fallback: Insert after MAIN CONTENT start
            logger.info("[Test Email] Using fallback insertion point")
            email_html = email_html.replace(
                'class="dark-card mobile-padding">',
                'class="dark-card mobile-padding">' + test_notice
            )
    else:
        # Fallback to inline template if import failed
        logger.warning("[Test Email] Using fallback inline template")
        email_html = _build_fallback_test_email(body.report_type, branding, sample_metrics)
    
    # Send via SendGrid
    payload = {
        "personalizations": [
            {
                "to": [{"email": body.email}],
                "subject": f"[Test] Sample {report_type_display} Report - {brand_name}",
            }
        ],
        "from": {
            "email": DEFAULT_FROM_EMAIL,
            "name": brand_name,  # Use affiliate brand name as sender
        },
        "content": [
            {
                "type": "text/html",
                "value": email_html,
            }
        ],
    }
    
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        logger.info(f"[Test Email] Sending to {body.email} for brand {brand_name}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(SENDGRID_API_URL, json=payload, headers=headers)
            
            if response.status_code == 202:
                logger.info(f"[Test Email] Sent successfully to {body.email}")
                return {
                    "ok": True,
                    "message": f"Test email sent to {body.email}",
                    "report_type": body.report_type,
                }
            else:
                error_text = response.text
                logger.error(f"[Test Email] SendGrid error {response.status_code}: {error_text}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to send email. Please try again."
                )
                
    except httpx.TimeoutException as e:
        logger.error(f"[Test Email] SendGrid timeout: {e}")
        raise HTTPException(status_code=504, detail="Email service timeout. Please try again.")
    except httpx.RequestError as e:
        logger.error(f"[Test Email] Request error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email. Please try again.")

