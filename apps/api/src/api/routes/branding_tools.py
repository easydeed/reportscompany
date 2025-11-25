"""
Branding tools routes - Sample PDF generation and test email.

Pass B4: Download & Test Send
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import io
import os
import httpx

from .reports import require_account_id
from ..db import db_conn
from ..services.affiliates import verify_affiliate_account

router = APIRouter(prefix="/v1/branding", tags=["branding-tools"])

# PDFShift configuration
PDFSHIFT_API_KEY = os.getenv("PDF_API_KEY", "")
PDFSHIFT_URL = "https://api.pdfshift.io/v3/convert/pdf"
PRINT_BASE = os.getenv("PRINT_BASE", "https://www.trendyreports.io")


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
    preview_url = f"{PRINT_BASE}/branding-preview/{report_type}"
    preview_url += f"?brand_name={branding['brand_display_name']}"
    if branding.get("logo_url"):
        preview_url += f"&logo_url={branding['logo_url']}"
    if branding.get("primary_color"):
        preview_url += f"&primary_color={branding['primary_color'].replace('#', '')}"
    if branding.get("accent_color"):
        preview_url += f"&accent_color={branding['accent_color'].replace('#', '')}"
    
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
    # For now, return a placeholder response
    # Full implementation would use SendGrid to send a branded email
    
    return {
        "ok": True,
        "message": f"Test email feature coming soon. Would send to: {body.email}",
        "report_type": body.report_type,
    }

