"""
SiteX Pro (ICE) Property Data Service
=====================================

Official API integration for SiteX Pro REST API.
Based on ICE SiteXPro REST QuickStart Guide v1.06 (July 2025)

Authentication: OAuth2 client credentials flow
Token TTL: 10 minutes (refresh at 9 minutes)

Environment Variables Required:
- SITEX_BASE_URL: API gateway URL (UAT or Prod)
- SITEX_CLIENT_ID: OAuth2 client ID  
- SITEX_CLIENT_SECRET: OAuth2 client secret
- SITEX_FEED_ID: Feed identifier (e.g., 100001)
"""

import httpx
import logging
import hashlib
import time
import asyncio
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class SiteXConfig:
    """SiteX API Configuration"""
    
    def __init__(self):
        self.base_url = os.getenv("SITEX_BASE_URL", "https://api.uat.bkitest.com")
        self.client_id = os.getenv("SITEX_CLIENT_ID", "")
        self.client_secret = os.getenv("SITEX_CLIENT_SECRET", "")
        self.feed_id = os.getenv("SITEX_FEED_ID", "100001")
        
    @property
    def token_url(self) -> str:
        return f"{self.base_url}/ls/apigwy/oauth2/v1/token"
    
    @property
    def search_url(self) -> str:
        return f"{self.base_url}/realestatedata/search"
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not all([self.base_url, self.client_id, self.client_secret, self.feed_id]):
            logger.error("SiteX configuration incomplete. Check environment variables.")
            return False
        return True


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class PropertyData(BaseModel):
    """Normalized property data from SiteX"""
    
    # Address
    full_address: str = ""
    street: str = ""
    city: str = ""
    state: str = "CA"
    zip_code: str = ""
    county: str = ""
    
    # Identifiers
    apn: str = ""
    fips: str = ""
    
    # Owner
    owner_name: str = ""
    secondary_owner: Optional[str] = None
    
    # Legal
    legal_description: str = ""
    
    # Property characteristics
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[int] = None
    year_built: Optional[int] = None
    property_type: str = ""
    
    # Tax/Assessment
    assessed_value: Optional[int] = None
    tax_amount: Optional[float] = None
    land_value: Optional[int] = None
    improvement_value: Optional[int] = None
    tax_year: Optional[int] = None
    
    # Location
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Metadata
    source: str = "sitex"
    confidence: float = 0.95
    raw_response: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    
    class Config:
        extra = "ignore"


class SiteXLocation(BaseModel):
    """Location match from SiteX search"""
    fips: str = ""
    apn: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""


# =============================================================================
# TOKEN MANAGER
# =============================================================================

class SiteXTokenManager:
    """
    Manages OAuth2 tokens for SiteX API.
    Tokens expire after 10 minutes - we refresh at 9 minutes.
    Thread-safe with asyncio lock.
    """
    
    def __init__(self, config: SiteXConfig):
        self.config = config
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._lock = asyncio.Lock()
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def get_token(self) -> str:
        """Get valid access token, refreshing if needed"""
        async with self._lock:
            # Check if current token is still valid (with 1 minute buffer)
            if self._token and self._token_expiry:
                if datetime.utcnow() < self._token_expiry - timedelta(minutes=1):
                    return self._token
            
            # Need new token
            return await self._refresh_token()
    
    async def _refresh_token(self) -> str:
        """Fetch new access token from SiteX"""
        logger.info("Refreshing SiteX access token...")
        
        try:
            response = await self._client.post(
                self.config.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            response.raise_for_status()
            
            data = response.json()
            self._token = data.get("access_token")
            
            # Token expires in 10 minutes, we'll refresh at 9
            expires_in = data.get("expires_in", 600)
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            logger.info(f"SiteX token refreshed, expires in {expires_in}s")
            return self._token
            
        except httpx.HTTPError as e:
            logger.error(f"SiteX token refresh failed: {e}")
            raise SiteXAuthError(f"Failed to obtain access token: {e}")
    
    async def close(self):
        """Cleanup"""
        await self._client.aclose()


# =============================================================================
# EXCEPTIONS
# =============================================================================

class SiteXError(Exception):
    """Base SiteX exception"""
    pass

class SiteXAuthError(SiteXError):
    """Authentication failed"""
    pass

class SiteXNotFoundError(SiteXError):
    """Property not found"""
    pass

class SiteXMultiMatchError(SiteXError):
    """Multiple properties matched"""
    def __init__(self, message: str, locations: list):
        super().__init__(message)
        self.locations = locations


# =============================================================================
# SITEX CLIENT
# =============================================================================

class SiteXClient:
    """
    SiteX Pro REST API Client
    
    Usage:
        client = SiteXClient()
        await client.initialize()
        
        # Search by address
        property_data = await client.search_by_address(
            address="714 Vine St",
            city_state_zip="Anaheim, CA 92805"
        )
        
        # Search by APN (more precise)
        property_data = await client.search_by_apn(
            fips="06059",
            apn="035-202-10"
        )
    """
    
    def __init__(self, config: Optional[SiteXConfig] = None):
        self.config = config or SiteXConfig()
        self._token_manager: Optional[SiteXTokenManager] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize client and token manager"""
        if self._initialized:
            return
            
        if not self.config.validate():
            raise SiteXError("Invalid SiteX configuration")
        
        self._token_manager = SiteXTokenManager(self.config)
        self._client = httpx.AsyncClient(timeout=30.0)
        self._initialized = True
        logger.info(f"SiteX client initialized: {self.config.base_url}")
    
    async def close(self):
        """Cleanup resources"""
        if self._token_manager:
            await self._token_manager.close()
        if self._client:
            await self._client.aclose()
        self._initialized = False
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # -------------------------------------------------------------------------
    # SEARCH METHODS
    # -------------------------------------------------------------------------
    
    async def search_by_address(
        self,
        address: str,
        city_state_zip: str,
        owner: Optional[str] = None
    ) -> PropertyData:
        """
        Search for property by address.
        
        Args:
            address: Street address (e.g., "714 Vine St")
            city_state_zip: City, State ZIP (e.g., "Anaheim, CA 92805" or just "92805")
            owner: Optional owner name for disambiguation
            
        Returns:
            PropertyData with all available property information
            
        Raises:
            SiteXNotFoundError: If no property found
            SiteXMultiMatchError: If multiple properties match (contains locations)
        """
        await self._ensure_initialized()
        
        params = {
            "addr": address,
            "lastLine": city_state_zip,
            "feedId": self.config.feed_id,
            "options": "search_exclude_nonres=Y",
            "clientReference": f"trendy_{int(time.time())}"
        }
        
        if owner:
            params["owner"] = owner
        
        logger.info(f"SiteX address search: {address}, {city_state_zip}")
        
        response = await self._make_request(params)
        return self._parse_response(response)
    
    async def search_by_apn(self, fips: str, apn: str) -> PropertyData:
        """
        Search for property by FIPS code and APN.
        This is the most precise search method.
        
        Args:
            fips: 5-digit county FIPS code (e.g., "06037" for LA County)
            apn: Assessor's Parcel Number
            
        Returns:
            PropertyData with all available property information
        """
        await self._ensure_initialized()
        
        params = {
            "fips": fips,
            "apn": apn,
            "feedId": self.config.feed_id,
            "options": "search_exclude_nonres=Y",
            "clientReference": f"trendy_{int(time.time())}"
        }
        
        logger.info(f"SiteX APN search: FIPS={fips}, APN={apn}")
        
        response = await self._make_request(params)
        return self._parse_response(response)
    
    # -------------------------------------------------------------------------
    # INTERNAL METHODS
    # -------------------------------------------------------------------------
    
    async def _ensure_initialized(self):
        """Ensure client is initialized"""
        if not self._initialized:
            await self.initialize()
    
    async def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Make authenticated request to SiteX API"""
        token = await self._token_manager.get_token()
        
        try:
            response = await self._client.get(
                self.config.search_url,
                params=params,
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Token might have expired, try once more with fresh token
                logger.warning("SiteX 401, refreshing token and retrying...")
                self._token_manager._token = None
                token = await self._token_manager.get_token()
                
                response = await self._client.get(
                    self.config.search_url,
                    params=params,
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                return response.json()
            raise SiteXError(f"SiteX API error: {e}")
            
        except httpx.HTTPError as e:
            logger.error(f"SiteX request failed: {e}")
            raise SiteXError(f"SiteX request failed: {e}")
    
    def _parse_response(self, response: Dict[str, Any]) -> PropertyData:
        """
        Parse SiteX API response into PropertyData.
        
        CRITICAL FIELD MAPPINGS (from DeedPro Phase 16-19 discoveries):
        - Legal description: Feed.PropertyProfile.LegalDescriptionInfo.LegalBriefDescription
        - County: Feed.PropertyProfile.CountyName OR SiteCountyName  
        - Owner: Feed.PropertyProfile.OwnerInformation.OwnerFullName
        - APN: Feed.PropertyProfile.APN OR PropertyAddress.APNFormatted
        """
        # Check for locations (multi-match scenario)
        locations = response.get("Locations", [])
        
        # Check for feed data
        feed = response.get("Feed", {})
        profile = feed.get("PropertyProfile", {})
        
        if not profile:
            # No direct feed data - check if we have locations
            if locations:
                if len(locations) == 1:
                    # Single match but no feed - this shouldn't happen with feedId
                    logger.warning("Single location match but no Feed data")
                    loc = locations[0]
                    return PropertyData(
                        full_address=f"{loc.get('Address', '')}, {loc.get('City', '')}, {loc.get('State', '')} {loc.get('ZIP', '')}",
                        street=loc.get("Address", ""),
                        city=loc.get("City", ""),
                        state=loc.get("State", "CA"),
                        zip_code=loc.get("ZIP", ""),
                        apn=loc.get("APN", ""),
                        fips=loc.get("FIPS", ""),
                        source="sitex",
                        raw_response=response
                    )
                else:
                    # Multiple matches
                    parsed_locations = [
                        SiteXLocation(
                            fips=loc.get("FIPS", ""),
                            apn=loc.get("APN", ""),
                            address=loc.get("Address", ""),
                            city=loc.get("City", ""),
                            state=loc.get("State", ""),
                            zip_code=loc.get("ZIP", "")
                        )
                        for loc in locations
                    ]
                    raise SiteXMultiMatchError(
                        f"Multiple properties found ({len(locations)} matches). Use APN search for precision.",
                        locations=parsed_locations
                    )
            else:
                raise SiteXNotFoundError("No property found for the given address")
        
        # Extract from PropertyProfile
        # Note: Some feeds use nested objects (PropertyAddress, OwnerInformation)
        # while others use flat fields (SiteAddress, PrimaryOwnerName)
        prop_address = profile.get("PropertyAddress", {}) or {}
        owner_info = profile.get("OwnerInformation", {}) or {}
        characteristics = profile.get("PropertyCharacteristics", {}) or {}
        legal_info = profile.get("LegalDescriptionInfo", {}) or {}
        tax_info = profile.get("AssessmentTaxInfo", {}) or {}
        
        # Build address - prefer direct Site* fields, fall back to nested PropertyAddress
        street = profile.get("SiteAddress", "") or prop_address.get("StreetAddress", "")
        city = profile.get("SiteCity", "") or prop_address.get("City", "")
        state = profile.get("SiteState", "") or prop_address.get("State", "CA")
        zip_code = profile.get("SiteZip", "") or prop_address.get("ZIP", "")
        
        # Build full address from components or use pre-formatted
        full_address = profile.get("SiteAddressCityState", "") or prop_address.get("FullAddress", "")
        if not full_address and street:
            full_address = f"{street}, {city}, {state} {zip_code}".strip()
        
        # CRITICAL: Correct field mappings based on actual API response
        return PropertyData(
            # Address
            full_address=full_address,
            street=street,
            city=city,
            state=state,
            zip_code=zip_code,
            
            # County
            county=profile.get("CountyName", "") or profile.get("SiteCountyName", ""),
            
            # Identifiers - APN can be in multiple places
            apn=profile.get("APN", "") or prop_address.get("APNFormatted", "") or prop_address.get("APN", ""),
            fips=profile.get("FIPS", "") or (locations[0].get("FIPS", "") if locations else ""),
            
            # Owner - check PrimaryOwnerName first (flat), then OwnerInformation (nested)
            owner_name=profile.get("PrimaryOwnerName", "") or owner_info.get("OwnerFullName", "") or owner_info.get("Owner1FullName", ""),
            secondary_owner=owner_info.get("Owner2FullName"),
            
            # Legal description - nested in LegalDescriptionInfo
            legal_description=legal_info.get("LegalBriefDescription", "") if legal_info else "",
            
            # Property characteristics
            bedrooms=self._safe_int(characteristics.get("Bedrooms")),
            bathrooms=self._safe_float(characteristics.get("Baths") or characteristics.get("Bathrooms")),
            sqft=self._safe_int(characteristics.get("BuildingArea") or characteristics.get("LivingArea")),
            lot_size=self._safe_int(characteristics.get("LotSize") or characteristics.get("LotSizeSqFt")),
            year_built=self._safe_int(characteristics.get("YearBuilt")),
            property_type=characteristics.get("UseCode", "") or characteristics.get("PropertyType", ""),
            
            # Tax/Assessment
            assessed_value=self._safe_int(tax_info.get("AssessedValue")),
            tax_amount=self._safe_float(tax_info.get("TaxAmount")),
            land_value=self._safe_int(tax_info.get("LandValue")),
            improvement_value=self._safe_int(tax_info.get("ImprovementValue")),
            tax_year=self._safe_int(tax_info.get("TaxYear")),
            
            # Location coordinates (if available)
            latitude=self._safe_float(profile.get("Latitude") or prop_address.get("Latitude")),
            longitude=self._safe_float(profile.get("Longitude") or prop_address.get("Longitude")),
            
            # Metadata
            source="sitex",
            confidence=0.95,
            raw_response=response
        )
    
    def _parse_address_parts(self, full_address: str, profile: Dict) -> tuple:
        """Parse address into components"""
        # Try to get from profile first
        street = profile.get("SiteAddress", "") or profile.get("PropertyAddress", {}).get("StreetAddress", "")
        city = profile.get("SiteCity", "") or profile.get("PropertyAddress", {}).get("City", "")
        state = profile.get("SiteState", "") or profile.get("PropertyAddress", {}).get("State", "CA")
        zip_code = profile.get("SiteZip", "") or profile.get("PropertyAddress", {}).get("ZIP", "")
        
        # Fall back to parsing full address
        if not street and full_address:
            parts = full_address.split(",")
            if len(parts) >= 1:
                street = parts[0].strip()
            if len(parts) >= 2:
                city = parts[1].strip()
            if len(parts) >= 3:
                state_zip = parts[2].strip().split()
                if len(state_zip) >= 1:
                    state = state_zip[0]
                if len(state_zip) >= 2:
                    zip_code = state_zip[1]
        
        return street, city, state, zip_code
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert to int"""
        if value is None or value == "":
            return None
        try:
            # Handle string numbers with commas
            if isinstance(value, str):
                value = value.replace(",", "").strip()
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert to float"""
        if value is None or value == "":
            return None
        try:
            if isinstance(value, str):
                value = value.replace(",", "").strip()
            return float(value)
        except (ValueError, TypeError):
            return None


# =============================================================================
# CACHING LAYER
# =============================================================================

# Simple in-memory cache (use Redis in production)
_property_cache: Dict[str, tuple] = {}  # key -> (PropertyData, expiry_timestamp)
CACHE_VERSION = "v3"
CACHE_TTL_HOURS = 24


def _get_cache_key(address: str, city_state_zip: str = "") -> str:
    """Generate cache key"""
    normalized = f"{address.lower().strip()}|{city_state_zip.lower().strip()}"
    hash_key = hashlib.md5(normalized.encode()).hexdigest()[:16]
    return f"{CACHE_VERSION}:{hash_key}"


def _get_cached(key: str) -> Optional[PropertyData]:
    """Get from cache if not expired"""
    if key in _property_cache:
        data, expiry = _property_cache[key]
        if time.time() < expiry:
            logger.debug(f"Cache hit: {key}")
            return data
        else:
            del _property_cache[key]
    return None


def _set_cache(key: str, data: PropertyData):
    """Set cache with TTL"""
    expiry = time.time() + (CACHE_TTL_HOURS * 3600)
    _property_cache[key] = (data, expiry)
    logger.debug(f"Cached: {key}")


# =============================================================================
# PUBLIC API
# =============================================================================

# Singleton client instance
_client: Optional[SiteXClient] = None


async def get_sitex_client() -> SiteXClient:
    """Get or create SiteX client singleton"""
    global _client
    if _client is None:
        _client = SiteXClient()
        await _client.initialize()
    return _client


async def lookup_property(
    address: str,
    city_state_zip: str = "",
    use_cache: bool = True
) -> Optional[PropertyData]:
    """
    Main entry point for property lookup.
    
    Args:
        address: Full address or just street address
        city_state_zip: City, State ZIP (can be empty if included in address)
        use_cache: Whether to use cache (default True)
        
    Returns:
        PropertyData or None if not found
        
    Example:
        # Option 1: Full address in one string
        data = await lookup_property("714 Vine St, Anaheim, CA 92805")
        
        # Option 2: Split address
        data = await lookup_property("714 Vine St", "Anaheim, CA 92805")
    """
    # Parse address if city_state_zip not provided
    if not city_state_zip and "," in address:
        parts = address.split(",", 1)
        address = parts[0].strip()
        city_state_zip = parts[1].strip() if len(parts) > 1 else ""
    
    # Check cache
    cache_key = _get_cache_key(address, city_state_zip)
    if use_cache:
        cached = _get_cached(cache_key)
        if cached:
            return cached
    
    # Lookup via SiteX
    try:
        client = await get_sitex_client()
        data = await client.search_by_address(address, city_state_zip)
        
        # Cache successful result
        _set_cache(cache_key, data)
        
        logger.info(f"SiteX lookup successful: {address}")
        return data
        
    except SiteXNotFoundError:
        logger.warning(f"Property not found: {address}, {city_state_zip}")
        return None
        
    except SiteXMultiMatchError as e:
        logger.warning(f"Multiple matches for: {address}. Returning first match.")
        # For now, return None - caller can handle multi-match if needed
        # In UI, you might want to show a picker
        return None
        
    except SiteXError as e:
        logger.error(f"SiteX error: {e}")
        return None


async def lookup_property_by_apn(fips: str, apn: str) -> Optional[PropertyData]:
    """
    Lookup property by FIPS and APN (most precise).
    
    Args:
        fips: 5-digit county FIPS code
        apn: Assessor's Parcel Number
        
    Returns:
        PropertyData or None
    """
    cache_key = f"{CACHE_VERSION}:apn:{fips}:{apn}"
    
    cached = _get_cached(cache_key)
    if cached:
        return cached
    
    try:
        client = await get_sitex_client()
        data = await client.search_by_apn(fips, apn)
        _set_cache(cache_key, data)
        return data
        
    except SiteXError as e:
        logger.error(f"SiteX APN lookup error: {e}")
        return None


# =============================================================================
# CLEANUP
# =============================================================================

async def shutdown():
    """Cleanup on application shutdown"""
    global _client
    if _client:
        await _client.close()
        _client = None
