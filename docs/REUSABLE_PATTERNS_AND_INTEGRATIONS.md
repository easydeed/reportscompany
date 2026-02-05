# Reusable Patterns and Integrations

> **Last Updated:** January 28, 2026  
> **Purpose:** Comprehensive documentation of all reusable patterns, integrations, and components in the TrendyReports codebase.

---

## Table of Contents

1. [Tier 1: External API Integrations](#tier-1-external-api-integrations)
   - [SiteX MLS Property Data Client](#1-sitex-mls-property-data-client)
   - [SimplyRETS MLS API Client](#2-simplyrets-mls-api-client)
   - [Twilio SMS Service](#3-twilio-sms-service)
   - [SendGrid Email Provider](#4-sendgrid-email-provider)
   - [Stripe Billing Integration](#5-stripe-billing-integration)
   - [Cloudflare R2 Storage Service](#6-cloudflare-r2-storage-service)
   - [OpenAI AI Insights Generator](#7-openai-ai-insights-generator)
   - [Google Maps Places Autocomplete](#8-google-maps-places-autocomplete)
2. [Tier 2: Document Generation](#tier-2-document-generation)
   - [PDF Engine (Multi-Backend)](#9-pdf-engine-multi-backend)
   - [Social Media Image Generator](#10-social-media-image-generator)
   - [QR Code Service](#11-qr-code-service)
   - [Email Template Engine](#12-email-template-engine)
3. [Tier 3: Infrastructure Patterns](#tier-3-infrastructure-patterns)
   - [Authentication Middleware](#13-authentication-middleware)
   - [Rate Limiting Middleware](#14-rate-limiting-middleware)
   - [Redis Caching Layer](#15-redis-caching-layer)
   - [Scheduled Task Ticker](#16-scheduled-task-ticker)
4. [Tier 4: Frontend Utilities](#tier-4-frontend-utilities)
   - [API Fetch with Proxy & Retry](#17-api-fetch-with-proxy--retry)
   - [Toast Notification System](#18-toast-notification-system)
   - [Market Metrics Calculator](#19-market-metrics-calculator)
5. [Tier 5: Reusable UI Components](#tier-5-reusable-ui-components)
   - [DataTable Component](#20-datatable-component)
   - [HorizontalStepper Component](#21-horizontalstepper-component)
   - [TimePicker Component](#22-timepicker-component)
   - [CadencePicker Component](#23-cadencepicker-component)
   - [CityAutocomplete Component](#24-cityautocomplete-component)

---

## Tier 1: External API Integrations

### 1. SiteX MLS Property Data Client

**Location:** `apps/api/src/api/services/sitex.py`

**Purpose:** OAuth2-authenticated client for fetching detailed property data from the SiteX MLS API.

**Key Features:**
- OAuth2 token management with automatic refresh
- Property search by address or APN (Assessor's Parcel Number)
- Response parsing into Pydantic `PropertyData` model
- Simple in-memory caching layer
- Async/await support

**Public API:**

```python
from api.services.sitex import lookup_property, PropertyData

# Main entry point with automatic caching
async def lookup_property(
    address: str, 
    city_state_zip: str = "", 
    use_cache: bool = True
) -> Optional[PropertyData]:
    """
    Look up property data by address.
    
    Args:
        address: Street address (e.g., "123 Main St")
        city_state_zip: City, state, and ZIP (e.g., "Los Angeles, CA 90001")
        use_cache: Whether to use cached results (default: True)
    
    Returns:
        PropertyData object or None if not found
    """
```

**Configuration (Environment Variables):**

| Variable | Description | Required |
|----------|-------------|----------|
| `SITEX_CLIENT_ID` | OAuth2 client ID | Yes |
| `SITEX_CLIENT_SECRET` | OAuth2 client secret | Yes |
| `SITEX_FEED_ID` | MLS feed identifier | Yes |
| `SITEX_BASE_URL` | API base URL | Yes |

**Usage Example:**

```python
# In an async route handler
property_data = await lookup_property(
    address="123 Main Street",
    city_state_zip="Los Angeles, CA 90001"
)

if property_data:
    print(f"Property: {property_data.address}")
    print(f"Bedrooms: {property_data.bedrooms}")
    print(f"Value: ${property_data.estimated_value:,}")
```

---

### 2. SimplyRETS MLS API Client

**Location:** `apps/api/src/api/services/simplyrets.py`

**Purpose:** Synchronous Python client for fetching MLS listings with rate limiting, pagination, and retry logic.

**Key Features:**
- HTTP Basic authentication
- Token-bucket rate limiter (configurable RPM)
- Automatic pagination for large result sets
- Exponential backoff retry logic
- Response normalization to consistent format

**Public API:**

```python
from api.services.simplyrets import fetch_properties, normalize_listing

def fetch_properties(
    params: Dict, 
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Fetch properties with automatic pagination and rate limiting.
    
    Args:
        params: Query parameters (status, city, type, etc.)
        limit: Maximum number of results (default: no limit)
    
    Returns:
        List of raw property dictionaries
    """

def normalize_listing(listing: Dict) -> Dict:
    """
    Normalize SimplyRETS response to consistent format.
    
    Returns:
        Normalized dictionary with standardized keys
    """
```

**Rate Limiter Class:**

```python
class RateLimiter:
    """Token-bucket rate limiter with minute window."""
    
    def __init__(self, rpm: int = 60, burst: int = 10):
        """
        Args:
            rpm: Requests per minute limit
            burst: Maximum burst capacity
        """
    
    def acquire(self):
        """Block until a request slot is available."""
```

**Configuration (Environment Variables):**

| Variable | Description | Required |
|----------|-------------|----------|
| `SIMPLYRETS_USERNAME` | API username | Yes |
| `SIMPLYRETS_PASSWORD` | API password | Yes |
| `SIMPLYRETS_BASE_URL` | API base URL (default: `https://api.simplyrets.com`) | No |

**Usage Example:**

```python
# Fetch active listings in a city
listings = fetch_properties({
    "status": "active",
    "cities": "Los Angeles",
    "type": "residential",
    "minprice": 500000,
    "maxprice": 1500000
}, limit=100)

# Normalize for consistent processing
normalized = [normalize_listing(l) for l in listings]
```

---

### 3. Twilio SMS Service

**Location:** `apps/api/src/api/services/twilio_sms.py`

**Purpose:** Async HTTP-based client for sending SMS messages via Twilio REST API (no SDK dependency).

**Key Features:**
- Async/await support with `httpx`
- E.164 phone number formatting/validation
- No Twilio SDK dependency (direct REST calls)
- Graceful configuration checking

**Public API:**

```python
from api.services.twilio_sms import send_sms, format_phone_e164, is_configured

async def send_sms(to_phone: str, message: str) -> dict:
    """
    Send SMS via Twilio REST API.
    
    Args:
        to_phone: Recipient phone in E.164 format (+1XXXXXXXXXX)
        message: SMS message body
    
    Returns:
        {"message_sid": "...", "status": "sent"}
    
    Raises:
        TwilioSMSError: If not configured or API error
    """

def format_phone_e164(
    phone: str, 
    default_country: str = "1"
) -> Optional[str]:
    """
    Format phone number to E.164 format.
    
    Args:
        phone: Raw phone number (various formats accepted)
        default_country: Country code if not provided (default: "1" for US)
    
    Returns:
        Formatted phone (+1XXXXXXXXXX) or None if invalid
    """

def is_configured() -> bool:
    """Check if Twilio credentials are configured."""
```

**Configuration (Environment Variables):**

| Variable | Description | Required |
|----------|-------------|----------|
| `TWILIO_ACCOUNT_SID` | Twilio account SID | Yes |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | Yes |
| `TWILIO_PHONE_NUMBER` | Sender phone number (E.164) | Yes |

**Usage Example:**

```python
# Format and send SMS
phone = format_phone_e164("(555) 123-4567")  # Returns "+15551234567"

if phone and is_configured():
    result = await send_sms(
        to_phone=phone,
        message="Your market report is ready! View it here: https://..."
    )
    print(f"Sent: {result['message_sid']}")
```

---

### 4. SendGrid Email Provider

**Location:** `apps/worker/src/worker/email/providers/sendgrid.py`

**Purpose:** Synchronous email sending via SendGrid v3 API with retry logic for transient failures.

**Key Features:**
- Exponential backoff retry (3 attempts)
- Retryable status code handling (429, 5xx)
- HTML content support
- Configurable from name/email

**Public API:**

```python
from worker.email.providers.sendgrid import send_email, is_configured

def send_email(
    to_emails: List[str],
    subject: str,
    html_content: str,
    from_name: str = None,
    from_email: str = None
) -> Tuple[int, str]:
    """
    Send email with retry logic for transient failures.
    
    Args:
        to_emails: List of recipient email addresses
        subject: Email subject line
        html_content: HTML body content
        from_name: Sender display name (optional)
        from_email: Sender email address (optional)
    
    Returns:
        Tuple of (status_code, message)
        - (202, "Email sent successfully") on success
        - (status_code, error_message) on failure
    """
```

**Configuration (Environment Variables):**

| Variable | Description | Required |
|----------|-------------|----------|
| `SENDGRID_API_KEY` | SendGrid API key | Yes |
| `SENDGRID_FROM_EMAIL` | Default sender email | Yes |
| `SENDGRID_FROM_NAME` | Default sender name | No |

**Retry Configuration:**

| Constant | Value | Description |
|----------|-------|-------------|
| `MAX_RETRIES` | 3 | Maximum retry attempts |
| `RETRY_DELAY_BASE` | 2.0 | Base delay in seconds |
| `RETRYABLE_STATUS_CODES` | {429, 500, 502, 503, 504} | Status codes to retry |

**Usage Example:**

```python
status, message = send_email(
    to_emails=["user@example.com"],
    subject="Your Weekly Market Report",
    html_content=rendered_html,
    from_name="TrendyReports"
)

if status == 202:
    print("Email sent successfully")
else:
    print(f"Failed: {message}")
```

---

### 5. Stripe Billing Integration

**Location:** 
- Routes: `apps/api/src/api/routes/billing.py`
- Webhooks: `apps/api/src/api/routes/stripe_webhook.py`
- Config: `apps/api/src/api/config/billing.py`

**Purpose:** Complete Stripe integration for subscription billing, including checkout sessions, customer portal, and webhook handling.

**Key Features:**
- Checkout session creation for plan upgrades
- Customer portal access for subscription management
- Webhook processing for subscription lifecycle events
- Plan slug ↔ Stripe Price ID mapping
- Automatic customer creation

**Configuration Module:**

```python
# apps/api/src/api/config/billing.py

# Map internal plan_slug → Stripe Price ID
STRIPE_PRICE_MAP = {
    "pro": os.getenv("STRIPE_PRICE_PRO_MONTH"),
    "team": os.getenv("STRIPE_PRICE_TEAM_MONTH"),
}

def get_stripe_price_for_plan(plan_slug: str) -> Optional[str]:
    """Get Stripe Price ID for a plan slug."""

def get_plan_for_stripe_price(price_id: str) -> Optional[str]:
    """Get plan slug for a Stripe Price ID."""
```

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/billing/checkout` | POST | Create Stripe checkout session |
| `/v1/billing/portal` | POST | Create customer portal session |
| `/webhooks/stripe` | POST | Handle Stripe webhook events |

**Webhook Events Handled:**

| Event | Action |
|-------|--------|
| `customer.subscription.created` | Update account plan |
| `customer.subscription.updated` | Update account plan |
| `customer.subscription.deleted` | Downgrade to free |

**Configuration (Environment Variables):**

| Variable | Description | Required |
|----------|-------------|----------|
| `STRIPE_SECRET_KEY` | Stripe API secret key | Yes |
| `STRIPE_WEBHOOK_SECRET` | Webhook signing secret | Yes |
| `STRIPE_PRICE_PRO_MONTH` | Pro plan price ID | Yes |
| `STRIPE_PRICE_TEAM_MONTH` | Team plan price ID | Yes |

**Usage Example:**

```python
# Create checkout session
@router.post("/checkout")
def create_checkout_session(body: CheckoutRequest, account_id: str = Depends(require_account_id)):
    price_id = get_stripe_price_for_plan(body.plan_slug)
    
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=stripe_customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{WEB_BASE}/account/plan?checkout=success",
        cancel_url=f"{WEB_BASE}/account/plan?checkout=cancel",
    )
    return {"url": session.url}
```

---

### 6. Cloudflare R2 Storage Service

**Location:** `apps/api/src/api/services/upload.py`

**Purpose:** Upload and manage branding assets (images) in Cloudflare R2 (S3-compatible object storage).

**Key Features:**
- S3-compatible API via `boto3`
- Image validation (type, size, dimensions)
- Public URL generation
- Long-term caching headers
- Unique filename generation

**Public API:**

```python
from api.services.upload import upload_branding_asset, validate_image, get_r2_client

async def upload_branding_asset(
    file: UploadFile,
    account_id: str,
    asset_type: str
) -> dict:
    """
    Upload image to R2 and return public URL.
    
    Args:
        file: FastAPI UploadFile object
        account_id: Owner account ID
        asset_type: Type identifier (e.g., "logo", "headshot")
    
    Returns:
        {"url": "https://...", "filename": "original.png"}
    
    Raises:
        HTTPException: If validation fails
    """

async def validate_image(file: UploadFile) -> bytes:
    """
    Validate uploaded image file.
    
    Checks:
        - Content type (png, jpeg, webp, gif)
        - File size (max 5MB)
        - Dimensions (min 100x100)
    
    Returns:
        File contents as bytes
    """
```

**Configuration (Environment Variables):**

| Variable | Description | Required |
|----------|-------------|----------|
| `R2_ACCOUNT_ID` | Cloudflare account ID | Yes |
| `R2_ACCESS_KEY_ID` | R2 access key | Yes |
| `R2_SECRET_ACCESS_KEY` | R2 secret key | Yes |
| `R2_BUCKET_NAME` | Bucket name | Yes |
| `R2_PUBLIC_URL` | Public CDN URL | Yes |

**Usage Example:**

```python
@router.post("/branding/logo")
async def upload_logo(
    file: UploadFile,
    account_id: str = Depends(require_account_id)
):
    result = await upload_branding_asset(
        file=file,
        account_id=account_id,
        asset_type="logo"
    )
    return {"logo_url": result["url"]}
```

---

### 7. OpenAI AI Insights Generator

**Location:** `apps/worker/src/worker/ai_insights.py`

**Purpose:** Generate AI-powered market insight paragraphs using OpenAI GPT models with sender/audience-aware prompting.

**Key Features:**
- Sender-aware prompts (agent vs affiliate tone)
- Audience-aware context (listing curation details)
- Configurable model and temperature
- Graceful fallback when disabled

**Public API:**

```python
from worker.ai_insights import generate_insight

def generate_insight(
    report_type: str,
    area: str,
    metrics: Dict,
    lookback_days: int = 30,
    filter_description: Optional[str] = None,
    sender_type: str = "REGULAR",
    total_found: int = 0,
    total_shown: int = 0,
    audience_name: Optional[str] = None,
) -> Optional[str]:
    """
    Generate an AI-powered market insight blurb.
    
    Args:
        report_type: Type of report (market_snapshot, new_listings, etc.)
        area: Geographic area (city, ZIP codes)
        metrics: Market metrics dictionary
        lookback_days: Report time period
        filter_description: Optional filter applied
        sender_type: "REGULAR" (agent) or "AFFILIATE"
        total_found: Total listings found
        total_shown: Total listings shown (after curation)
        audience_name: Name of target audience
    
    Returns:
        Generated insight paragraph or None if disabled/error
    """
```

**System Prompts:**

| Sender Type | Tone |
|-------------|------|
| `REGULAR` (Agent) | Warm, personable, client-focused |
| `AFFILIATE` | Professional, analytical, informative |

**Configuration (Environment Variables):**

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `AI_INSIGHTS_ENABLED` | Enable/disable feature ("true"/"false") | No |

**Usage Example:**

```python
insight = generate_insight(
    report_type="new_listings_gallery",
    area="Beverly Hills, CA",
    metrics={"total_new": 42, "median_price": 2500000},
    lookback_days=7,
    sender_type="REGULAR",
    total_found=100,
    total_shown=20,
    audience_name="Luxury Home Buyers"
)

if insight:
    print(insight)
    # "Exciting news! 42 stunning new properties just hit the market..."
```

---

### 8. Google Maps Places Autocomplete

**Location:** `apps/web/hooks/useGooglePlaces.ts`

**Purpose:** React hook for integrating Google Places Autocomplete into address input fields.

**Key Features:**
- Automatic Google Maps API loading detection
- Address component parsing into structured result
- Country restriction support
- Lat/lng coordinates extraction
- Cleanup on unmount

**Public API:**

```typescript
import { useGooglePlaces, PlaceResult } from '@/hooks/useGooglePlaces';

interface PlaceResult {
  streetNumber: string;
  street: string;
  address: string;      // Full street address
  city: string;
  state: string;
  zip: string;
  county: string;
  fullAddress: string;  // Formatted address from Google
  lat?: number;
  lng?: number;
}

interface UseGooglePlacesOptions {
  onPlaceSelect?: (place: PlaceResult) => void;
  countryRestriction?: string;  // Default: "us"
}

function useGooglePlaces(
  inputRef: React.RefObject<HTMLInputElement | null>,
  options?: UseGooglePlacesOptions
): {
  place: PlaceResult | null;
  isLoaded: boolean;
  error: Error | null;
  reset: () => void;
}
```

**Configuration:**

Requires Google Maps JavaScript API loaded with Places library:

```html
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_KEY&libraries=places"></script>
```

Or via `@react-google-maps/api` loader.

**Usage Example:**

```tsx
function AddressInput() {
  const inputRef = useRef<HTMLInputElement>(null);
  const { place, isLoaded, reset } = useGooglePlaces(inputRef, {
    onPlaceSelect: (result) => {
      console.log('Selected:', result.fullAddress);
      console.log('City:', result.city);
      console.log('Coordinates:', result.lat, result.lng);
    },
    countryRestriction: 'us'
  });

  return (
    <div>
      <input 
        ref={inputRef} 
        type="text" 
        placeholder="Enter address..."
        disabled={!isLoaded}
      />
      {place && (
        <p>Selected: {place.city}, {place.state} {place.zip}</p>
      )}
    </div>
  );
}
```

---

## Tier 2: Document Generation

### 9. PDF Engine (Multi-Backend)

**Location:** `apps/worker/src/worker/pdf_engine.py`

**Purpose:** Abstraction layer for PDF generation supporting multiple rendering backends.

**Key Features:**
- Local Playwright/Chromium rendering
- Cloud-based PDFShift API
- Configurable engine selection
- URL or HTML content input
- Letter format with configurable margins

**Public API:**

```python
from worker.pdf_engine import render_pdf, render_pdf_playwright, render_pdf_pdfshift

def render_pdf(
    run_id: str,
    account_id: str,
    html_content: Optional[str] = None,
    print_base: Optional[str] = None
) -> Tuple[str, str]:
    """
    Render PDF using the configured engine.
    
    Args:
        run_id: Unique report run identifier
        account_id: Owner account ID
        html_content: Optional HTML string (if None, fetches from URL)
        print_base: Base URL for print endpoint
    
    Returns:
        Tuple of (pdf_file_path, source_url)
    """
```

**Backend Selection:**

| Engine | Use Case | Pros | Cons |
|--------|----------|------|------|
| `playwright` | Local/self-hosted | Free, no external deps | Requires Chromium |
| `pdfshift` | Cloud/serverless | No browser needed | API costs |

**Configuration (Environment Variables):**

| Variable | Description | Required |
|----------|-------------|----------|
| `PDF_ENGINE` | Engine to use ("playwright" or "pdfshift") | Yes |
| `PDFSHIFT_API_KEY` | PDFShift API key (if using pdfshift) | Conditional |
| `PDF_DIR` | Output directory for PDFs | Yes |
| `PRINT_BASE` | Base URL for print endpoints | Yes |

**Usage Example:**

```python
# Generate PDF from report URL
pdf_path, source_url = render_pdf(
    run_id="rpt_abc123",
    account_id="acc_xyz789"
)

print(f"PDF saved to: {pdf_path}")
print(f"Source: {source_url}")
```

---

### 10. Social Media Image Generator

**Location:** `apps/worker/src/worker/social_engine.py`

**Purpose:** Generate social media images (1080x1920 JPEG) using PDFShift screenshot API.

**Key Features:**
- Instagram/Stories optimized dimensions (1080x1920)
- Asset loading delay for complex pages
- JPEG output format

**Public API:**

```python
from worker.social_engine import render_social_image

def render_social_image(
    run_id: str,
    account_id: str,
    print_base: Optional[str] = None
) -> Tuple[str, str]:
    """
    Render social media image (1080x1920 JPEG) using PDFShift.
    
    Args:
        run_id: Unique report run identifier
        account_id: Owner account ID
        print_base: Base URL for social endpoint
    
    Returns:
        Tuple of (jpg_file_path, source_url)
    """
```

**Configuration (Environment Variables):**

| Variable | Description | Required |
|----------|-------------|----------|
| `PDFSHIFT_API_KEY` | PDFShift API key | Yes |
| `SOCIAL_DIR` | Output directory for images | Yes |
| `PRINT_BASE` | Base URL for social endpoints | Yes |

**Usage Example:**

```python
jpg_path, source_url = render_social_image(
    run_id="rpt_abc123",
    account_id="acc_xyz789"
)

# Upload to social media or attach to email
```

---

### 11. QR Code Service

**Location:** `apps/api/src/api/services/qr_service.py`

**Purpose:** Generate styled QR codes with customizable colors and upload to R2 storage.

**Key Features:**
- Rounded module style
- High error correction (H level)
- Custom foreground/background colors
- R2 upload with long-term caching
- Fallback to external QR service

**Public API:**

```python
from api.services.qr_service import generate_qr_code

async def generate_qr_code(
    url: str,
    color: str = "#000000",
    report_id: str = "",
    background: str = "#FFFFFF",
    box_size: int = 10
) -> str:
    """
    Generate QR code and upload to R2, with fallbacks.
    
    Args:
        url: URL to encode in QR code
        color: Foreground color (hex)
        report_id: Unique identifier for filename
        background: Background color (hex)
        box_size: Size of each QR module
    
    Returns:
        Public URL of generated QR code image
    """
```

**Dependencies:**

```
qrcode[pil]
Pillow
```

**Configuration (Environment Variables):**

| Variable | Description | Required |
|----------|-------------|----------|
| `R2_*` | R2 storage credentials | Yes (for upload) |

**Usage Example:**

```python
qr_url = await generate_qr_code(
    url="https://reports.trendy.com/view/rpt_abc123",
    color="#6B46C1",  # Brand purple
    report_id="rpt_abc123"
)

# Use in email or PDF template
print(f"QR Code: {qr_url}")
```

---

### 12. Email Template Engine

**Location:** `apps/worker/src/worker/email/template.py`

**Purpose:** Generate comprehensive HTML emails for scheduled report notifications with full email client compatibility.

**Key Features:**
- Table-based layout (Outlook compatible)
- White-label branding support
- Dark mode support
- Mobile responsive
- Dynamic content sections (metrics, listings, insights)
- AI insights integration

**Public API:**

```python
from worker.email.template import schedule_email_html

def schedule_email_html(
    account_name: str,
    report_type: str,
    city: Optional[str],
    zip_codes: Optional[list],
    lookback_days: int,
    metrics: Dict,
    pdf_url: str,
    unsubscribe_url: str,
    brand: Optional[Brand] = None,
    listings: Optional[List[Dict]] = None,
    preset_display_name: Optional[str] = None,
    filter_description: Optional[str] = None,
    sender_type: str = "REGULAR",
    total_found: int = 0,
    total_shown: int = 0,
    audience_name: Optional[str] = None,
) -> str:
    """
    Generate HTML email for a scheduled report notification.
    
    Args:
        account_name: Sender's display name
        report_type: Type of report
        city: City name (if area type is city)
        zip_codes: List of ZIP codes (if area type is zip)
        lookback_days: Report time period
        metrics: Market metrics dictionary
        pdf_url: Link to PDF download
        unsubscribe_url: Unsubscribe link
        brand: Optional branding configuration
        listings: Optional featured listings
        preset_display_name: Custom report title
        filter_description: Applied filter description
        sender_type: "REGULAR" or "AFFILIATE"
        total_found: Total listings found
        total_shown: Listings shown in report
        audience_name: Target audience name
    
    Returns:
        Complete HTML email string
    """
```

**Usage Example:**

```python
html = schedule_email_html(
    account_name="Jane Realtor",
    report_type="new_listings_gallery",
    city="Beverly Hills",
    zip_codes=None,
    lookback_days=7,
    metrics={"total_new": 42, "median_price": 2500000},
    pdf_url="https://...",
    unsubscribe_url="https://...",
    brand=Brand(primary_color="#6B46C1", logo_url="..."),
    listings=featured_listings[:6],
    sender_type="REGULAR",
    audience_name="Luxury Buyers"
)

send_email(to_emails=recipients, subject="New Listings This Week", html_content=html)
```

---

## Tier 3: Infrastructure Patterns

### 13. Authentication Middleware

**Location:** `apps/api/src/api/middleware/authn.py`

**Purpose:** FastAPI middleware for JWT and API key authentication with public endpoint bypass.

**Key Features:**
- JWT token validation (header or cookie)
- API key authentication
- Token blacklist checking
- Public endpoint bypass list
- User context injection

**Authentication Flow:**

```
1. Check if path is public → bypass
2. Check Authorization: Bearer header
   - Try JWT validation
   - If fails, try API key lookup
3. Check mr_token cookie for JWT
4. Check X-Demo-Account header (demo mode)
5. If no auth → 401 Unauthorized
6. Set request.state.account_id and request.state.user
```

**Public Endpoints (bypass auth):**

```python
PUBLIC_PATHS = [
    "/health",
    "/v1/auth/",
    "/webhooks/",
    "/v1/public/",
    "/docs",
    "/openapi.json",
]
```

**Configuration (Environment Variables):**

| Variable | Description | Required |
|----------|-------------|----------|
| `JWT_SECRET` | Secret for JWT signing/verification | Yes |

**Usage in Routes:**

```python
from api.deps import require_account_id

@router.get("/my-data")
def get_my_data(account_id: str = Depends(require_account_id)):
    # account_id is guaranteed to be set
    return {"account_id": account_id}
```

---

### 14. Rate Limiting Middleware

**Location:** `apps/api/src/api/middleware/authn.py` (same file as auth)

**Purpose:** Redis-based per-account rate limiting with configurable limits.

**Key Features:**
- Minute-bucket sliding window
- Per-account limits (from DB or default)
- Standard rate limit headers
- 429 response on exceeded

**Response Headers:**

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests per minute |
| `X-RateLimit-Remaining` | Remaining requests in window |
| `X-RateLimit-Reset` | Seconds until window resets |

**Configuration (Environment Variables):**

| Variable | Description | Required |
|----------|-------------|----------|
| `REDIS_URL` | Redis connection URL | Yes |

**Default Limits:**

| Plan | Requests/Minute |
|------|-----------------|
| Free | 60 |
| Pro | 300 |
| Team | 600 |

---

### 15. Redis Caching Layer

**Location:** `apps/worker/src/worker/cache.py`

**Purpose:** Simple Redis-based caching utilities for the worker with TTL support.

**Key Features:**
- Namespace-based key generation
- MD5 hash for complex payloads
- TTL support
- Datetime serialization handling

**Public API:**

```python
from worker.cache import get, set, safe_json_dumps

def get(namespace: str, payload: dict) -> Optional[dict]:
    """
    Get cached data by namespace and payload.
    
    Args:
        namespace: Cache namespace (e.g., "listings", "metrics")
        payload: Query parameters that identify the cache entry
    
    Returns:
        Cached data or None if not found
    """

def set(namespace: str, payload: dict, data: dict, ttl_s: int = 3600):
    """
    Set cached data with TTL.
    
    Args:
        namespace: Cache namespace
        payload: Query parameters (used for key generation)
        data: Data to cache
        ttl_s: Time to live in seconds (default: 1 hour)
    """

def safe_json_dumps(obj) -> str:
    """JSON serialization with datetime handling."""
```

**Key Format:**

```
mr:{namespace}:{md5_hash_of_payload}
```

**Usage Example:**

```python
# Check cache first
cached = get("listings", {"city": "LA", "status": "active"})
if cached:
    return cached

# Fetch fresh data
data = fetch_listings(city="LA", status="active")

# Cache for 30 minutes
set("listings", {"city": "LA", "status": "active"}, data, ttl_s=1800)
```

---

### 16. Scheduled Task Ticker

**Location:** `apps/worker/src/worker/schedules_tick.py`

**Purpose:** Process due scheduled reports with timezone/DST awareness and atomic locking.

**Key Features:**
- Timezone-aware next run computation
- DST-robust scheduling
- Atomic database locking (prevents race conditions)
- Celery task enqueueing

**Public API:**

```python
from worker.schedules_tick import process_due_schedules, compute_next_run, enqueue_report

def process_due_schedules():
    """
    Find all due schedules and enqueue them.
    
    Uses SELECT ... FOR UPDATE SKIP LOCKED for atomic processing.
    Should be called periodically (e.g., every minute via cron).
    """

def compute_next_run(
    cadence: str,
    weekly_dow: Optional[int],
    monthly_dom: Optional[int],
    send_hour: int,
    send_minute: int,
    timezone: str = "UTC",
    from_time: Optional[datetime] = None
) -> datetime:
    """
    Compute the next run time for a schedule.
    
    Args:
        cadence: "weekly" or "monthly"
        weekly_dow: Day of week (0=Sunday, 1=Monday, ...)
        monthly_dom: Day of month (1-28)
        send_hour: Hour in 24h format
        send_minute: Minute
        timezone: IANA timezone string
        from_time: Base time (default: now)
    
    Returns:
        Next run time in UTC (timezone-naive datetime)
    """

def enqueue_report(
    schedule_id: str,
    account_id: str,
    report_type: str,
    city: Optional[str],
    zip_codes: Optional[list],
    lookback_days: int,
    filters: Optional[Dict[str, Any]] = None
) -> tuple[str, str]:
    """
    Enqueue a report generation task to Celery.
    
    Returns:
        Tuple of (run_id, celery_task_id)
    """
```

**Cron Setup:**

```bash
# Run every minute
* * * * * python -c "from worker.schedules_tick import process_due_schedules; process_due_schedules()"
```

---

## Tier 4: Frontend Utilities

### 17. API Fetch with Proxy & Retry

**Location:** `apps/web/lib/api.ts`

**Purpose:** Client-side API fetch function with proxy routing and retry logic.

**Key Features:**
- Browser: Routes through `/api/proxy` to avoid CORS
- Server: Direct API calls
- Automatic retry for transient errors
- Cookie-based authentication

**Public API:**

```typescript
import { apiFetch, API_BASE } from '@/lib/api';

async function apiFetch(
  path: string, 
  init: RequestInit = {}
): Promise<any> {
  /**
   * Fetch from API with automatic routing and retry.
   * 
   * @param path - API path (e.g., "/v1/reports")
   * @param init - Fetch options
   * @returns Parsed JSON response
   * @throws Error on non-OK response after retries
   */
}
```

**Routing Logic:**

| Context | URL |
|---------|-----|
| Browser | `/api/proxy/v1/reports` → internal proxy |
| Server | `https://api.example.com/v1/reports` → direct |

**Usage Example:**

```typescript
// GET request
const reports = await apiFetch('/v1/reports');

// POST request
const newReport = await apiFetch('/v1/reports', {
  method: 'POST',
  body: JSON.stringify({ city: 'Los Angeles', report_type: 'market_snapshot' })
});
```

---

### 18. Toast Notification System

**Location:** `apps/web/hooks/use-toast.ts`

**Purpose:** Global toast notification system inspired by `react-hot-toast`.

**Key Features:**
- Global state management
- Configurable display limit
- Auto-dismiss with delay
- Update existing toasts

**Public API:**

```typescript
import { useToast, toast } from '@/hooks/use-toast';

// Hook usage
function MyComponent() {
  const { toasts, toast, dismiss } = useToast();
  
  const showSuccess = () => {
    toast({
      title: "Success!",
      description: "Your report has been generated.",
      variant: "default"  // or "destructive"
    });
  };
}

// Direct usage (outside components)
toast({
  title: "Error",
  description: "Something went wrong.",
  variant: "destructive"
});
```

**Toast Options:**

| Property | Type | Description |
|----------|------|-------------|
| `title` | ReactNode | Toast title |
| `description` | ReactNode | Toast description |
| `variant` | "default" \| "destructive" | Visual style |
| `action` | ToastActionElement | Optional action button |

---

### 19. Market Metrics Calculator

**Location:** `apps/worker/src/worker/compute/calc.py`

**Purpose:** Calculate market snapshot metrics from property listing data.

**Key Features:**
- Active/pending/closed counts
- Median and average calculations
- Days on market (DOM)
- Months of inventory (MOI)
- Close-to-list ratio
- Absorption rate

**Public API:**

```python
from worker.compute.calc import snapshot_metrics

def snapshot_metrics(rows: List[Dict]) -> Dict:
    """
    Calculate market metrics from listing data.
    
    Args:
        rows: List of normalized listing dictionaries
              Required keys: status, list_price, close_price, 
              list_date, days_on_market, price_per_sqft, 
              close_to_list_ratio
    
    Returns:
        Dictionary with calculated metrics:
        - total_active: int
        - total_pending: int
        - total_closed: int
        - new_listings_7d: int
        - median_list_price: int
        - median_close_price: int
        - avg_dom: float
        - avg_price_per_sqft: int
        - close_to_list_ratio: float
        - months_of_inventory: float
        - absorption_rate: float
    """
```

**Usage Example:**

```python
listings = fetch_properties({"city": "LA", "status": ["active", "closed"]})
normalized = [normalize_listing(l) for l in listings]
metrics = snapshot_metrics(normalized)

print(f"Active: {metrics['total_active']}")
print(f"Median Price: ${metrics['median_list_price']:,}")
print(f"Days on Market: {metrics['avg_dom']}")
print(f"Months of Inventory: {metrics['months_of_inventory']}")
```

---

## Tier 5: Reusable UI Components

### 20. DataTable Component

**Location:** `packages/ui/src/components/data-table.tsx`

**Purpose:** Generic table component for displaying tabular data with custom columns.

**Key Features:**
- Custom column renderers
- Empty state handling
- Consistent styling with glass effect
- Type-safe with generics

**Public API:**

```typescript
import { DataTable } from '@ui/components/data-table';

interface Column<T> {
  key: keyof T;
  label: string;
  render?: (value: T[keyof T], row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  className?: string;
}
```

**Usage Example:**

```tsx
interface User {
  id: string;
  name: string;
  email: string;
  status: 'active' | 'inactive';
}

const columns: Column<User>[] = [
  { key: 'name', label: 'Name' },
  { key: 'email', label: 'Email' },
  { 
    key: 'status', 
    label: 'Status',
    render: (value) => (
      <Badge variant={value === 'active' ? 'success' : 'secondary'}>
        {value}
      </Badge>
    )
  }
];

<DataTable data={users} columns={columns} />
```

---

### 21. HorizontalStepper Component

**Location:** `packages/ui/src/components/horizontal-stepper.tsx`

**Purpose:** Visual stepper for multi-step forms with animated progress.

**Key Features:**
- Animated progress bar (Framer Motion)
- Completed step checkmarks
- Current step indicator with pulse
- Step labels

**Public API:**

```typescript
import { HorizontalStepper } from '@ui/components/horizontal-stepper';

interface Step {
  id: string;
  label: string;
}

interface HorizontalStepperProps {
  steps: Step[];
  currentStep: number;  // 0-indexed
  className?: string;
}
```

**Usage Example:**

```tsx
const steps = [
  { id: 'type', label: 'Report Type' },
  { id: 'area', label: 'Area' },
  { id: 'delivery', label: 'Delivery' },
  { id: 'confirm', label: 'Confirm' }
];

<HorizontalStepper steps={steps} currentStep={1} />
```

---

### 22. TimePicker Component

**Location:** `packages/ui/src/components/time-picker.tsx`

**Purpose:** User-friendly time selector with hour/minute dropdowns.

**Key Features:**
- 24-hour format
- 15-minute intervals for minutes
- Controlled component

**Public API:**

```typescript
import { TimePicker } from '@ui/components/time-picker';

interface TimePickerProps {
  value: string;            // "HH:MM" format
  onChange: (value: string) => void;
  className?: string;
}
```

**Usage Example:**

```tsx
const [time, setTime] = useState("09:00");

<TimePicker value={time} onChange={setTime} />
```

---

### 23. CadencePicker Component

**Location:** `packages/ui/src/components/cadence-picker.tsx`

**Purpose:** Complete scheduling cadence selector (weekly/monthly + time).

**Key Features:**
- Weekly/monthly cadence toggle
- Day of week selector (weekly)
- Day of month selector (monthly)
- Integrated time picker

**Public API:**

```typescript
import { CadencePicker } from '@ui/components/cadence-picker';

type Cadence = "weekly" | "monthly";

interface CadencePickerProps {
  cadence: Cadence;
  onCadenceChange: (cadence: Cadence) => void;
  weekday?: string;
  onWeekdayChange?: (weekday: string) => void;
  monthDay?: number;
  onMonthDayChange?: (day: number) => void;
  time: string;
  onTimeChange: (time: string) => void;
  className?: string;
}
```

**Usage Example:**

```tsx
<CadencePicker
  cadence={cadence}
  onCadenceChange={setCadence}
  weekday={weekday}
  onWeekdayChange={setWeekday}
  monthDay={monthDay}
  onMonthDayChange={setMonthDay}
  time={time}
  onTimeChange={setTime}
/>
```

---

### 24. CityAutocomplete Component

**Location:** `packages/ui/src/components/city-autocomplete.tsx`

**Purpose:** Autocomplete input for city selection from a predefined list.

**Key Features:**
- Real-time filtering
- Keyboard navigation
- Exact match indicator
- Configurable city list

**Public API:**

```typescript
import { CityAutocomplete } from '@ui/components/city-autocomplete';

interface CityAutocompleteProps {
  value: string;
  onChange: (city: string) => void;
  placeholder?: string;
  className?: string;
}
```

**Usage Example:**

```tsx
const [city, setCity] = useState("");

<CityAutocomplete
  value={city}
  onChange={setCity}
  placeholder="Search for a city..."
/>
```

---

## Quick Reference: Environment Variables

### API Service

```bash
# Authentication
JWT_SECRET=your-jwt-secret

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# SiteX MLS
SITEX_CLIENT_ID=...
SITEX_CLIENT_SECRET=...
SITEX_FEED_ID=...
SITEX_BASE_URL=...

# SimplyRETS
SIMPLYRETS_USERNAME=...
SIMPLYRETS_PASSWORD=...

# Twilio
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# Stripe
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO_MONTH=price_...
STRIPE_PRICE_TEAM_MONTH=price_...

# Cloudflare R2
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=...
R2_PUBLIC_URL=https://...
```

### Worker Service

```bash
# Database & Redis
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# SendGrid
SENDGRID_API_KEY=SG....
SENDGRID_FROM_EMAIL=noreply@example.com
SENDGRID_FROM_NAME=TrendyReports

# OpenAI
OPENAI_API_KEY=sk-...
AI_INSIGHTS_ENABLED=true

# PDF Generation
PDF_ENGINE=pdfshift  # or playwright
PDFSHIFT_API_KEY=...
PDF_DIR=/tmp/pdfs
SOCIAL_DIR=/tmp/social
PRINT_BASE=https://reports.example.com
```

### Web Application

```bash
NEXT_PUBLIC_API_BASE=https://api.example.com
NEXT_PUBLIC_GOOGLE_MAPS_KEY=AIza...
```

---

## Summary

This document covers **24 reusable patterns and integrations** across 5 tiers:

| Tier | Count | Examples |
|------|-------|----------|
| External APIs | 8 | SiteX, SimplyRETS, Twilio, SendGrid, Stripe, R2, OpenAI, Google Places |
| Document Generation | 4 | PDF Engine, Social Images, QR Codes, Email Templates |
| Infrastructure | 4 | Auth, Rate Limiting, Caching, Scheduled Tasks |
| Frontend Utilities | 3 | API Fetch, Toasts, Metrics Calculator |
| UI Components | 5 | DataTable, Stepper, TimePicker, CadencePicker, CityAutocomplete |

Each pattern is designed for reusability and follows consistent conventions for configuration, error handling, and API design.
