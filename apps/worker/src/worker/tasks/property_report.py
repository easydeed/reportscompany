"""
Property Report Generation Task
================================

Celery task for generating property reports (seller/buyer).

Flow:
1. Fetch report from DB with user/branding joins
2. Build HTML with PropertyReportBuilder
3. Generate PDF with PDFShift
4. Upload to R2
5. Update report: status='complete', pdf_url=...

Usage:
    from worker.tasks.property_report import generate_property_report
    generate_property_report.delay(report_id="uuid")
"""

import os
import time
import logging
import psycopg
import boto3
from botocore.client import Config
from celery import shared_task

from ..app import celery
from ..property_builder import PropertyReportBuilder
from ..pdf_engine import render_pdf

logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/market_reports")
PDF_DIR = os.getenv("PDF_DIR", "/tmp/mr_reports")

# Cloudflare R2 Configuration
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "market-reports")
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else ""
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "")  # e.g., https://cdn.example.com

os.makedirs(PDF_DIR, exist_ok=True)


def upload_to_r2(local_path: str, s3_key: str, content_type: str = "application/pdf") -> str:
    """
    Upload file to Cloudflare R2 and return public URL.
    
    Args:
        local_path: Local file path to upload
        s3_key: S3 key (e.g., "property-reports/uuid.pdf")
        content_type: MIME type of the file
    
    Returns:
        Public URL or presigned URL
    """
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        logger.warning("R2 credentials not set, skipping upload")
        return f"http://localhost:10000/dev-files/{s3_key}"
    
    # Create R2 client (S3-compatible)
    s3_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto',
        config=Config(signature_version='s3v4')
    )
    
    logger.info(f"Uploading to R2: {s3_key}")
    with open(local_path, 'rb') as f:
        s3_client.upload_fileobj(
            f,
            R2_BUCKET_NAME,
            s3_key,
            ExtraArgs={'ContentType': content_type}
        )
    
    # Return public URL if configured, otherwise presigned URL
    if R2_PUBLIC_URL:
        public_url = f"{R2_PUBLIC_URL.rstrip('/')}/{s3_key}"
        logger.info(f"Uploaded to R2 (public): {public_url}")
        return public_url
    
    # Generate presigned URL (7 days)
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': R2_BUCKET_NAME,
            'Key': s3_key
        },
        ExpiresIn=604800  # 7 days
    )
    
    logger.info(f"Uploaded to R2 (presigned): {presigned_url[:100]}...")
    return presigned_url


def fetch_report_with_joins(report_id: str) -> dict:
    """
    Fetch property report from database with user and branding joins.
    
    Returns dict with:
    - All property_reports fields
    - agent: user info (name, email, phone, photo_url, etc.)
    - branding: affiliate_branding if applicable
    """
    with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    pr.id::text,
                    pr.account_id::text,
                    pr.user_id::text,
                    pr.report_type,
                    pr.theme,
                    pr.accent_color,
                    pr.language,
                    pr.property_address,
                    pr.property_city,
                    pr.property_state,
                    pr.property_zip,
                    pr.property_county,
                    pr.apn,
                    pr.owner_name,
                    pr.legal_description,
                    pr.property_type,
                    pr.sitex_data,
                    pr.comparables,
                    pr.short_code,
                    pr.qr_code_url,
                    
                    -- User/Agent info
                    u.name as agent_name,
                    u.email as agent_email,
                    u.phone as agent_phone,
                    u.photo_url as agent_photo_url,
                    u.title as agent_title,
                    u.license_number as agent_license,
                    
                    -- Account info
                    a.name as account_name,
                    a.account_type,
                    a.sponsor_account_id::text,
                    
                    -- Branding info (from account's own branding or sponsor's)
                    ab.brand_display_name,
                    ab.logo_url as brand_logo_url,
                    ab.primary_color as brand_primary_color,
                    ab.accent_color as brand_accent_color,
                    ab.rep_photo_url as brand_rep_photo_url,
                    ab.contact_line1 as brand_contact_line1,
                    ab.contact_line2 as brand_contact_line2,
                    ab.website_url as brand_website_url
                    
                FROM property_reports pr
                LEFT JOIN users u ON pr.user_id = u.id
                LEFT JOIN accounts a ON pr.account_id = a.id
                LEFT JOIN LATERAL (
                    -- Get branding from sponsor if regular user, or own branding if affiliate
                    SELECT *
                    FROM affiliate_branding
                    WHERE account_id = COALESCE(
                        CASE WHEN a.account_type = 'REGULAR' THEN a.sponsor_account_id ELSE NULL END,
                        CASE WHEN a.account_type = 'INDUSTRY_AFFILIATE' THEN a.id ELSE NULL END
                    )
                    LIMIT 1
                ) ab ON true
                WHERE pr.id = %s::uuid
            """, (report_id,))
            
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Property report not found: {report_id}")
            
            # Map to dictionary
            columns = [
                'id', 'account_id', 'user_id', 'report_type', 'theme',
                'accent_color', 'language', 'property_address', 'property_city',
                'property_state', 'property_zip', 'property_county', 'apn',
                'owner_name', 'legal_description', 'property_type', 'sitex_data',
                'comparables', 'short_code', 'qr_code_url',
                'agent_name', 'agent_email', 'agent_phone', 'agent_photo_url',
                'agent_title', 'agent_license',
                'account_name', 'account_type', 'sponsor_account_id',
                'brand_display_name', 'brand_logo_url', 'brand_primary_color',
                'brand_accent_color', 'brand_rep_photo_url', 'brand_contact_line1',
                'brand_contact_line2', 'brand_website_url'
            ]
            
            data = dict(zip(columns, row))
            
            # Structure the result
            result = {
                # Report fields
                'id': data['id'],
                'account_id': data['account_id'],
                'user_id': data['user_id'],
                'report_type': data['report_type'],
                'theme': data['theme'],
                'accent_color': data['accent_color'],
                'language': data['language'],
                'property_address': data['property_address'],
                'property_city': data['property_city'],
                'property_state': data['property_state'],
                'property_zip': data['property_zip'],
                'property_county': data['property_county'],
                'apn': data['apn'],
                'owner_name': data['owner_name'],
                'legal_description': data['legal_description'],
                'property_type': data['property_type'],
                'sitex_data': data['sitex_data'],
                'comparables': data['comparables'],
                'short_code': data['short_code'],
                'qr_code_url': data['qr_code_url'],
                
                # Agent info
                'agent': {
                    'name': data['agent_name'] or data['account_name'] or 'Agent',
                    'email': data['agent_email'] or '',
                    'phone': data['agent_phone'] or '',
                    'photo_url': data['agent_photo_url'] or data['brand_rep_photo_url'],
                    'title': data['agent_title'] or 'Real Estate Professional',
                    'license_number': data['agent_license'],
                    'company_name': data['brand_display_name'] or data['account_name'],
                    'logo_url': data['brand_logo_url'],
                },
                
                # Branding
                'branding': {
                    'display_name': data['brand_display_name'],
                    'logo_url': data['brand_logo_url'],
                    'primary_color': data['brand_primary_color'],
                    'accent_color': data['brand_accent_color'],
                    'contact_line1': data['brand_contact_line1'],
                    'contact_line2': data['brand_contact_line2'],
                    'website_url': data['brand_website_url'],
                } if data['brand_display_name'] else None
            }
            
            return result


def update_report_status(report_id: str, status: str, pdf_url: str = None, error: str = None):
    """Update property report status in database."""
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            if error:
                cur.execute("""
                    UPDATE property_reports
                    SET status = %s, updated_at = NOW()
                    WHERE id = %s::uuid
                """, (status, report_id))
                logger.error(f"Report {report_id} failed: {error}")
            elif pdf_url:
                cur.execute("""
                    UPDATE property_reports
                    SET status = %s, pdf_url = %s, updated_at = NOW()
                    WHERE id = %s::uuid
                """, (status, pdf_url, report_id))
            else:
                cur.execute("""
                    UPDATE property_reports
                    SET status = %s, updated_at = NOW()
                    WHERE id = %s::uuid
                """, (status, report_id))


def update_report_comparables(report_id: str, comparables: list):
    """Save fetched comparables back to the database."""
    import json
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE property_reports
                SET comparables = %s::jsonb, updated_at = NOW()
                WHERE id = %s::uuid
            """, (json.dumps(comparables), report_id))


@celery.task(
    name="generate_property_report",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,  # Max 5 minutes between retries
    retry_kwargs={"max_retries": 3},
)
def generate_property_report(self, report_id: str):
    """
    Generate a property report PDF.
    
    Steps:
    1. Fetch report data from DB with user/branding joins
    2. Build HTML using PropertyReportBuilder
    3. Generate PDF using PDFShift
    4. Upload PDF to R2
    5. Update report status and pdf_url
    
    Args:
        report_id: UUID of the property_reports record
        
    Returns:
        dict with success status and pdf_url
    """
    started = time.perf_counter()
    logger.info(f"Starting property report generation: {report_id}")
    
    try:
        # 1. Update status to processing
        update_report_status(report_id, 'processing')
        
        # 2. Fetch report data with joins
        logger.info(f"Fetching report data: {report_id}")
        report_data = fetch_report_with_joins(report_id)
        account_id = report_data['account_id']
        
        # 3. Build HTML with PropertyReportBuilder
        logger.info(f"Building HTML for report: {report_id}")
        builder = PropertyReportBuilder(report_data)
        
        # Fetch comparables if not already set
        comparables = builder.fetch_comparables()
        if comparables and not report_data.get('comparables'):
            # Save comparables back to DB for future use
            update_report_comparables(report_id, comparables)
        
        # Render the full HTML
        html_content = builder.render_html()
        logger.info(f"Generated HTML: {len(html_content)} chars")
        
        # 4. Generate PDF with PDFShift
        logger.info(f"Generating PDF for report: {report_id}")
        pdf_path, _ = render_pdf(
            run_id=report_id,
            account_id=account_id,
            html_content=html_content
        )
        logger.info(f"PDF generated: {pdf_path}")
        
        # 5. Upload to R2
        # Create descriptive filename
        address_safe = (
            report_data.get('property_address', 'Property')
            .replace(' ', '_')
            .replace(',', '')
            .replace('.', '')
            [:50]
        )
        report_type = report_data.get('report_type', 'report').title()
        pdf_filename = f"{address_safe}_{report_type}_Report.pdf"
        s3_key = f"property-reports/{account_id}/{report_id}/{pdf_filename}"
        
        logger.info(f"Uploading PDF to R2: {s3_key}")
        pdf_url = upload_to_r2(pdf_path, s3_key)
        
        # 6. Update report with success status and PDF URL
        update_report_status(report_id, 'complete', pdf_url=pdf_url)
        
        elapsed = time.perf_counter() - started
        logger.info(f"Property report complete: {report_id} ({elapsed:.2f}s)")
        
        return {
            "success": True,
            "report_id": report_id,
            "pdf_url": pdf_url,
            "elapsed_seconds": round(elapsed, 2)
        }
        
    except Exception as e:
        elapsed = time.perf_counter() - started
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.exception(f"Property report failed: {report_id}")
        
        # Update status to failed
        update_report_status(report_id, 'failed', error=error_msg)
        
        # Re-raise to trigger Celery retry
        raise

