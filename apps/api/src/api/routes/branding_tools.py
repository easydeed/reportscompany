"""
Branding tools routes - Sample PDF generation and test email.

Pass B4: Download & Test Send

V3.1: Unified with worker email template for single source of truth.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from urllib.parse import urlencode
import io
import os
import httpx
import logging
import sys

from .reports import require_account_id
from ..db import db_conn
from ..services.affiliates import verify_affiliate_account

# Import the unified email template from worker
# This ensures test emails match production emails exactly
try:
    # Add worker path to allow importing
    import importlib.util
    worker_template_path = os.path.join(
        os.path.dirname(__file__), 
        "../../../../worker/src/worker/email/template.py"
    )
    spec = importlib.util.spec_from_file_location("email_template", worker_template_path)
    email_template_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(email_template_module)
    schedule_email_html = email_template_module.schedule_email_html
    UNIFIED_TEMPLATE_AVAILABLE = True
except Exception as e:
    # Fallback if import fails (e.g., in certain deployment scenarios)
    UNIFIED_TEMPLATE_AVAILABLE = False
    schedule_email_html = None
    print(f"[Branding Tools] Could not import unified email template: {e}")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/branding", tags=["branding-tools"])

# PDFShift configuration
PDFSHIFT_API_KEY = os.getenv("PDF_API_KEY", "")
PDFSHIFT_URL = "https://api.pdfshift.io/v3/convert/pdf"
PRINT_BASE = os.getenv("PRINT_BASE", "https://www.trendyreports.io")

# SendGrid configuration (optional - for test emails)
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "reports@trendyreports.io")
DEFAULT_FROM_NAME = os.getenv("DEFAULT_FROM_NAME", "TrendyReports")


class SamplePdfRequest(BaseModel):
    """Request model for sample PDF generation."""
    report_type: str = "market_snapshot"


class TestEmailRequest(BaseModel):
    """Request model for test email."""
    email: EmailStr
    report_type: str = "market_snapshot"


def get_branding_for_account(cur, account_id: str) -> dict:
    """Get branding data for an account (affiliate or regular)."""
    # Check if this is an affiliate
    cur.execute("""
        SELECT account_type FROM accounts WHERE id = %s::uuid
    """, (account_id,))
    row = cur.fetchone()
    
    if row and row[0] == "INDUSTRY_AFFILIATE":
        # Get affiliate branding - try with email_logo_url first, fall back if column doesn't exist
        try:
            cur.execute("""
                SELECT 
                    brand_display_name,
                    logo_url,
                    email_logo_url,
                    primary_color,
                    accent_color,
                    rep_photo_url,
                    contact_line1,
                    contact_line2,
                    website_url
                FROM affiliate_branding
                WHERE account_id = %s::uuid
            """, (account_id,))
            brand_row = cur.fetchone()
            
            if brand_row:
                return {
                    "brand_display_name": brand_row[0],
                    "logo_url": brand_row[1],
                    "email_logo_url": brand_row[2],  # Light version for email headers
                    "primary_color": brand_row[3] or "#7C3AED",
                    "accent_color": brand_row[4] or "#F26B2B",
                    "rep_photo_url": brand_row[5],
                    "contact_line1": brand_row[6],
                    "contact_line2": brand_row[7],
                    "website_url": brand_row[8],
                }
        except Exception:
            # Fallback if email_logo_url column doesn't exist yet
            cur.execute("""
                SELECT 
                    brand_display_name,
                    logo_url,
                    primary_color,
                    accent_color,
                    rep_photo_url,
                    contact_line1,
                    contact_line2,
                    website_url
                FROM affiliate_branding
                WHERE account_id = %s::uuid
            """, (account_id,))
            brand_row = cur.fetchone()
            
            if brand_row:
                return {
                    "brand_display_name": brand_row[0],
                    "logo_url": brand_row[1],
                    "email_logo_url": None,  # Column doesn't exist yet
                    "primary_color": brand_row[2] or "#7C3AED",
                    "accent_color": brand_row[3] or "#F26B2B",
                    "rep_photo_url": brand_row[4],
                    "contact_line1": brand_row[5],
                    "contact_line2": brand_row[6],
                    "website_url": brand_row[7],
                }
    
    # Get account name as fallback
    cur.execute("""
        SELECT name, logo_url, primary_color 
        FROM accounts WHERE id = %s::uuid
    """, (account_id,))
    acc_row = cur.fetchone()
    
    return {
        "brand_display_name": acc_row[0] if acc_row else "Your Brand",
        "logo_url": acc_row[1] if acc_row else None,
        "email_logo_url": None,
        "primary_color": acc_row[2] if acc_row else "#7C3AED",
        "accent_color": "#F26B2B",
        "rep_photo_url": None,
        "contact_line1": None,
        "contact_line2": None,
        "website_url": None,
    }


@router.post("/sample-pdf")
async def generate_sample_pdf(
    body: SamplePdfRequest,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Generate a sample branded PDF for preview/download.
    
    Uses sample data (not real MLS data) to show how branding appears.
    The PDF is generated on-the-fly and not stored.
    
    Pass B4.1: Sample PDF Generation
    """
    report_type = body.report_type
    
    # Validate report type
    valid_types = [
        "market_snapshot", "new_listings", "inventory", "closed",
        "price_bands", "open_houses", "new_listings_gallery", "featured_listings"
    ]
    if report_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid report type: {report_type}")
    
    # Get branding
    with db_conn() as (conn, cur):
        branding = get_branding_for_account(cur, account_id)
    
    # Build the preview URL with branding params
    # We'll use a special preview endpoint that renders sample data
    params = {
        "brand_name": branding['brand_display_name'] or "Your Brand",
    }
    if branding.get("logo_url"):
        params["logo_url"] = branding['logo_url']
    if branding.get("primary_color"):
        params["primary_color"] = branding['primary_color'].replace('#', '')
    if branding.get("accent_color"):
        params["accent_color"] = branding['accent_color'].replace('#', '')
    # Pass contact/footer info for branded footer
    if branding.get("rep_photo_url"):
        params["rep_photo_url"] = branding['rep_photo_url']
    if branding.get("contact_line1"):
        params["contact_line1"] = branding['contact_line1']
    if branding.get("contact_line2"):
        params["contact_line2"] = branding['contact_line2']
    if branding.get("website_url"):
        params["website_url"] = branding['website_url']
    
    preview_url = f"{PRINT_BASE}/branding-preview/{report_type}?{urlencode(params)}"
    print(f"[Branding PDF] Preview URL: {preview_url}")
    
    # Generate PDF using PDFShift
    if not PDFSHIFT_API_KEY:
        # Fallback: return a simple HTML-based PDF placeholder
        raise HTTPException(
            status_code=503,
            detail="PDF generation service not configured. Please contact support."
        )
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                PDFSHIFT_URL,
                auth=("api", PDFSHIFT_API_KEY),
                json={
                    "source": preview_url,
                    "landscape": False,
                    "use_print": True,
                    "format": "Letter",
                    "margin": "0",
                },
            )
            
            if response.status_code != 200:
                print(f"[Branding PDF] PDFShift error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=502,
                    detail="Failed to generate PDF. Please try again."
                )
            
            pdf_bytes = response.content
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="PDF generation timed out. Please try again.")
    except Exception as e:
        print(f"[Branding PDF] Error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    # Return PDF as downloadable file
    filename = f"sample-{report_type.replace('_', '-')}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        }
    )


def _build_fallback_test_email(report_type: str, branding: dict, metrics: dict) -> str:
    """
    Fallback test email template if unified template import fails.
    This is a simplified version - prefer the unified template.
    """
    brand_name = branding.get("brand_display_name") or "Your Brand"
    primary_color = branding.get("primary_color") or "#7C3AED"
    accent_color = branding.get("accent_color") or "#F26B2B"
    report_type_display = report_type.replace("_", " ").title()
    
    return f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{brand_name} - {report_type_display} (Test)</title>
</head>
<body style="margin: 0; padding: 40px; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
  <table width="600" style="margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden;">
    <tr>
      <td style="background: linear-gradient(135deg, {primary_color}, {accent_color}); padding: 40px; text-align: center;">
        <h1 style="color: #fff; margin: 0; font-family: Georgia, serif;">{brand_name}</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0;">{report_type_display}</p>
      </td>
    </tr>
    <tr>
      <td style="padding: 40px;">
        <div style="background: #fef3c7; padding: 16px; border-radius: 8px; margin-bottom: 24px;">
          <p style="margin: 0; color: #92400e;"><strong>🧪 This is a test email</strong> — It shows how your branding appears.</p>
        </div>
        <table width="100%">
          <tr>
            <td style="text-align: center; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
              <p style="font-size: 30px; color: {primary_color}; margin: 0; font-family: Georgia, serif;">{metrics.get("total_active", 127)}</p>
              <p style="font-size: 11px; color: #64748b; margin: 8px 0 0; text-transform: uppercase;">Active Listings</p>
            </td>
            <td style="text-align: center; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
              <p style="font-size: 30px; color: {primary_color}; margin: 0; font-family: Georgia, serif;">$4.2M</p>
              <p style="font-size: 11px; color: #64748b; margin: 8px 0 0; text-transform: uppercase;">Median Price</p>
            </td>
            <td style="text-align: center; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
              <p style="font-size: 30px; color: {primary_color}; margin: 0; font-family: Georgia, serif;">{metrics.get("avg_dom", 42)} days</p>
              <p style="font-size: 11px; color: #64748b; margin: 8px 0 0; text-transform: uppercase;">Avg DOM</p>
            </td>
          </tr>
        </table>
        <p style="text-align: center; margin-top: 24px;">
          <a href="#" style="display: inline-block; background: {primary_color}; color: #fff; padding: 14px 32px; border-radius: 6px; text-decoration: none; font-family: Georgia, serif;">View Full Report →</a>
        </p>
      </td>
    </tr>
    <tr>
      <td style="padding: 24px; background: #f9fafb; text-align: center; border-top: 1px solid #e5e7eb;">
        <p style="margin: 0; font-size: 13px; color: #94a3b8;">Test email from <span style="color: {primary_color};">{brand_name}</span></p>
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
    # V4.2: Report-type-specific sample data for accurate test previews
    
    # Base metrics shared across report types
    base_metrics = {
        "total_active": 127,
        "median_list_price": 4200000,
        "median_close_price": 4150000,
        "avg_dom": 42,
        "months_of_inventory": 2.8,
        "sale_to_list_ratio": 98.5,
        "total_closed": 42,
        "total_pending": 18,
        "new_listings_7d": 23,
    }
    
    # Report-specific sample data
    report_specific_metrics = {
        "market_snapshot": {
            # Property type breakdown (segmentation)
            "sfr_count": 89,
            "condo_count": 28,
            "townhome_count": 10,
            # Price tier breakdown (segmentation)
            "entry_tier_count": 45,
            "entry_tier_range": "Under $1M",
            "moveup_tier_count": 52,
            "moveup_tier_range": "$1M - $3M",
            "luxury_tier_count": 30,
            "luxury_tier_range": "$3M+",
        },
        "new_listings": {
            "avg_ppsf": 892,  # Avg price per sq ft
            "total_active": 47,  # New listings count
        },
        "inventory": {
            "new_this_month": 34,  # New listings this month
            "total_active": 156,  # Active inventory
        },
        "closed": {
            "total_closed": 38,
            "total_volume": 158700000,  # Total sales volume
        },
        "price_bands": {
            "min_price": 450000,
            "max_price": 8500000,
            "bands": [
                {"name": "Entry Level", "range": "$450K - $750K", "count": 45},
                {"name": "Move-Up", "range": "$750K - $1.5M", "count": 62},
                {"name": "Premium", "range": "$1.5M - $3M", "count": 38},
                {"name": "Luxury", "range": "$3M+", "count": 22},
            ],
        },
        "open_houses": {
            "total_active": 24,
            "saturday_count": 15,
            "sunday_count": 18,
        },
        "new_listings_gallery": {
            "total_listings": 12,
            "min_price": 575000,
            "avg_sqft": 2450,
        },
        "featured_listings": {
            "total_listings": 6,
            "max_price": 12500000,
            "avg_sqft": 4200,
        },
    }
    
    # Merge base with report-specific metrics
    sample_metrics = {**base_metrics, **report_specific_metrics.get(body.report_type, {})}
    
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

