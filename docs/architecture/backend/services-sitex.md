# SiteX Pro Integration

> OAuth2-authenticated property data API for address lookup and APN search.
> File: `apps/api/src/api/services/sitex.py`

## Overview

SiteX Pro (ICE) provides comprehensive property data including:
- Address and owner information
- Property characteristics (beds, baths, sqft, year built)
- Tax/assessment data
- Legal descriptions
- APN and FIPS codes
- Geocoding (lat/lng)

## Architecture

```
sitex.py
  ├── SiteXConfig          # Configuration from env vars
  ├── SiteXTokenManager    # OAuth2 token lifecycle
  ├── SiteXClient          # API client (singleton)
  ├── PropertyData          # Pydantic response model
  └── Public Functions
      ├── lookup_property()        # Search by address
      └── lookup_property_by_apn() # Search by FIPS + APN
```

## OAuth2 Token Management

- **Flow:** Client credentials grant
- **Token URL:** `{base_url}/ls/apigwy/oauth2/v1/token`
- **Token TTL:** 10 minutes
- **Refresh strategy:** Refresh at 9 minutes (1 minute buffer)
- **Thread safety:** asyncio Lock prevents concurrent token refreshes

### Environment Variables

| Variable | Description |
|----------|-------------|
| `SITEX_BASE_URL` | API gateway URL (UAT or Prod) |
| `SITEX_CLIENT_ID` | OAuth2 client ID |
| `SITEX_CLIENT_SECRET` | OAuth2 client secret |
| `SITEX_FEED_ID` | Feed identifier (e.g., 100001) |

## Key Functions

### lookup_property(address, city_state_zip, use_cache=True)
- Main entry point for property lookup
- Parses address if city_state_zip not provided (splits on first comma)
- Checks in-memory cache first (24 hour TTL, MD5 key)
- Returns `PropertyData` or None
- Handles `SiteXMultiMatchError` silently (returns None)

### lookup_property_by_apn(fips, apn)
- Most precise search method
- Caches by `apn:{fips}:{apn}` key
- Returns `PropertyData` or None

### SiteXClient.search_by_address(address, city_state_zip, owner)
- Sends GET to `/realestatedata/search`
- Params: addr, lastLine, feedId, options=search_exclude_nonres
- Auto-retries once on 401 (token refresh)

### SiteXClient._parse_response(response)
- Handles three scenarios:
  1. **Single match with Feed data:** Parses PropertyProfile
  2. **Multiple matches (Locations):** Raises `SiteXMultiMatchError` with location list
  3. **No match:** Raises `SiteXNotFoundError`

**Critical field mappings:**
- Legal description: `Feed.PropertyProfile.LegalDescriptionInfo.LegalBriefDescription`
- County: `Feed.PropertyProfile.CountyName` or `SiteCountyName`
- Owner: `Feed.PropertyProfile.OwnerInformation.OwnerFullName`
- APN: `Feed.PropertyProfile.APN` or `PropertyAddress.APNFormatted`

## Caching

Simple in-memory dict cache (not Redis):
- Key: MD5 hash of normalized address
- TTL: 24 hours
- Version prefix for cache invalidation (`v3:`)

## Error Types

| Exception | Meaning |
|-----------|---------|
| `SiteXError` | Base exception |
| `SiteXAuthError` | OAuth2 token failure |
| `SiteXNotFoundError` | Property not found |
| `SiteXMultiMatchError` | Multiple properties match (contains location list) |

## Callers
- `routes/property.py`: search, search-by-apn endpoints
- `routes/lead_pages.py`: consumer CMA property search
