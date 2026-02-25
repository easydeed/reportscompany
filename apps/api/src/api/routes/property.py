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
from math import radians, cos, sin, asin, sqrt
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points in miles.
    Uses the Haversine formula.
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    miles = 3956 * c  # Earth radius in miles
    return miles

from ..db import db_conn, fetchall_dicts, fetchone_dict, set_rls
from ..services.sitex import (
    PropertyData,
    SiteXError,
    SiteXMultiMatchError,
    SiteXNotFoundError,
    lookup_property,
    lookup_property_by_apn,
)
from ..services.simplyrets import (
    fetch_properties as simplyrets_fetch_properties,
    build_comparables_params,
    normalize_listing,
)
from ..worker_client import enqueue_property_report
from ..services.qr_service import generate_qr_code
from ..services.property_stats import get_agent_stats, get_affiliate_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/property", tags=["property"])


# =============================================================================
# PROPERTY TYPE MAPPING (SiteX UseCode -> SimplyRETS type + subtype)
# Reference: docs/architecture/property-type-data-contract.md
# =============================================================================

# Maps lowercase SiteX UseCode to (SimplyRETS type, SimplyRETS subtype)
# SimplyRETS `type` query parameter uses FULL WORDS per the API spec:
#   https://docs.simplyrets.com/api/index.html#/Listings/get_properties
#   residential, rental, multifamily, commercial, land
# SimplyRETS `subtype` query parameter uses CamelCase (as returned in property.subType):
#   SingleFamilyResidence, Condominium, Townhouse, ManufacturedHome, Duplex
PROPERTY_TYPE_MAP = {
    # ---- Single Family Residence ----
    "sfr":                          ("residential", "SingleFamilyResidence"),
    "rsfr":                         ("residential", "SingleFamilyResidence"),
    "single family":                ("residential", "SingleFamilyResidence"),
    "singlefamily":                 ("residential", "SingleFamilyResidence"),
    "single family residential":    ("residential", "SingleFamilyResidence"),
    "residential":                  ("residential", "SingleFamilyResidence"),
    "pud":                          ("residential", "SingleFamilyResidence"),
    # ---- Condominium ----
    "condo":                        ("residential", "Condominium"),
    "condominium":                  ("residential", "Condominium"),
    # ---- Townhouse ----
    "townhouse":                    ("residential", "Townhouse"),
    "th":                           ("residential", "Townhouse"),
    "townhome":                     ("residential", "Townhouse"),
    # ---- Duplex ----
    "duplex":                       ("multifamily", "Duplex"),
    # ---- Triplex ----
    "triplex":                      ("multifamily", "Triplex"),
    # ---- Quadruplex ----
    "quadplex":                     ("multifamily", "Quadruplex"),
    "quadruplex":                   ("multifamily", "Quadruplex"),
    # ---- Multi-Family (generic) ----
    "multi-family":                 ("multifamily", None),
    "multifamily":                  ("multifamily", None),
    # ---- Mobile / Manufactured ----
    "mobile":                       ("residential", "ManufacturedHome"),
    "mobilehome":                   ("residential", "ManufacturedHome"),
    "manufactured":                 ("residential", "ManufacturedHome"),
    # ---- Land ----
    "land":                         ("land", None),
    "vacant land":                  ("land", None),
    # ---- Commercial ----
    "commercial":                   ("commercial", None),
}

# Post-filter: allowed SimplyRETS property.subType values per normalized category
# Used as safety net after SimplyRETS returns results.
# Values MUST match what SimplyRETS actually returns in property.subType — CamelCase, no spaces.
# See extract.py subtype_map for authoritative source: "SingleFamilyResidence", "Condominium", etc.
POST_FILTER_ALLOWED_SUBTYPES = {
    "singlefamilyresidence": {"SingleFamilyResidence", "Detached"},
    "condominium":           {"Condominium", "StockCooperative", "Attached"},
    "townhouse":             {"Townhouse", "Attached"},
    "duplex":                {"Duplex"},
    "triplex":               {"Triplex"},
    "quadruplex":            {"Quadruplex"},
    "manufacturedhome":      {"ManufacturedHome", "ManufacturedOnLand", "MobileHome"},
}


def resolve_simplyrets_type(sitex_use_code: Optional[str]) -> tuple:
    """
    Resolve SiteX UseCode to SimplyRETS (type, subtype) pair.

    Returns:
        (simplyrets_type, simplyrets_subtype) — subtype may be None
        Defaults to ("residential", "singlefamilyresidence") if unresolved.
    """
    if not sitex_use_code:
        return ("residential", "SingleFamilyResidence")

    key = sitex_use_code.strip().lower()

    # 1. Exact match
    if key in PROPERTY_TYPE_MAP:
        return PROPERTY_TYPE_MAP[key]

    # 2. Substring match (e.g., "rsfr" contains "sfr")
    for pattern, mapping in PROPERTY_TYPE_MAP.items():
        if pattern in key or key in pattern:
            return mapping

    # 3. Default to SFR (most common residential type)
    logger.warning(f"Unknown SiteX UseCode '{sitex_use_code}', defaulting to SFR")
    return ("residential", "SingleFamilyResidence")


def post_filter_by_property_type(
    listings: list,
    simplyrets_subtype: Optional[str],
) -> list:
    """
    Post-filter SimplyRETS listings to remove property types that don't match
    the subject property. This is a safety net since SimplyRETS may ignore
    the subtype filter depending on the vendor.

    Args:
        listings: Raw SimplyRETS listing dicts
        simplyrets_subtype: The subtype we queried for (e.g., "singlefamilyresidence")

    Returns:
        Filtered list of listings
    """
    if not simplyrets_subtype:
        return listings  # No subtype filter requested, return all

    allowed = POST_FILTER_ALLOWED_SUBTYPES.get(simplyrets_subtype.lower())
    if not allowed:
        return listings  # No post-filter defined for this subtype

    filtered = []
    removed = 0
    for listing in listings:
        prop = listing.get("property", {})
        listing_subtype = prop.get("subType") or prop.get("subTypeText") or ""
        # Allow if subType matches OR if subType is missing (don't over-filter)
        if not listing_subtype or listing_subtype in allowed:
            filtered.append(listing)
        else:
            removed += 1

    if removed > 0:
        logger.warning(
            f"Post-filter removed {removed} listings with mismatched subtype "
            f"(wanted: {simplyrets_subtype}, allowed: {allowed})"
        )

    return filtered


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


# ComparableProperty - Using simple dicts now (like Worker does) to avoid Pydantic validation issues
# with SimplyRETS data that may have None values or unexpected types


class ComparablesRequest(BaseModel):
    """Request for comparable properties with filtering options"""
    address: str
    city_state_zip: Optional[str] = ""
    # Optional subject property characteristics (override SiteX lookup)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    property_type: Optional[str] = None
    # Search filters
    radius_miles: float = Field(default=1.0, ge=0.1, le=10.0, description="Search radius in miles")
    sqft_variance: float = Field(default=0.20, ge=0.0, le=0.50, description="SQFT +/- variance (0.20 = 20%). 0 = no sqft filter.")
    status: Literal["Closed", "Active", "All"] = "Active"
    limit: int = Field(default=15, ge=1, le=50)


# SearchParamsUsed - Now using simple dict in ComparablesResponse
# class SearchParamsUsed(BaseModel):
#     radius_miles: float
#     sqft_variance: float
#     sqft_range: Optional[Dict[str, int]] = None
#     beds_range: Optional[Dict[str, int]] = None
#     baths_range: Optional[Dict[str, int]] = None
#     total_before_filter: int = 0
#     was_auto_expanded: bool = False


class ComparablesResponse(BaseModel):
    """Response with comparable properties"""
    success: bool
    subject_property: Optional[dict] = None  # Simple dict for subject info
    comparables: List[dict] = []  # Simple dicts like Worker uses
    total_found: int = 0
    search_params: Optional[dict] = None  # Simple dict for params
    error: Optional[str] = None
    # C3: Fallback ladder metadata for confidence badge
    comp_ladder_level: Optional[str] = None
    comp_confidence_grade: Optional[str] = None
    comp_confidence_reason: Optional[str] = None


class PropertyReportCreate(BaseModel):
    """Create a new property report"""
    report_type: Literal["seller", "buyer"] = "seller"
    # Theme: accepts number (1-5) or name (classic, modern, elegant, teal, bold)
    theme: Any = Field(default=4, description="Theme ID (1-5) or name (classic, modern, elegant, teal, bold)")
    accent_color: str = Field(default="#0d294b", pattern=r"^#[0-9a-fA-F]{6}$")
    language: Literal["en", "es"] = "en"
    
    # Property address (new structure - can also use legacy address/city_state_zip)
    property_address: Optional[str] = None
    property_city: Optional[str] = None
    property_state: str = "CA"
    property_zip: Optional[str] = None
    
    # Legacy address fields (for backwards compatibility)
    address: Optional[str] = Field(default=None, min_length=5)
    city_state_zip: Optional[str] = ""
    
    # Property details (optional, can come from SiteX lookup)
    apn: Optional[str] = None
    owner_name: Optional[str] = None
    
    # Comparables and pages
    selected_comp_ids: Optional[List[str]] = None
    comparables: Optional[List[dict]] = None  # Full comparable objects
    selected_pages: Optional[List[str]] = None
    comp_parameters: Optional[dict] = None
    sitex_data: Optional[dict] = None


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
    comparables: Optional[List[dict]] = None  # Full comparable objects
    selected_pages: Optional[List[str]] = None  # List of page IDs to include
    pdf_url: Optional[str] = None
    status: str
    short_code: str
    qr_code_url: Optional[str] = None
    error_message: Optional[str] = None
    view_count: int
    created_at: str
    updated_at: str


class PreviewRequest(BaseModel):
    """Request for live HTML preview of a report"""
    theme: int = Field(default=4, ge=1, le=5, description="Theme ID (1-5)")
    accent_color: str = Field(default="#0d294b", pattern=r"^#[0-9a-fA-F]{6}$")
    
    # Property data
    property_address: str
    property_city: str = ""
    property_state: str = "CA"
    property_zip: str = ""
    
    # SiteX data (full property details)
    sitex_data: Optional[dict] = None
    
    # Comparables (selected comparables)
    comparables: Optional[List[dict]] = None
    
    # Agent/branding context (optional, will use defaults if not provided)
    agent: Optional[dict] = None
    branding: Optional[dict] = None

    # Pages to render — if omitted, defaults to cover + comparables + range (fast preview)
    pages: Optional[List[str]] = None


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
    
    Enhanced with:
    - SQFT variance filtering (+/- percentage)
    - Radius-based distance filtering
    - Bed/bath matching
    - Returns search params used for UI adjustment
    
    Flow:
    1. Look up subject property via SiteX (or use provided characteristics)
    2. Build SimplyRETS query with filters
    3. Post-filter by distance if lat/lng available
    4. Return comparables with search metadata
    """
    # Auth required
    require_account_id(request)
    
    # Use values directly from payload - frontend already has property details from Step 1
    # NO SiteX call needed here - SimplyRETS is all we need for comparables
    subject_sqft = payload.sqft
    subject_beds = payload.beds
    subject_baths = payload.baths
    subject_lat = payload.latitude
    subject_lng = payload.longitude
    subject_prop_type = payload.property_type
    
    # Parse city and zip from city_state_zip (e.g., "La Verne, CA 91750")
    subject_city = None
    subject_zip = None
    if payload.city_state_zip:
        parts = payload.city_state_zip.split(",")
        if parts:
            subject_city = parts[0].strip()
        # Try to extract ZIP from last part (e.g., "CA 91750" -> "91750")
        if len(parts) > 1:
            state_zip = parts[-1].strip()
            zip_parts = state_zip.split()
            if zip_parts and zip_parts[-1].isdigit():
                subject_zip = zip_parts[-1]
    
    logger.warning(f"Comparables search: city={subject_city}, zip={subject_zip}, beds={subject_beds}, baths={subject_baths}, sqft={subject_sqft}, property_type={subject_prop_type}")
    
    # Track search params for response
    sqft_range = None
    beds_range = None
    baths_range = None
    
    # Step 2: Search SimplyRETS for comparables using the API's own client
    # (API and worker are separate deployments, so we use our own simplyrets service)
    try:
        # Build search params - same logic as working Market Reports
        # Map status filter to SimplyRETS values
        status_map = {
            "Closed": "Closed",
            "Active": "Active",
            "All": "Active,Closed",
        }
        # PROPERTY TYPE FILTER — uses canonical mapping from data contract
        # See: docs/architecture/property-type-data-contract.md
        sr_type, sr_subtype = resolve_simplyrets_type(subject_prop_type)
        logger.warning(f"Property type mapping: '{subject_prop_type}' -> type={sr_type}, subtype={sr_subtype}")

        # Build base SQFT range for ladder widening.
        # sqft_variance == 0 means the user selected "Any" in the UI — skip sqft filter from L0.
        base_sqft_variance = payload.sqft_variance if payload.sqft_variance > 0 else None

        # ──────────────────────────────────────────────────────────────────────
        # FALLBACK LADDER for comps: start strict, progressively loosen until
        # we have enough results. Each ladder level logs which level succeeded.
        #
        # Key design decisions:
        #   - sqft_var=None  → skip the sqft filter entirely (thin markets)
        #   - We track the BEST (most results) seen across all levels so we
        #     never return fewer comps than a prior level happened to find.
        #   - FALLBACK_MIN is the target; we still return whatever we found
        #     even if we never reach it (avoids returning 0 when 2–4 exist).
        # ──────────────────────────────────────────────────────────────────────
        FALLBACK_MIN = 5   # target; we keep trying until we reach this

        def _build_params(sqft_var, extra_beds: int = 0,
                          include_subtype: bool = True,
                          use_city: bool = True) -> Dict[str, Any]:
            """Build SimplyRETS params for one ladder attempt."""
            p: Dict[str, Any] = {
                "status": status_map.get(payload.status, "Active"),
                "type": sr_type,
                "limit": payload.limit * 4,
            }
            # Location — prefer postalCodes (precise) + cities (deterministic)
            if subject_zip:
                p["postalCodes"] = subject_zip
            if subject_city and use_city:
                p["cities"] = subject_city

            # SQFT variance — None means no sqft filter
            if subject_sqft and sqft_var is not None:
                p["minarea"] = int(subject_sqft * (1 - sqft_var))
                p["maxarea"] = int(subject_sqft * (1 + sqft_var))

            # Bed filter
            if subject_beds:
                p["minbeds"] = max(1, subject_beds - 1 - extra_beds)
                p["maxbeds"] = subject_beds + 1 + extra_beds

            # Bath filter (only at strict level, extra_beds==0)
            if subject_baths and extra_beds == 0:
                p["minbaths"] = max(1, int(subject_baths) - 1)
                p["maxbaths"] = int(subject_baths) + 1

            # Subtype
            if include_subtype and sr_subtype:
                p["subtype"] = sr_subtype

            return p

        def _filter_distance(raw: List[Dict], radius: float) -> List[Dict]:
            """Post-filter by radius if coordinates known."""
            if not (subject_lat and subject_lng):
                return raw
            out = []
            for lst in raw:
                geo = lst.get("geo", {})
                clat, clng = geo.get("lat"), geo.get("lng")
                if clat and clng:
                    d = haversine_distance(subject_lat, subject_lng, clat, clng)
                    if d <= radius:
                        lst["_distance_miles"] = round(d, 2)
                        out.append(lst)
                else:
                    lst["_distance_miles"] = None
                    out.append(lst)
            out.sort(key=lambda x: x.get("_distance_miles") or 999)
            return out

        # Ladder definition:
        #   (label, sqft_var, extra_beds, include_subtype, use_city, radius_miles)
        # sqft_var=None → no sqft filter
        # radius progressively widens at later levels
        _r = payload.radius_miles
        ladder = [
            ("L0:strict",              base_sqft_variance, 0, True,  True,  _r),
            ("L1:no-subtype",          base_sqft_variance, 0, False, True,  _r),
            ("L2:sqft+30%",            0.30,               0, False, True,  _r),
            ("L3:sqft+50%,beds+1",     0.50,               1, False, True,  _r),
            ("L4:no-sqft,beds+2",      None,               2, False, True,  _r),
            ("L5:no-sqft,radius*3",    None,               2, False, True,  _r * 3),
        ]

        listings: List[Dict] = []
        best_listings: List[Dict] = []   # best seen across all levels
        fallback_level_used = "L0:strict"
        total_before_filter = 0

        for label, sqft_var, extra_beds, incl_sub, use_city, radius in ladder:
            params = _build_params(sqft_var, extra_beds, incl_sub, use_city)
            logger.warning(f"Comps fallback {label}: params={params}")

            raw = await simplyrets_fetch_properties(params, limit=payload.limit * 4)
            logger.warning(f"Comps fallback {label}: SimplyRETS returned {len(raw)} raw")

            # Distance filter (radius widens at later levels)
            filtered = _filter_distance(raw, radius)
            # Always post-filter by property type to keep comps same type as subject.
            # incl_sub only controls whether we send the subtype param to SimplyRETS
            # (to avoid over-filtering by the API at looser levels); we still enforce
            # type consistency ourselves on every level.
            filtered = post_filter_by_property_type(filtered, sr_subtype)

            total_before_filter = len(raw)

            # Always keep the best (most) results seen across all ladder levels
            if len(filtered) > len(best_listings):
                best_listings = filtered
                fallback_level_used = label

            if len(filtered) >= FALLBACK_MIN:
                logger.warning(f"Comps fallback succeeded at {label}: {len(filtered)} results")
                break
            else:
                logger.warning(
                    f"Comps fallback {label}: only {len(filtered)} results (need {FALLBACK_MIN}), "
                    f"best so far={len(best_listings)}, trying next level..."
                )

        # Use the best results found across all ladder levels
        listings = best_listings

        # Track sqft_range/beds_range/baths_range for response (from level 0 params for display)
        _p0 = _build_params(base_sqft_variance, 0, True, True)
        sqft_range = (
            {"min": _p0["minarea"], "max": _p0["maxarea"]}
            if "minarea" in _p0 else None
        )
        beds_range = (
            {"min": _p0.get("minbeds"), "max": _p0.get("maxbeds")}
            if "minbeds" in _p0 else None
        )
        baths_range = (
            {"min": _p0.get("minbaths"), "max": _p0.get("maxbaths")}
            if "minbaths" in _p0 else None
        )

        logger.warning(
            f"Comparables final: {len(listings)} after fallback ladder "
            f"(level_used={fallback_level_used}, total_before_filter={total_before_filter})"
        )
        
        # Convert to simple dicts (like Worker does) - no Pydantic validation issues
        comparables = []
        for listing in listings[:payload.limit]:
            prop = listing.get("property") or {}
            address_obj = listing.get("address") or {}
            geo = listing.get("geo") or {}
            mls_obj = listing.get("mls") or {}
            
            comp = {
                "mls_id": str(listing.get("mlsId") or ""),
                "address": address_obj.get("full") or "",
                "city": address_obj.get("city") or "",
                "state": address_obj.get("state") or "",
                "zip_code": address_obj.get("postalCode") or "",
                "price": listing.get("listPrice") or listing.get("closePrice") or 0,
                "list_price": listing.get("listPrice"),
                "close_price": listing.get("closePrice"),
                "bedrooms": prop.get("bedrooms") or 0,
                "bathrooms": prop.get("bathsFull") or 0,
                "sqft": prop.get("area") or 0,
                "year_built": prop.get("yearBuilt"),
                "lot_size": prop.get("lotSize"),
                "photo_url": (listing.get("photos") or [None])[0],
                "photos": listing.get("photos") or [],
                "status": mls_obj.get("status") or "Closed",
                "dom": mls_obj.get("daysOnMarket"),
                "days_on_market": mls_obj.get("daysOnMarket"),
                "list_date": listing.get("listDate"),
                "close_date": listing.get("closeDate"),
                "lat": geo.get("lat"),
                "lng": geo.get("lng"),
                "distance_miles": listing.get("_distance_miles"),
            }
            comparables.append(comp)
        
        # Build subject property info for response
        subject_info = {
            "address": payload.address,
            "city": subject_city,
            "zip_code": subject_zip,
            "beds": subject_beds,
            "baths": subject_baths,
            "sqft": subject_sqft,
            "lat": subject_lat,
            "lng": subject_lng,
        }
        
        # Build search params as simple dict
        search_params = {
            "radius_miles": payload.radius_miles,
            "sqft_variance": payload.sqft_variance,
            "sqft_range": sqft_range,
            "beds_range": beds_range,
            "baths_range": baths_range,
            "total_before_filter": total_before_filter,
        }
        
        # C3: Compute confidence grade from fallback ladder level
        _lv = (fallback_level_used or "").lower()
        if _lv.startswith("l0"):
            _conf_grade  = "A"
            _conf_reason = "Strict match"
        elif _lv.startswith("l1"):
            _conf_grade  = "B"
            _conf_reason = "Subtype relaxed"
        elif _lv.startswith("l2"):
            _conf_grade  = "B"
            _conf_reason = "Sqft range widened"
        elif _lv.startswith("l3") or _lv.startswith("l4"):
            _conf_grade  = "C"
            _conf_reason = "Sqft + beds loosened"
        else:
            _conf_grade  = "C"
            _conf_reason = "Thin market"
        if len(comparables) < 3:
            _conf_grade  = "D"
            _conf_reason = "Thin market"

        return ComparablesResponse(
            success=True,
            subject_property=subject_info,
            comparables=comparables,
            total_found=len(comparables),
            search_params=search_params,
            comp_ladder_level=fallback_level_used,
            comp_confidence_grade=_conf_grade,
            comp_confidence_reason=_conf_reason,
        )
        
    except Exception as e:
        logger.error(f"Comparables search error: {e}", exc_info=True)
        return ComparablesResponse(
            success=False,
            subject_property=None,
            comparables=[],
            total_found=0,
            error=f"Comparable search failed: {str(e)}"
        )


# =============================================================================
# PROPERTY REPORT STATISTICS ENDPOINTS
# =============================================================================


class PropertyStatsResponse(BaseModel):
    """Property report statistics for dashboard"""
    period: dict
    summary: dict
    report_types: Optional[dict] = None
    themes: dict
    engagement: dict
    leads: dict
    top_reports: Optional[List[dict]] = None
    daily_trend: Optional[List[dict]] = None
    all_time: Optional[dict] = None


class AffiliateStatsResponse(BaseModel):
    """Affiliate-level property report statistics"""
    period: dict
    summary: dict
    aggregate: dict
    themes: dict
    leaderboard: List[dict]
    inactive_agents: List[dict]


@router.get("/stats", response_model=PropertyStatsResponse)
def get_property_stats(
    request: Request,
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)")
):
    """
    Get property report statistics for the current user's account.
    
    Returns:
    - Report counts and completion rates
    - Theme distribution
    - Lead metrics and conversion rates
    - Top performing reports
    - Daily activity trend
    """
    account_id = require_account_id(request)
    
    # Parse dates
    from_dt = datetime.fromisoformat(from_date.replace('Z', '')) if from_date else None
    to_dt = datetime.fromisoformat(to_date.replace('Z', '')) if to_date else None
    
    stats = get_agent_stats(account_id, from_dt, to_dt)
    return stats


@router.get("/stats/affiliate", response_model=AffiliateStatsResponse)
def get_affiliate_property_stats(
    request: Request,
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)")
):
    """
    Get property report statistics for all sponsored agents under this affiliate.
    
    Only accessible to INDUSTRY_AFFILIATE accounts.
    
    Returns:
    - Aggregate stats across all sponsored agents
    - Agent leaderboard (by reports + leads)
    - Inactive agents list
    - Theme distribution
    """
    account_id = require_account_id(request)
    
    # Verify this is an affiliate account
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        cur.execute("SELECT account_type FROM accounts WHERE id = %s", (account_id,))
        row = fetchone_dict(cur)
        if not row or row.get("account_type") != "INDUSTRY_AFFILIATE":
            raise HTTPException(
                status_code=403, 
                detail="This endpoint is only available to affiliate accounts"
            )
    
    # Parse dates
    from_dt = datetime.fromisoformat(from_date.replace('Z', '')) if from_date else None
    to_dt = datetime.fromisoformat(to_date.replace('Z', '')) if to_date else None
    
    stats = get_affiliate_stats(account_id, from_dt, to_dt)
    return stats


# =============================================================================
# PREVIEW ENDPOINT
# =============================================================================


@router.post("/preview")
async def generate_preview_html(payload: PreviewRequest, request: Request):
    """
    Generate live HTML preview of a property report.
    
    This endpoint renders the report template with the provided data
    and returns HTML that can be displayed in an iframe for real-time preview.
    
    Used by the wizard Step 3 (Theme Selection) to show users
    exactly what their report will look like.
    """
    # Import PropertyReportBuilder here to avoid circular imports
    import sys
    import os
    
    # Add worker path for importing PropertyReportBuilder
    worker_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "worker", "src")
    if worker_path not in sys.path:
        sys.path.insert(0, worker_path)
    
    try:
        from worker.property_builder import PropertyReportBuilder
    except ImportError:
        # If we can't import the worker module, return a fallback response
        raise HTTPException(
            status_code=500, 
            detail="Preview generation is not available in this environment"
        )
    
    # Build report data structure matching PropertyReportBuilder expectations
    report_data = {
        "theme": payload.theme,
        "accent_color": payload.accent_color,
        "report_type": "seller",
        "property_address": payload.property_address,
        "property_city": payload.property_city,
        "property_state": payload.property_state,
        "property_zip": payload.property_zip,
        "sitex_data": payload.sitex_data or {},
        "comparables": payload.comparables or [],
        "agent": payload.agent or {
            "name": "Your Name",
            "title": "Real Estate Agent",
            "phone": "(555) 123-4567",
            "email": "agent@example.com",
            "company_name": "Your Company",
        },
        "branding": payload.branding or {},
        "selected_pages": ["cover", "contents", "aerial", "property", "analysis", "comparables", "range"],
    }
    
    # Pages to render — caller can limit to just a few pages for speed
    preview_pages = payload.pages or ["cover", "property", "comparables"]

    try:
        builder = PropertyReportBuilder(report_data)
        html = builder.render_preview(pages=preview_pages)
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html, media_type="text/html")
        
    except Exception as e:
        logger.error(f"Preview generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")


# =============================================================================
# PROPERTY REPORT ENDPOINTS
# =============================================================================


@router.post("/reports", response_model=PropertyReportResponse)
async def create_property_report(payload: PropertyReportCreate, request: Request):
    """
    Create a new property report.
    
    1. Check plan limits
    2. Use provided sitex_data or lookup property via SiteX
    3. Generate short_code and QR code
    4. Store selected_pages and selected_comp_ids
    5. Queue PDF generation
    """
    account_id = require_account_id(request)
    user_id = require_user_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        # 1. Check plan limits
        allowed, message = check_property_report_limits(cur, account_id)
        if not allowed:
            raise HTTPException(status_code=429, detail=message)
        
        # 2. Determine address input (new vs legacy format)
        # New format: property_address, property_city, property_state, property_zip
        # Legacy format: address, city_state_zip
        lookup_address = payload.property_address or payload.address
        lookup_csz = payload.city_state_zip or ""
        
        if payload.property_city and payload.property_state:
            lookup_csz = f"{payload.property_city}, {payload.property_state} {payload.property_zip or ''}"
        
        # Use provided sitex_data or lookup via SiteX
        property_data = None
        sitex_data = payload.sitex_data
        
        if not sitex_data and lookup_address:
            try:
                property_data = await lookup_property(lookup_address, lookup_csz)
                if property_data:
                    sitex_data = property_data.model_dump()
            except SiteXError as e:
                logger.warning(f"SiteX lookup failed: {e}")
        
        # Extract address components (from sitex_data, property_data, or payload)
        if sitex_data:
            prop_address = sitex_data.get("street") or sitex_data.get("full_address", "").split(",")[0] or payload.property_address or lookup_address
            prop_city = sitex_data.get("city") or payload.property_city or ""
            prop_state = sitex_data.get("state") or payload.property_state or "CA"
            prop_zip = sitex_data.get("zip_code") or payload.property_zip or ""
            prop_county = sitex_data.get("county")
            apn = payload.apn or sitex_data.get("apn")
            owner_name = payload.owner_name or sitex_data.get("owner_name")
            legal_desc = sitex_data.get("legal_description")
            prop_type = sitex_data.get("property_type")
        elif property_data:
            prop_address = property_data.street or lookup_address.split(",")[0].strip()
            prop_city = property_data.city or payload.property_city or ""
            prop_state = property_data.state or payload.property_state or "CA"
            prop_zip = property_data.zip_code or payload.property_zip or ""
            prop_county = property_data.county
            apn = payload.apn or property_data.apn
            owner_name = payload.owner_name or property_data.owner_name
            legal_desc = property_data.legal_description
            prop_type = property_data.property_type
            sitex_data = property_data.model_dump()
        else:
            # Parse from input
            prop_address = payload.property_address or (lookup_address.split(",")[0].strip() if lookup_address else "")
            prop_city = payload.property_city or ""
            prop_state = payload.property_state or "CA"
            prop_zip = payload.property_zip or ""
            
            # Try to parse legacy city_state_zip if new fields not provided
            if not prop_city and lookup_csz:
                csz_parts = lookup_csz.split(",")
                prop_city = csz_parts[0].strip() if csz_parts else ""
                if len(csz_parts) > 1:
                    state_zip = csz_parts[1].strip().split()
                    prop_state = state_zip[0] if state_zip else "CA"
                    prop_zip = state_zip[1] if len(state_zip) > 1 else ""
            
            prop_county = None
            apn = payload.apn
            owner_name = payload.owner_name
            legal_desc = None
            prop_type = None
        
        # 3. Create report record (short_code auto-generated by trigger)
        # Check if selected_pages column exists (for backwards compatibility)
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'property_reports' AND column_name = 'selected_pages'
            )
        """)
        has_selected_pages_column = cur.fetchone()[0]
        
        if has_selected_pages_column:
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
                    comparables,
                    selected_pages,
                    status
                )
                VALUES (
                    %s::uuid, %s::uuid, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb, %s::jsonb, 'draft'
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
                json.dumps(payload.comparables) if payload.comparables else None,
                json.dumps(payload.selected_pages) if payload.selected_pages else None,
            ))
        else:
            # Fallback: insert without selected_pages column
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
                    comparables,
                    status
                )
                VALUES (
                    %s::uuid, %s::uuid, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb, 'draft'
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
                json.dumps(payload.comparables) if payload.comparables else None,
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
        
        # 5. Queue PDF generation via Celery
        try:
            enqueue_property_report(report_id)
            logger.info(f"Queued property report PDF generation: {report_id}")
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
        
        # Check if selected_pages column exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'property_reports' AND column_name = 'selected_pages'
            )
        """)
        has_selected_pages_column = cur.fetchone()[0]
        
        if has_selected_pages_column:
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
                    selected_pages,
                    pdf_url,
                    status,
                    short_code,
                    qr_code_url,
                    error_message,
                    view_count,
                    created_at::text,
                    updated_at::text
                FROM property_reports
                WHERE id = %s::uuid AND account_id = %s::uuid
            """, (report_id, account_id))
        else:
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
                    NULL as selected_pages,
                    pdf_url,
                    status,
                    short_code,
                    qr_code_url,
                    error_message,
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
        selected_pages=row[18],
        pdf_url=row[19],
        status=row[20],
        short_code=row[21],
        qr_code_url=row[22],
        error_message=row[23],
        view_count=row[24],
        created_at=row[25],
        updated_at=row[26],
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
