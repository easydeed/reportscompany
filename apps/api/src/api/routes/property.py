"""
Property Reports API

Endpoints for property data lookup, comparables, and property report management.
Integrates with SiteX Pro for property data and SimplyRETS for comparable sales.
"""

import json
import logging
import random
import string
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..db import db_conn, fetchall_dicts, fetchone_dict, set_rls
from ..services.sitex import (
    PropertyData,
    SiteXError,
    SiteXMultiMatchError,
    SiteXNotFoundError,
    lookup_property,
    lookup_property_by_apn,
)
from ..worker_client import enqueue_generate_report
from ..services.qr_service import generate_qr_code

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/property", tags=["property"])


# =============================================================================
# SCHEMAS
# =============================================================================


class AddressSearchRequest(BaseModel):
    """Property search by address"""
    address: str = Field(..., min_length=5, description="Full or partial address")
    city_state_zip: Optional[str] = Field(
        default="",
        description="City, State ZIP (optional if included in address)"
    )


class APNSearchRequest(BaseModel):
    """Property search by FIPS and APN"""
    fips: str = Field(..., min_length=5, max_length=5, description="5-digit FIPS county code")
    apn: str = Field(..., min_length=3, description="Assessor's Parcel Number")


class PropertySearchResponse(BaseModel):
    """Response for property search"""
    success: bool
    data: Optional[PropertyData] = None
    error: Optional[str] = None
    multiple_matches: Optional[List[dict]] = None


class ComparableProperty(BaseModel):
    """Comparable property from MLS"""
    mls_id: str
    address: str
    city: str
    state: str
    zip_code: str
    list_price: Optional[int] = None
    close_price: Optional[int] = None
    status: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[int] = None
    year_built: Optional[int] = None
    dom: Optional[int] = None
    close_date: Optional[str] = None
    distance_miles: Optional[float] = None
    photo_url: Optional[str] = None


class ComparablesRequest(BaseModel):
    """Request for comparable properties"""
    address: str
    city_state_zip: Optional[str] = ""
    radius_miles: float = Field(default=1.0, ge=0.1, le=10.0)
    status: Literal["Closed", "Active", "All"] = "Closed"
    limit: int = Field(default=10, ge=1, le=50)


class ComparablesResponse(BaseModel):
    """Response with comparable properties"""
    success: bool
    subject_property: Optional[PropertyData] = None
    comparables: List[ComparableProperty] = []
    error: Optional[str] = None


class PropertyReportCreate(BaseModel):
    """Create a new property report"""
    report_type: Literal["seller", "buyer"] = "seller"
    address: str = Field(..., min_length=5)
    city_state_zip: Optional[str] = ""
    theme: int = Field(default=1, ge=1, le=5)
    accent_color: str = Field(default="#2563eb", pattern=r"^#[0-9a-fA-F]{6}$")
    language: Literal["en", "es"] = "en"


class PropertyReportResponse(BaseModel):
    """Property report response"""
    id: str
    status: str
    short_code: str
    qr_code_url: Optional[str] = None
    property_address: str
    report_type: str
    created_at: str


class PropertyReportDetail(BaseModel):
    """Full property report details"""
    id: str
    account_id: str
    user_id: Optional[str] = None
    report_type: str
    theme: int
    accent_color: str
    language: str
    property_address: str
    property_city: str
    property_state: str
    property_zip: str
    property_county: Optional[str] = None
    apn: Optional[str] = None
    owner_name: Optional[str] = None
    legal_description: Optional[str] = None
    property_type: Optional[str] = None
    sitex_data: Optional[dict] = None
    comparables: Optional[List[dict]] = None
    pdf_url: Optional[str] = None
    status: str
    short_code: str
    qr_code_url: Optional[str] = None
    view_count: int
    created_at: str
    updated_at: str


# =============================================================================
# HELPERS
# =============================================================================


def require_account_id(request: Request) -> str:
    """Extract and validate account_id from request state."""
    account_id = getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return account_id


def require_user_id(request: Request) -> str:
    """Extract user_id from request state."""
    user_id = getattr(request.state, "user_id", None)
    return user_id


async def generate_qr_code_for_report(
    short_code: str,
    report_id: str,
    accent_color: str = "#2563eb",
    base_url: str = "https://trendyreports.io"
) -> str:
    """
    Generate QR code for a property report and upload to R2.
    The QR code will point to: {base_url}/p/{short_code}
    """
    target_url = f"{base_url}/p/{short_code}"
    return await generate_qr_code(
        url=target_url,
        color=accent_color,
        report_id=report_id
    )


def check_property_report_limits(cur, account_id: str) -> tuple[bool, str]:
    """
    Check if account can create a new property report.
    Returns (allowed: bool, message: str)
    """
    # Get account's plan and limits
    cur.execute("""
        SELECT 
            a.plan_slug,
            p.property_reports_per_month,
            (
                SELECT COUNT(*) FROM property_reports pr
                WHERE pr.account_id = a.id
                AND pr.created_at >= date_trunc('month', CURRENT_DATE)
            ) as reports_this_month
        FROM accounts a
        LEFT JOIN plans p ON a.plan_slug = p.plan_slug
        WHERE a.id = %s::uuid
    """, (account_id,))
    
    row = cur.fetchone()
    if not row:
        return False, "Account not found"
    
    plan_slug, limit, count = row
    
    # If no limit set, allow unlimited
    if limit is None:
        return True, "OK"
    
    if count >= limit:
        return False, f"Property report limit reached ({count}/{limit} this month)"
    
    return True, f"OK ({count + 1}/{limit})"


# =============================================================================
# PROPERTY SEARCH ENDPOINTS
# =============================================================================


@router.post("/search", response_model=PropertySearchResponse)
async def search_property(payload: AddressSearchRequest, request: Request):
    """
    Search for property by address.
    
    Returns property data including APN, owner, characteristics, and tax info.
    """
    # Auth required
    require_account_id(request)
    
    try:
        result = await lookup_property(payload.address, payload.city_state_zip)
        
        if result:
            return PropertySearchResponse(success=True, data=result)
        else:
            return PropertySearchResponse(
                success=False,
                error="Property not found. Please verify the address."
            )
            
    except SiteXMultiMatchError as e:
        # Return the multiple matches so UI can offer selection
        return PropertySearchResponse(
            success=False,
            error=str(e),
            multiple_matches=[loc.model_dump() for loc in e.locations]
        )
    except SiteXError as e:
        logger.error(f"SiteX error in property search: {e}")
        return PropertySearchResponse(
            success=False,
            error="Property lookup service unavailable. Please try again."
        )


@router.post("/search-by-apn", response_model=PropertySearchResponse)
async def search_by_apn(payload: APNSearchRequest, request: Request):
    """
    Search for property by FIPS code and APN.
    This is the most precise search method.
    """
    # Auth required
    require_account_id(request)
    
    try:
        result = await lookup_property_by_apn(payload.fips, payload.apn)
        
        if result:
            return PropertySearchResponse(success=True, data=result)
        else:
            return PropertySearchResponse(
                success=False,
                error="Property not found for given FIPS/APN."
            )
    except SiteXError as e:
        logger.error(f"SiteX APN lookup error: {e}")
        return PropertySearchResponse(
            success=False,
            error="Property lookup service unavailable."
        )


@router.post("/comparables", response_model=ComparablesResponse)
async def get_comparables(payload: ComparablesRequest, request: Request):
    """
    Get comparable properties for a given address.
    
    1. Looks up subject property via SiteX
    2. Searches SimplyRETS for nearby comparable sales
    """
    # Auth required
    require_account_id(request)
    
    # Step 1: Get subject property
    try:
        subject = await lookup_property(payload.address, payload.city_state_zip)
        if not subject:
            return ComparablesResponse(
                success=False,
                error="Subject property not found. Please verify the address."
            )
    except SiteXError as e:
        return ComparablesResponse(
            success=False,
            error=f"Property lookup failed: {e}"
        )
    
    # Step 2: Search SimplyRETS for comparables
    # Import here to avoid circular imports and keep worker dependency optional
    try:
        import sys
        import os
        
        # Add worker path for SimplyRETS vendor
        worker_path = os.path.join(os.path.dirname(__file__), '../../../../worker/src')
        if worker_path not in sys.path:
            sys.path.insert(0, worker_path)
        
        from worker.vendors.simplyrets import fetch_properties
        
        # Build search params based on subject property
        params = {
            "q": subject.city or payload.address.split(",")[0],
            "status": "Closed" if payload.status == "Closed" else "Active,Closed",
            "type": "RES",
            "limit": payload.limit * 2,  # Fetch extra to filter
        }
        
        # Add property type filter if available
        if subject.property_type:
            if "condo" in subject.property_type.lower():
                params["subtype"] = "Condominium"
            else:
                params["subtype"] = "SingleFamilyResidence"
        
        # Add price range (+/- 30% of subject if we have assessed value)
        if subject.assessed_value:
            est_value = subject.assessed_value * 1.2  # Rough market estimate
            params["minprice"] = int(est_value * 0.7)
            params["maxprice"] = int(est_value * 1.3)
        
        # Add bed/bath filters
        if subject.bedrooms:
            params["minbeds"] = max(1, subject.bedrooms - 1)
            params["maxbeds"] = subject.bedrooms + 1
        
        # Fetch from SimplyRETS
        listings = fetch_properties(params, limit=payload.limit * 2)
        
        # Convert to ComparableProperty objects
        comparables = []
        for listing in listings[:payload.limit]:
            prop = listing.get("property", {})
            address_obj = listing.get("address", {})
            
            comp = ComparableProperty(
                mls_id=listing.get("mlsId", ""),
                address=address_obj.get("full", ""),
                city=address_obj.get("city", ""),
                state=address_obj.get("state", ""),
                zip_code=address_obj.get("postalCode", ""),
                list_price=listing.get("listPrice"),
                close_price=listing.get("closePrice"),
                status=listing.get("mls", {}).get("status", ""),
                bedrooms=prop.get("bedrooms"),
                bathrooms=prop.get("bathsFull"),
                sqft=prop.get("area"),
                lot_size=prop.get("lotSize"),
                year_built=prop.get("yearBuilt"),
                dom=listing.get("mls", {}).get("daysOnMarket"),
                close_date=listing.get("closeDate"),
                photo_url=listing.get("photos", [None])[0] if listing.get("photos") else None,
            )
            comparables.append(comp)
        
        return ComparablesResponse(
            success=True,
            subject_property=subject,
            comparables=comparables
        )
        
    except ImportError:
        logger.warning("SimplyRETS vendor not available")
        return ComparablesResponse(
            success=True,
            subject_property=subject,
            comparables=[],
            error="Comparable search unavailable"
        )
    except Exception as e:
        logger.error(f"Comparables search error: {e}")
        return ComparablesResponse(
            success=True,
            subject_property=subject,
            comparables=[],
            error=f"Comparable search failed: {str(e)}"
        )


# =============================================================================
# PROPERTY REPORT ENDPOINTS
# =============================================================================


@router.post("/reports", response_model=PropertyReportResponse)
async def create_property_report(payload: PropertyReportCreate, request: Request):
    """
    Create a new property report.
    
    1. Check plan limits
    2. Lookup property via SiteX
    3. Generate short_code and QR code
    4. Queue PDF generation
    """
    account_id = require_account_id(request)
    user_id = require_user_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        # 1. Check plan limits
        allowed, message = check_property_report_limits(cur, account_id)
        if not allowed:
            raise HTTPException(status_code=429, detail=message)
        
        # 2. Lookup property via SiteX
        try:
            property_data = await lookup_property(payload.address, payload.city_state_zip)
        except SiteXError as e:
            logger.error(f"SiteX lookup failed: {e}")
            property_data = None
        
        # Extract address components (from SiteX or parse from input)
        if property_data:
            prop_address = property_data.street or payload.address.split(",")[0].strip()
            prop_city = property_data.city or ""
            prop_state = property_data.state or "CA"
            prop_zip = property_data.zip_code or ""
            prop_county = property_data.county
            apn = property_data.apn
            owner_name = property_data.owner_name
            legal_desc = property_data.legal_description
            prop_type = property_data.property_type
            sitex_data = property_data.model_dump() if property_data else None
        else:
            # Parse from input
            parts = payload.address.split(",")
            prop_address = parts[0].strip() if parts else payload.address
            
            csz_parts = (payload.city_state_zip or "").split(",")
            prop_city = csz_parts[0].strip() if csz_parts else ""
            
            state_zip = csz_parts[1].strip().split() if len(csz_parts) > 1 else []
            prop_state = state_zip[0] if state_zip else "CA"
            prop_zip = state_zip[1] if len(state_zip) > 1 else ""
            
            prop_county = None
            apn = None
            owner_name = None
            legal_desc = None
            prop_type = None
            sitex_data = None
        
        # 3. Create report record (short_code auto-generated by trigger)
        cur.execute("""
            INSERT INTO property_reports (
                account_id,
                user_id,
                report_type,
                theme,
                accent_color,
                language,
                property_address,
                property_city,
                property_state,
                property_zip,
                property_county,
                apn,
                owner_name,
                legal_description,
                property_type,
                sitex_data,
                status
            )
            VALUES (
                %s::uuid, %s::uuid, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s::jsonb, 'draft'
            )
            RETURNING 
                id::text,
                short_code,
                status,
                created_at::text
        """, (
            account_id,
            user_id,
            payload.report_type,
            payload.theme,
            payload.accent_color,
            payload.language,
            prop_address,
            prop_city,
            prop_state,
            prop_zip,
            prop_county,
            apn,
            owner_name,
            legal_desc,
            prop_type,
            json.dumps(sitex_data) if sitex_data else None,
        ))
        
        row = cur.fetchone()
        report_id, short_code, status, created_at = row
        
        # 4. Generate QR code and upload to R2
        qr_code_url = await generate_qr_code_for_report(
            short_code=short_code,
            report_id=report_id,
            accent_color=payload.accent_color
        )
        
        # Update with QR code URL
        cur.execute("""
            UPDATE property_reports
            SET qr_code_url = %s, status = 'processing'
            WHERE id = %s::uuid
        """, (qr_code_url, report_id))
        
        conn.commit()
        
        # 5. Queue PDF generation
        try:
            enqueue_generate_report(
                run_id=report_id,
                account_id=account_id,
                report_type=f"property_{payload.report_type}",
                params={
                    "property_address": prop_address,
                    "property_city": prop_city,
                    "property_state": prop_state,
                    "property_zip": prop_zip,
                    "theme": payload.theme,
                    "accent_color": payload.accent_color,
                    "language": payload.language,
                }
            )
        except Exception as e:
            logger.error(f"Failed to enqueue property report: {e}")
            # Update status to failed
            cur.execute("""
                UPDATE property_reports
                SET status = 'failed'
                WHERE id = %s::uuid
            """, (report_id,))
            conn.commit()
        
        full_address = f"{prop_address}, {prop_city}, {prop_state} {prop_zip}".strip(", ")
        
        return PropertyReportResponse(
            id=report_id,
            status="processing",
            short_code=short_code,
            qr_code_url=qr_code_url,
            property_address=full_address,
            report_type=payload.report_type,
            created_at=created_at,
        )


@router.get("/reports")
def list_property_reports(
    request: Request,
    status: Optional[Literal["draft", "processing", "complete", "failed"]] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List property reports for current account.
    """
    account_id = require_account_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        # Build query
        where_clauses = ["account_id = %s::uuid"]
        params = [account_id]
        
        if status:
            where_clauses.append("status = %s")
            params.append(status)
        
        where_sql = " AND ".join(where_clauses)
        
        # Get total count
        cur.execute(f"SELECT COUNT(*) FROM property_reports WHERE {where_sql}", params)
        total = cur.fetchone()[0]
        
        # Get reports
        params.extend([limit, offset])
        cur.execute(f"""
            SELECT 
                id::text,
                report_type,
                property_address,
                property_city,
                property_state,
                property_zip,
                status,
                short_code,
                qr_code_url,
                pdf_url,
                view_count,
                created_at::text,
                updated_at::text
            FROM property_reports
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params)
        
        reports = []
        for row in cur.fetchall():
            full_address = f"{row[2]}, {row[3]}, {row[4]} {row[5]}".strip(", ")
            reports.append({
                "id": row[0],
                "report_type": row[1],
                "property_address": full_address,
                "status": row[6],
                "short_code": row[7],
                "qr_code_url": row[8],
                "pdf_url": row[9],
                "view_count": row[10],
                "created_at": row[11],
                "updated_at": row[12],
            })
    
    return {
        "reports": reports,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/reports/{report_id}", response_model=PropertyReportDetail)
def get_property_report(report_id: str, request: Request):
    """
    Get full details of a property report.
    """
    account_id = require_account_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        cur.execute("""
            SELECT 
                id::text,
                account_id::text,
                user_id::text,
                report_type,
                theme,
                accent_color,
                language,
                property_address,
                property_city,
                property_state,
                property_zip,
                property_county,
                apn,
                owner_name,
                legal_description,
                property_type,
                sitex_data,
                comparables,
                pdf_url,
                status,
                short_code,
                qr_code_url,
                view_count,
                created_at::text,
                updated_at::text
            FROM property_reports
            WHERE id = %s::uuid AND account_id = %s::uuid
        """, (report_id, account_id))
        
        row = cur.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Property report not found")
    
    return PropertyReportDetail(
        id=row[0],
        account_id=row[1],
        user_id=row[2],
        report_type=row[3],
        theme=row[4],
        accent_color=row[5],
        language=row[6],
        property_address=row[7],
        property_city=row[8],
        property_state=row[9],
        property_zip=row[10],
        property_county=row[11],
        apn=row[12],
        owner_name=row[13],
        legal_description=row[14],
        property_type=row[15],
        sitex_data=row[16],
        comparables=row[17],
        pdf_url=row[18],
        status=row[19],
        short_code=row[20],
        qr_code_url=row[21],
        view_count=row[22],
        created_at=row[23],
        updated_at=row[24],
    )


@router.delete("/reports/{report_id}")
def delete_property_report(report_id: str, request: Request):
    """
    Delete a property report.
    """
    account_id = require_account_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        cur.execute("""
            DELETE FROM property_reports
            WHERE id = %s::uuid AND account_id = %s::uuid
            RETURNING id
        """, (report_id, account_id))
        
        deleted = cur.fetchone()
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Property report not found")
    
    return {"ok": True, "deleted_id": report_id}


# =============================================================================
# LANDING PAGE SETTINGS ENDPOINTS
# =============================================================================


class LandingPageSettings(BaseModel):
    """Landing page settings response"""
    id: str
    property_address: str
    short_code: str
    qr_code_url: Optional[str] = None
    is_active: bool
    expires_at: Optional[str] = None
    max_leads: Optional[int] = None
    access_code: Optional[str] = None
    view_count: int
    unique_visitors: int
    last_viewed_at: Optional[str] = None


class LandingPageSettingsUpdate(BaseModel):
    """Update landing page settings"""
    is_active: Optional[bool] = None
    expires_at: Optional[str] = None
    max_leads: Optional[int] = None
    access_code: Optional[str] = None


@router.get("/reports/{report_id}/settings", response_model=LandingPageSettings)
def get_landing_page_settings(report_id: str, request: Request):
    """
    Get landing page settings for a property report.
    """
    account_id = require_account_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        cur.execute("""
            SELECT 
                id::text,
                CONCAT(property_address, ', ', property_city, ', ', property_state, ' ', property_zip) as property_address,
                short_code,
                qr_code_url,
                is_active,
                expires_at::text,
                max_leads,
                access_code,
                view_count,
                unique_visitors,
                last_viewed_at::text
            FROM property_reports
            WHERE id = %s::uuid AND account_id = %s::uuid
        """, (report_id, account_id))
        
        row = cur.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Property report not found")
    
    return LandingPageSettings(
        id=row[0],
        property_address=row[1],
        short_code=row[2],
        qr_code_url=row[3],
        is_active=row[4],
        expires_at=row[5],
        max_leads=row[6],
        access_code=row[7],
        view_count=row[8],
        unique_visitors=row[9],
        last_viewed_at=row[10],
    )


@router.patch("/reports/{report_id}/settings", response_model=LandingPageSettings)
def update_landing_page_settings(
    report_id: str,
    updates: LandingPageSettingsUpdate,
    request: Request
):
    """
    Update landing page settings for a property report.
    """
    account_id = require_account_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        # Build dynamic UPDATE
        fields = []
        values = []
        
        if updates.is_active is not None:
            fields.append("is_active = %s")
            values.append(updates.is_active)
        
        if updates.expires_at is not None:
            if updates.expires_at:
                fields.append("expires_at = %s::timestamptz")
                values.append(updates.expires_at)
            else:
                fields.append("expires_at = NULL")
        
        if updates.max_leads is not None:
            if updates.max_leads > 0:
                fields.append("max_leads = %s")
                values.append(updates.max_leads)
            else:
                fields.append("max_leads = NULL")
        
        if updates.access_code is not None:
            if updates.access_code:
                fields.append("access_code = %s")
                values.append(updates.access_code)
            else:
                fields.append("access_code = NULL")
        
        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        fields.append("updated_at = NOW()")
        values.extend([report_id, account_id])
        
        cur.execute(f"""
            UPDATE property_reports
            SET {', '.join(fields)}
            WHERE id = %s::uuid AND account_id = %s::uuid
            RETURNING 
                id::text,
                CONCAT(property_address, ', ', property_city, ', ', property_state, ' ', property_zip) as property_address,
                short_code,
                qr_code_url,
                is_active,
                expires_at::text,
                max_leads,
                access_code,
                view_count,
                unique_visitors,
                last_viewed_at::text
        """, values)
        
        row = cur.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Property report not found")
    
    logger.info(f"Updated landing page settings for report {report_id}")
    
    return LandingPageSettings(
        id=row[0],
        property_address=row[1],
        short_code=row[2],
        qr_code_url=row[3],
        is_active=row[4],
        expires_at=row[5],
        max_leads=row[6],
        access_code=row[7],
        view_count=row[8],
        unique_visitors=row[9],
        last_viewed_at=row[10],
    )


@router.post("/reports/{report_id}/regenerate-qr")
async def regenerate_qr_code(report_id: str, request: Request):
    """
    Regenerate the QR code and short code for a property report.
    
    WARNING: This will invalidate the existing QR code and short link.
    """
    account_id = require_account_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        # First verify report exists and get current data
        cur.execute("""
            SELECT 
                id::text,
                accent_color
            FROM property_reports
            WHERE id = %s::uuid AND account_id = %s::uuid
        """, (report_id, account_id))
        
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Property report not found")
        
        report_id_str, accent_color = row
        
        # Generate new short code (excludes confusing chars: i, l, o, 0, 1)
        chars = 'abcdefghjkmnpqrstuvwxyz23456789'
        
        # Try to generate a unique code
        max_attempts = 10
        new_short_code = None
        
        for _ in range(max_attempts):
            candidate = ''.join(random.choice(chars) for _ in range(8))
            cur.execute(
                "SELECT 1 FROM property_reports WHERE short_code = %s",
                (candidate,)
            )
            if not cur.fetchone():
                new_short_code = candidate
                break
        
        if not new_short_code:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate unique short code"
            )
        
        # Generate new QR code
        new_qr_url = await generate_qr_code_for_report(
            short_code=new_short_code,
            report_id=report_id_str,
            accent_color=accent_color or "#2563eb"
        )
        
        # Update the report
        cur.execute("""
            UPDATE property_reports
            SET short_code = %s,
                qr_code_url = %s,
                updated_at = NOW()
            WHERE id = %s::uuid AND account_id = %s::uuid
            RETURNING short_code, qr_code_url
        """, (new_short_code, new_qr_url, report_id, account_id))
        
        updated = cur.fetchone()
        conn.commit()
    
    logger.info(f"Regenerated QR code for report {report_id}: {new_short_code}")
    
    return {
        "ok": True,
        "short_code": updated[0],
        "qr_code_url": updated[1],
    }


# =============================================================================
# PUBLIC ENDPOINT - No Auth Required
# =============================================================================


class PublicPropertyReportResponse(BaseModel):
    """Public property report data for landing page"""
    # Property info
    property_address: str
    property_city: str
    property_state: str
    property_zip: str
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    year_built: Optional[int] = None
    
    # Report metadata
    report_type: str
    theme: int
    accent_color: str
    short_code: str
    
    # Agent/branding info
    agent_name: Optional[str] = None
    agent_photo_url: Optional[str] = None
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    agent_phone: Optional[str] = None
    agent_email: Optional[str] = None
    website_url: Optional[str] = None
    
    # Landing page controls
    is_active: bool = True
    expires_at: Optional[str] = None
    requires_access_code: bool = False


@router.get("/public/{short_code}", response_model=PublicPropertyReportResponse)
def get_public_property_report(short_code: str):
    """
    PUBLIC endpoint - Get property report info for QR code landing page.
    
    No authentication required.
    Checks landing page controls (is_active, expires_at, max_leads).
    Increments view_count on each request.
    """
    from datetime import timezone
    
    with db_conn() as (conn, cur):
        # No RLS - public endpoint
        # First, check the report's landing page status
        cur.execute("""
            SELECT
                id::text,
                account_id::text,
                user_id::text,
                report_type,
                theme,
                accent_color,
                property_address,
                property_city,
                property_state,
                property_zip,
                property_type,
                sitex_data,
                short_code,
                is_active,
                expires_at,
                max_leads,
                access_code,
                (SELECT COUNT(*) FROM leads WHERE property_report_id = property_reports.id) as lead_count
            FROM property_reports
            WHERE short_code = %s
        """, (short_code,))
        
        report_row = cur.fetchone()
        
        if not report_row:
            raise HTTPException(status_code=404, detail="Property report not found")
        
        (
            report_id,
            account_id,
            user_id,
            report_type,
            theme,
            accent_color,
            prop_address,
            prop_city,
            prop_state,
            prop_zip,
            prop_type,
            sitex_data,
            short_code_val,
            is_active,
            expires_at,
            max_leads,
            access_code,
            lead_count,
        ) = report_row
        
        # Check landing page controls
        if not is_active:
            raise HTTPException(status_code=410, detail="This page is no longer available")
        
        if expires_at and expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="This page has expired")
        
        if max_leads and lead_count >= max_leads:
            raise HTTPException(status_code=410, detail="This page is no longer accepting submissions")
        
        # Increment view count (after checks pass)
        cur.execute("""
            UPDATE property_reports
            SET view_count = view_count + 1,
                last_viewed_at = NOW()
            WHERE id = %s::uuid
        """, (report_id,))
        
        # Extract property details from sitex_data if available
        bedrooms = None
        bathrooms = None
        sqft = None
        year_built = None
        
        if sitex_data:
            bedrooms = sitex_data.get("bedrooms")
            bathrooms = sitex_data.get("bathrooms")
            sqft = sitex_data.get("sqft")
            year_built = sitex_data.get("year_built")
        
        # Get agent and branding info
        agent_name = None
        agent_photo_url = None
        agent_phone = None
        agent_email = None
        company_name = None
        company_logo_url = None
        website_url = None
        
        # First try to get from user
        if user_id:
            cur.execute("""
                SELECT 
                    first_name,
                    last_name,
                    avatar_url,
                    phone,
                    email
                FROM users
                WHERE id = %s::uuid
            """, (user_id,))
            
            user_row = cur.fetchone()
            if user_row:
                first_name = user_row[0] or ""
                last_name = user_row[1] or ""
                agent_name = f"{first_name} {last_name}".strip()
                agent_photo_url = user_row[2]
                agent_phone = user_row[3]
                agent_email = user_row[4]
        
        # Get account branding
        cur.execute("""
            SELECT 
                a.name,
                a.logo_url,
                a.rep_photo_url,
                a.contact_line1,
                a.contact_line2,
                a.website_url,
                ab.brand_display_name,
                ab.logo_url as affiliate_logo,
                ab.rep_photo_url as affiliate_photo
            FROM accounts a
            LEFT JOIN affiliate_branding ab ON a.id = ab.account_id
            WHERE a.id = %s::uuid
        """, (account_id,))
        
        branding_row = cur.fetchone()
        if branding_row:
            company_name = branding_row[6] or branding_row[0]  # Prefer affiliate branding
            company_logo_url = branding_row[7] or branding_row[1]
            
            # Use agent photo from branding if not already set
            if not agent_photo_url:
                agent_photo_url = branding_row[8] or branding_row[2]
            
            # Parse contact info if agent name not already set
            if not agent_name and branding_row[3]:
                agent_name = branding_row[3].split("•")[0].strip() if "•" in branding_row[3] else branding_row[3]
            
            website_url = branding_row[5]
        
        conn.commit()
    
    return PublicPropertyReportResponse(
        property_address=prop_address,
        property_city=prop_city,
        property_state=prop_state,
        property_zip=prop_zip,
        property_type=prop_type,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        sqft=sqft,
        year_built=year_built,
        report_type=report_type,
        theme=theme,
        accent_color=accent_color,
        short_code=short_code_val,
        agent_name=agent_name,
        agent_photo_url=agent_photo_url,
        company_name=company_name,
        company_logo_url=company_logo_url,
        agent_phone=agent_phone,
        agent_email=agent_email,
        website_url=website_url,
        is_active=is_active,
        expires_at=expires_at.isoformat() if expires_at else None,
        requires_access_code=bool(access_code),
    )
