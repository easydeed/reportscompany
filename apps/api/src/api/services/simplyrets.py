"""
SimplyRETS API Client for Property Reports comparables.

This replicates the WORKING SimplyRETS integration from the worker service.
The API and worker are separate deployments, so we need our own client here.

Auth: HTTP Basic Auth with SIMPLYRETS_USERNAME and SIMPLYRETS_PASSWORD
Base URL: https://api.simplyrets.com
"""

import os
import logging
from typing import Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)

# SimplyRETS Configuration - MUST match worker env vars
BASE_URL = os.getenv("SIMPLYRETS_BASE_URL", "https://api.simplyrets.com")
USERNAME = os.getenv("SIMPLYRETS_USERNAME", "simplyrets")
PASSWORD = os.getenv("SIMPLYRETS_PASSWORD", "simplyrets")
TIMEOUT = float(os.getenv("SIMPLYRETS_TIMEOUT_S", "30"))

# Log configuration on startup (mask password) - use WARNING so it shows in Render logs
logger.warning(f"SimplyRETS configured: URL={BASE_URL}, User={USERNAME}, Timeout={TIMEOUT}s")


async def fetch_properties(params: Dict, limit: Optional[int] = None) -> List[Dict]:
    """
    Fetch properties from SimplyRETS API.
    
    This is an async version of the worker's fetch_properties function.
    Uses HTTP Basic Auth (same as the working worker implementation).
    
    Args:
        params: SimplyRETS query parameters (q, status, type, minbeds, etc.)
        limit: Maximum number of results to return
        
    Returns:
        List of property dictionaries from SimplyRETS
    """
    # Apply limit to params
    query_params = {**params}
    if limit:
        query_params["limit"] = min(limit, 500)  # SimplyRETS max per request
    
    # Ensure we always include type=RES to exclude rentals
    if "type" not in query_params:
        query_params["type"] = "RES"
    
    logger.warning(f"SimplyRETS request: GET /properties params={query_params}")
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(
                f"{BASE_URL}/properties",
                params=query_params,
                auth=(USERNAME, PASSWORD),  # HTTP Basic Auth - CRITICAL!
            )
            
            # Log response status
            logger.warning(f"SimplyRETS response: status={response.status_code}")
            
            if response.status_code == 401:
                logger.error("SimplyRETS auth failed - check SIMPLYRETS_USERNAME/PASSWORD env vars")
                raise Exception("SimplyRETS authentication failed")
            
            if response.status_code == 429:
                logger.warning("SimplyRETS rate limited")
                raise Exception("SimplyRETS rate limit exceeded")
            
            response.raise_for_status()
            
            data = response.json()
            logger.warning(f"SimplyRETS returned {len(data)} properties")
            
            return data
            
        except httpx.TimeoutException:
            logger.error(f"SimplyRETS timeout after {TIMEOUT}s")
            raise Exception("SimplyRETS request timed out")
        except httpx.HTTPStatusError as e:
            logger.error(f"SimplyRETS HTTP error: {e.response.status_code} - {e.response.text[:200]}")
            raise
        except Exception as e:
            logger.error(f"SimplyRETS error: {type(e).__name__}: {e}")
            raise


def build_comparables_params(
    city: Optional[str] = None,
    zip_code: Optional[str] = None,
    status: str = "Closed",
    min_sqft: Optional[int] = None,
    max_sqft: Optional[int] = None,
    min_beds: Optional[int] = None,
    max_beds: Optional[int] = None,
    min_baths: Optional[int] = None,
    max_baths: Optional[int] = None,
    property_subtype: Optional[str] = None,
    limit: int = 25,
) -> Dict:
    """
    Build SimplyRETS query parameters for comparable properties search.
    
    Follows the same pattern as the working Market Reports query builders.
    
    Args:
        city: City name for location search (uses 'q' param)
        zip_code: ZIP code for location search (uses 'postalCodes' param)
        status: Listing status - "Active", "Closed", or "Active,Closed"
        min_sqft: Minimum square footage
        max_sqft: Maximum square footage
        min_beds: Minimum bedrooms
        max_beds: Maximum bedrooms
        min_baths: Minimum bathrooms
        max_baths: Maximum bathrooms
        property_subtype: Property subtype (SingleFamilyResidence, Condominium, etc.)
        limit: Maximum results to return
        
    Returns:
        Dictionary of SimplyRETS query parameters
    """
    params: Dict = {
        "type": "RES",  # CRITICAL: Exclude rentals
        "status": status,
        "limit": limit,
    }
    
    # Location - prefer ZIP code, fall back to city search
    if zip_code:
        params["postalCodes"] = zip_code
    if city:
        params["q"] = city  # Fuzzy search - works with all SimplyRETS accounts
    
    # Square footage filter
    if min_sqft:
        params["minarea"] = min_sqft
    if max_sqft:
        params["maxarea"] = max_sqft
    
    # Bedroom filter
    if min_beds:
        params["minbeds"] = min_beds
    if max_beds:
        params["maxbeds"] = max_beds
    
    # Bathroom filter
    if min_baths:
        params["minbaths"] = min_baths
    if max_baths:
        params["maxbaths"] = max_baths
    
    # Property subtype filter
    if property_subtype:
        params["subtype"] = property_subtype
    
    return params


def normalize_listing(listing: Dict) -> Dict:
    """
    Normalize a SimplyRETS listing into a consistent format.
    
    This matches the response structure expected by the frontend.
    """
    prop = listing.get("property", {})
    address = listing.get("address", {})
    geo = listing.get("geo", {})
    mls = listing.get("mls", {})
    photos = listing.get("photos", [])
    
    return {
        "id": str(listing.get("mlsId", "")),
        "mls_id": str(listing.get("mlsId", "")),
        "address": address.get("full", ""),
        "city": address.get("city", ""),
        "state": address.get("state", ""),
        "zip_code": address.get("postalCode", ""),
        "list_price": listing.get("listPrice"),
        "close_price": listing.get("closePrice"),
        "price": listing.get("closePrice") or listing.get("listPrice") or 0,
        "status": mls.get("status", ""),
        "bedrooms": prop.get("bedrooms"),
        "bathrooms": prop.get("bathsFull"),
        "sqft": prop.get("area"),
        "lot_size": prop.get("lotSize"),
        "year_built": prop.get("yearBuilt"),
        "dom": mls.get("daysOnMarket"),
        "days_on_market": mls.get("daysOnMarket"),
        "list_date": listing.get("listDate"),
        "close_date": listing.get("closeDate"),
        "photo_url": photos[0] if photos else None,
        "photos": photos,
        "lat": geo.get("lat"),
        "lng": geo.get("lng"),
        "property_type": prop.get("type"),
        "property_subtype": prop.get("subType"),
    }

