# SiteX Pro Integration

## Overview

SiteX Pro provides property detail data and comparable property search for property reports (CMAs).

## Service Details

- **Used by:** API service (`services/sitex.py`)
- **Auth method:** OAuth2 with automatic token refresh
- **Capabilities:**
  - Property detail lookup by address or APN
  - Comparable property search with configurable radius and filters

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SITEX_CLIENT_ID` | OAuth2 client ID |
| `SITEX_CLIENT_SECRET` | OAuth2 client secret |
| `SITEX_BASE_URL` | Base URL for the SiteX Pro API |

## Key Behaviors

- OAuth2 tokens are automatically refreshed when expired
- Property details include full property characteristics, tax data, and ownership info
- Comparable search returns similar properties based on proximity, size, and features
- Used in the property report generation flow for subject property data and comp selection
