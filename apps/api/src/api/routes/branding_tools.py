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
# Note: get_branding_for_account is defined locally in this module (not imported)

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
    
    # Build sample email HTML using V0-style email-safe template
    report_type_display = body.report_type.replace("_", " ").title()
    
    # Build logo HTML (conditional)
    if logo_url:
        logo_html = f'<img src="{logo_url}" alt="{brand_name}" width="180" height="50" style="display: block; max-width: 180px; height: auto;" />'
    else:
        logo_html = f'<p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 24px; font-weight: 700; color: #ffffff;">{brand_name}</p>'
    
    # Build footer HTML (conditional based on available data)
    if rep_photo_url and (contact_line1 or contact_line2):
        footer_html = f'''
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td width="80" valign="top" style="padding-right: 20px;">
                    <img src="{rep_photo_url}" alt="Agent Photo" width="70" height="70" style="display: block; width: 70px; height: 70px; border-radius: 50%; object-fit: cover;" />
                  </td>
                  <td valign="middle">
                    {f'<p style="margin: 0 0 4px 0; font-family: Arial, Helvetica, sans-serif; font-size: 15px; font-weight: 600; color: #1f2937; line-height: 1.4;">{contact_line1}</p>' if contact_line1 else ''}
                    {f'<p style="margin: 0 0 8px 0; font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #6b7280; line-height: 1.4;">{contact_line2}</p>' if contact_line2 else ''}
                    {f'<a href="{website_url}" target="_blank" style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: {primary_color}; text-decoration: none; font-weight: 500;">{website_url.replace("https://", "").replace("http://", "")}</a>' if website_url else ''}
                  </td>
                </tr>
              </table>'''
    else:
        footer_html = f'''
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td align="center">
                    <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 15px; font-weight: 600; color: #1f2937; line-height: 1.4;">{brand_name}</p>
                    {f'<p style="margin: 4px 0 0 0; font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #6b7280;">{contact_line1}</p>' if contact_line1 else ''}
                    {f'<p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #6b7280;">{contact_line2}</p>' if contact_line2 else ''}
                    {f'<a href="{website_url}" target="_blank" style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: {primary_color}; text-decoration: none; font-weight: 500;">{website_url.replace("https://", "").replace("http://", "")}</a>' if website_url else ''}
                  </td>
                </tr>
              </table>'''
    
    email_html = f'''<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="x-apple-disable-message-reformatting">
  <title>{brand_name} - {report_type_display} (Test)</title>
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:AllowPNG/>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f4; font-family: Arial, Helvetica, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;">
  
  <!-- Wrapper Table -->
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #f4f4f4;" bgcolor="#f4f4f4">
    <tr>
      <td align="center" style="padding: 20px 10px;">
        
        <!-- Main Container -->
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" bgcolor="#ffffff">
          
          <!-- Header Section -->
          <tr>
            <td align="center" style="background-color: {primary_color}; padding: 30px 40px;" bgcolor="{primary_color}">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 20px;">
                    {logo_html}
                  </td>
                </tr>
                <tr>
                  <td align="center">
                    <h1 style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 28px; font-weight: 700; color: #ffffff; line-height: 1.3;">
                      {report_type_display}
                    </h1>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-top: 10px;">
                    <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 16px; color: rgba(255,255,255,0.9); line-height: 1.5;">
                      Beverly Hills &bull; Last 30 Days
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Test Email Notice -->
          <tr>
            <td style="padding: 25px 30px 0 30px; background-color: #ffffff;" bgcolor="#ffffff">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #fef3c7; border-radius: 8px;">
                <tr>
                  <td style="padding: 15px 20px;">
                    <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #92400e; line-height: 1.5;">
                      <strong>🧪 This is a test email</strong> — It shows how your branding appears in scheduled report emails sent to your agents' clients.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Metrics Section -->
          <tr>
            <td style="padding: 30px 30px 40px 30px; background-color: #ffffff;" bgcolor="#ffffff">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 20px;">
                    <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 14px; font-weight: 600; color: {accent_color}; text-transform: uppercase; letter-spacing: 1px;">
                      Sample Metrics
                    </p>
                  </td>
                </tr>
                <tr>
                  <td>
                    <!-- 3-Column Metrics Table -->
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                      <tr>
                        <!-- Metric 1 -->
                        <td width="32%" align="center" valign="top" style="padding: 20px 10px; background-color: #f9fafb; border-radius: 8px;" bgcolor="#f9fafb">
                          <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                              <td align="center">
                                <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 32px; font-weight: 700; color: {primary_color}; line-height: 1.2;">
                                  127
                                </p>
                              </td>
                            </tr>
                            <tr>
                              <td align="center" style="padding-top: 8px;">
                                <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 13px; color: #6b7280; line-height: 1.4;">
                                  Active Listings
                                </p>
                              </td>
                            </tr>
                          </table>
                        </td>
                        
                        <!-- Spacer -->
                        <td width="2%">&nbsp;</td>
                        
                        <!-- Metric 2 -->
                        <td width="32%" align="center" valign="top" style="padding: 20px 10px; background-color: #f9fafb; border-radius: 8px;" bgcolor="#f9fafb">
                          <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                              <td align="center">
                                <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 32px; font-weight: 700; color: {primary_color}; line-height: 1.2;">
                                  $4.2M
                                </p>
                              </td>
                            </tr>
                            <tr>
                              <td align="center" style="padding-top: 8px;">
                                <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 13px; color: #6b7280; line-height: 1.4;">
                                  Median Price
                                </p>
                              </td>
                            </tr>
                          </table>
                        </td>
                        
                        <!-- Spacer -->
                        <td width="2%">&nbsp;</td>
                        
                        <!-- Metric 3 -->
                        <td width="32%" align="center" valign="top" style="padding: 20px 10px; background-color: #f9fafb; border-radius: 8px;" bgcolor="#f9fafb">
                          <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                              <td align="center">
                                <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 32px; font-weight: 700; color: {primary_color}; line-height: 1.2;">
                                  42
                                </p>
                              </td>
                            </tr>
                            <tr>
                              <td align="center" style="padding-top: 8px;">
                                <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 13px; color: #6b7280; line-height: 1.4;">
                                  Avg. DOM
                                </p>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- CTA Section -->
          <tr>
            <td align="center" style="padding: 0 40px 40px 40px; background-color: #ffffff;" bgcolor="#ffffff">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="center" style="background-color: {accent_color}; border-radius: 8px;" bgcolor="{accent_color}">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="#" style="height:50px;v-text-anchor:middle;width:220px;" arcsize="16%" stroke="f" fillcolor="{accent_color}">
                      <w:anchorlock/>
                      <center>
                    <![endif]-->
                    <a href="#" style="display: inline-block; padding: 16px 40px; font-family: Arial, Helvetica, sans-serif; font-size: 16px; font-weight: 600; color: #ffffff; text-decoration: none; border-radius: 8px; background-color: {accent_color};">
                      View Full Report
                    </a>
                    <!--[if mso]>
                      </center>
                    </v:roundrect>
                    <![endif]-->
                  </td>
                </tr>
              </table>
              <p style="margin: 15px 0 0 0; font-family: Arial, Helvetica, sans-serif; font-size: 13px; color: #9ca3af;">
                (In real emails, this button links to the PDF report)
              </p>
            </td>
          </tr>
          
          <!-- Divider -->
          <tr>
            <td style="padding: 0 40px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td style="border-top: 1px solid #e5e7eb; height: 1px; font-size: 1px; line-height: 1px;">&nbsp;</td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Footer Section -->
          <tr>
            <td style="padding: 40px; background-color: #ffffff;" bgcolor="#ffffff">
              {footer_html}
            </td>
          </tr>
          
          <!-- Unsubscribe Footer -->
          <tr>
            <td align="center" style="padding: 20px 40px; background-color: #f9fafb;" bgcolor="#f9fafb">
              <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 12px; color: #9ca3af; line-height: 1.6;">
                This is a test email from {brand_name}.<br />
                In production, recipients can <span style="color: #6b7280; text-decoration: underline;">unsubscribe</span> from these notifications.
              </p>
            </td>
          </tr>
          
        </table>
        <!-- End Main Container -->
        
      </td>
    </tr>
  </table>
  <!-- End Wrapper Table -->
  
</body>
</html>'''
    
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

