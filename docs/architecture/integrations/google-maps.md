# Google Maps Integration

## Overview

Google Maps provides address autocomplete on the frontend and static map image generation in the worker.

## Service Details

- **Used by:**
  - **Frontend:** Places Autocomplete via `useGooglePlaces` hook
  - **Worker:** Static Maps API for property report images (aerial views, comp location maps)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` | Frontend API key (exposed to browser) |
| `GOOGLE_MAPS_API_KEY` | Worker API key (server-side only) |

## Frontend Usage

- The `useGooglePlaces` React hook integrates Google Places Autocomplete
- Used in property search inputs throughout the report builder and CMA flows
- Returns structured address components (street, city, state, zip)

## Worker Usage

- Static Maps API generates map images embedded in property reports
- Aerial/satellite views of the subject property
- Comp location maps showing subject and comparable properties with markers
- Generated images are uploaded to R2 for inclusion in PDFs
