"""
Branding tools routes - Sample PDF generation and test email.

Pass B4: Download & Test Send
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

from .reports import require_account_id
from ..db import db_conn
from ..services.affiliates import verify_affiliate_account
from ..services.branding import get_branding_for_account

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
        # Get affiliate branding
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


@router.post("/test-email")
async def send_test_email(
    body: TestEmailRequest,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Send a test branded email to the specified address.
    
    Uses sample data (not real MLS data) to show how branding appears in emails.
    
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
    logo_url = branding.get("logo_url")
    primary_color = branding.get("primary_color") or "#7C3AED"
    accent_color = branding.get("accent_color") or "#F26B2B"
    rep_photo_url = branding.get("rep_photo_url")
    contact_line1 = branding.get("contact_line1")
    contact_line2 = branding.get("contact_line2")
    website_url = branding.get("website_url")
    
    # Build sample email HTML
    report_type_display = body.report_type.replace("_", " ").title()
    
    email_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{report_type_display} Report - Sample</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f9fafb;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td align="center" style="padding: 40px 0;">
                    <table role="presentation" style="width: 600px; max-width: 100%; background-color: #ffffff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">
                        
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 30px; text-align: center; background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 100%); border-radius: 8px 8px 0 0;">
                                {f'<img src="{logo_url}" alt="{brand_name}" style="height: 50px; margin-bottom: 20px; object-fit: contain;" />' if logo_url else f'<div style="font-size: 32px; font-weight: 700; color: white; margin-bottom: 20px;">{brand_name[0]}</div>'}
                                <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700;">📊 Sample {report_type_display} Report</h1>
                                <p style="margin: 10px 0 0; color: #e0e7ff; font-size: 14px;">Beverly Hills • Last 30 days</p>
                                <p style="margin: 15px 0 0; color: #ffffff; font-size: 14px; font-weight: 500;">{brand_name}</p>
                            </td>
                        </tr>
                        
                        <!-- Body -->
                        <tr>
                            <td style="padding: 30px 40px;">
                                <p style="margin: 0; font-size: 16px; color: #374151; line-height: 1.6;">
                                    Hi there,
                                </p>
                                <p style="margin: 15px 0 0; font-size: 16px; color: #374151; line-height: 1.6;">
                                    This is a <strong>test email</strong> showing how your branding appears in scheduled report emails. When your sponsored agents receive their market reports, they'll see your branding just like this!
                                </p>
                                
                                <div style="margin: 25px 0; padding: 20px; background-color: #f3f4f6; border-radius: 8px;">
                                    <h3 style="margin: 0 0 15px 0; font-size: 16px; color: #374151;">Sample Metrics</h3>
                                    <table style="width: 100%; border-collapse: collapse;">
                                        <tr>
                                            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 14px;">Median Price</td>
                                            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #111827; font-size: 14px; font-weight: 600; text-align: right;">$4,150,000</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 14px;">Active Listings</td>
                                            <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #111827; font-size: 14px; font-weight: 600; text-align: right;">127</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 10px 0; color: #6b7280; font-size: 14px;">Days on Market</td>
                                            <td style="padding: 10px 0; color: #111827; font-size: 14px; font-weight: 600; text-align: right;">42</td>
                                        </tr>
                                    </table>
                                </div>
                                
                                <p style="margin: 20px 0; font-size: 14px; color: #6b7280; text-align: center;">
                                    In a real report, there would be a button here to download the full PDF report.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; border-radius: 0 0 8px 8px;">
                                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        {f'''<td style="width: 60px; vertical-align: top; padding-right: 15px;">
                                            <img src="{rep_photo_url}" alt="Representative" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 2px solid {primary_color};" />
                                        </td>''' if rep_photo_url else ''}
                                        <td style="vertical-align: top;">
                                            <p style="margin: 0; font-size: 14px; color: #374151; font-weight: 600;">{brand_name}</p>
                                            {f'<p style="margin: 3px 0 0; font-size: 12px; color: #6b7280;">{contact_line1}</p>' if contact_line1 else ''}
                                            {f'<p style="margin: 0; font-size: 12px; color: #6b7280;">{contact_line2}</p>' if contact_line2 else ''}
                                            {f'<p style="margin: 5px 0 0; font-size: 12px;"><a href="{website_url}" style="color: {primary_color}; text-decoration: none;">{website_url.replace("https://", "").replace("http://", "")}</a></p>' if website_url else ''}
                                        </td>
                                    </tr>
                                </table>
                                <p style="margin: 20px 0 0; font-size: 11px; color: #9ca3af; text-align: center;">
                                    This is a test email from {brand_name}. In production, recipients can unsubscribe from scheduled reports.
                                </p>
                            </td>
                        </tr>
                        
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
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

