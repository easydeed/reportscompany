# SimplyRETS Integration

## Overview

SimplyRETS provides MLS (Multiple Listing Service) listing data for market report generation.

## Service Details

- **Used by:** Worker service (`vendors/simplyrets.py`)
- **Auth method:** Basic Auth (username/password)
- **Rate limiting:** 60 RPM + 10 burst (token bucket algorithm)
- **Pagination:** GET `/properties` with 500 results per page, max 1000 results
- **Retry policy:** 3 attempts with exponential backoff on 429 (rate limit) and 5xx (server error) responses

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SIMPLYRETS_BASE_URL` | Base URL for the SimplyRETS API |
| `SIMPLYRETS_USERNAME` | Basic Auth username |
| `SIMPLYRETS_PASSWORD` | Basic Auth password |
| `SIMPLYRETS_RPM` | Requests per minute limit (default: 60) |
| `SIMPLYRETS_BURST` | Burst request allowance (default: 10) |
| `SIMPLYRETS_TIMEOUT_S` | Request timeout in seconds |
| `SIMPLYRETS_MAX_RESULTS` | Maximum results to fetch (default: 1000) |

## Key Behaviors

- Token bucket rate limiter prevents exceeding API quotas
- Elastic widening: if initial query returns too few results, filters are progressively relaxed
- Market-adaptive filters adjust search parameters based on area characteristics
- All data is fetched during the worker report generation pipeline
