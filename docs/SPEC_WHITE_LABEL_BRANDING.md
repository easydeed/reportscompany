# SPEC 1 – WHITE-LABEL BRANDING (W2–W4)

**Status:** 🔄 In Progress  
**Last Updated:** November 14, 2025

---

## 🌐 GLOBAL CONSTRAINTS FOR W2–W4

### Do not touch:
- Auth logic (mr_token, login, accept-invite, RLS)
- Plan/limit logic, affiliates model, invite flow, Stripe code
- CORS/env config or routing

### Assume:
- `affiliate_branding` table already exists
- `get_brand_for_account(db, account_id)` helper already exists and is tested

### Only change:
- Affiliate-facing branding API & UI
- Email template builder & worker email orchestration
- Report data API & PDF template mapping

---

## W2 – Affiliate Branding API + UI

### W2.1 – Branding API routes (backend)

**File:** `apps/api/src/api/routes/affiliates.py`

**Add two endpoints:**
- `GET /v1/affiliate/branding`
- `POST /v1/affiliate/branding`

**Shared guard:**
- Resolve current_account using existing account context
- If `current_account.account_type != 'INDUSTRY_AFFILIATE'`:
  - `raise HTTPException(status_code=403, detail="not_affiliate_account")`

**GET /v1/affiliate/branding:**
- Query `affiliate_branding` using `account_id = current_account.id`
- If row exists → return its fields
- If not:
  - Use `brand_display_name = current_account.name`
  - All other fields null

**Response JSON:**
```json
{
  "brand_display_name": "ACME Title",
  "logo_url": "https://...",
  "primary_color": "#123456",
  "accent_color": "#ABCDEF",
  "rep_photo_url": "https://...",
  "contact_line1": "Jane Doe • Senior Rep",
  "contact_line2": "555-123-4567 • jane@example.com",
  "website_url": "https://acme-title.com"
}
```

**POST /v1/affiliate/branding:**
- Accept the same fields in JSON body
- Validate:
  - `brand_display_name` non-empty
  - If colors provided, they look like hex (`^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$`)
- Upsert:
  - If row exists for `account_id` → UPDATE
  - Else → INSERT
- Return saved object in same shape as GET

---

### W2.2 – Proxy + Branding page (frontend)

**Proxy File:** `apps/web/app/api/proxy/v1/affiliate/branding/route.ts`

**Implement:**
- GET → forward to backend `/v1/affiliate/branding`
- POST → forward to backend `/v1/affiliate/branding` with JSON body
- Use same base URL/env as other proxies

**Page File:** `apps/web/app/affiliate/branding/page.tsx`

**Server component:**
- Fetch `GET /api/proxy/v1/affiliate/branding` at render
- If 403 → render: "This account is not an industry affiliate."

**Render a simple form with fields:**
- Brand Display Name
- Logo URL
- Primary Color
- Accent Color
- Rep Photo URL
- Contact Line 1
- Contact Line 2
- Website URL

**On submit (client-side):**
- POST to `/api/proxy/v1/affiliate/branding` with JSON
- Show success toast/inline message
- Re-fetch or locally update state to refresh preview

**Add a live preview card:**
- Shows logo (if URL), display name, colored header using primary/accent, contact lines

---

### W2.3 – Add "Branding" link to affiliate nav

**File:** Sidebar/nav component (e.g., `apps/web/components/sidebar.tsx`)

**In the nav items for affiliate accounts:**
- If `account_type === 'INDUSTRY_AFFILIATE'`:
  - Add nav item:
    - Label: "Branding"
    - href: `/app/affiliate/branding`
- Do not show this item for REGULAR accounts

---

## W3 – Wire Branding into Emails

### W3.1 – Extend email template builder

**File:** `apps/worker/src/email/templates.py`

**Import Brand type** (or define a minimal typed dict locally matching W1)

**Update function signature:**
```python
def build_schedule_email_html(
    result_json: Dict,
    pdf_url: str,
    unsubscribe_url: str,
    account_name: str | None = None,
    brand: Optional[Brand] = None,
) -> str:
```

**Inside, derive:**
```python
brand_name = (brand and brand.get("display_name")) or account_name or "TrendyReports"
logo_url = brand.get("logo_url") if brand else None
primary = (brand and brand.get("primary_color")) or "#7C3AED"
accent = (brand and brand.get("accent_color")) or "#F26B2B"
rep_photo = (brand or {}).get("rep_photo_url")
contact_line1 = (brand or {}).get("contact_line1")
contact_line2 = (brand or {}).get("contact_line2")
website_url = (brand or {}).get("website_url")
```

**Use these in the HTML:**
- **Header:** If `logo_url` → `<img>` left + `brand_name` text
- **Colors:** Inline styles (e.g., background for header bar, CTA button) use `primary` and `accent`
- **Footer:**
  - Show `contact_line1`, `contact_line2`, `website_url` as main contact info
  - Keep unsubscribe link
  - Optionally keep a tiny line "Powered by TrendyReports" in muted 10px font

**Do not change:** KPI content or CTA link behavior

---

### W3.2 – Worker calls branding helper

**File:** `apps/worker/src/worker/tasks.py`

**After determining `account_id` for the schedule run:**
- Use DB connection to call `get_brand_for_account(db, account_id)`
- Pass that `brand` into `build_schedule_email_html(...)`

**Note:** For REGULAR accounts with `sponsor_account_id`, branding will automatically use affiliate brand because of W1's logic

---

## W4 – Wire Branding into PDFs

### W4.1 – Add brand object to report data API

**File:** `apps/api/src/api/routes/reports.py`

**When constructing the response:**
- You already know `account_id` of the report or run
- Call `get_brand_for_account(db, account_id)`
- Add the result to the JSON under "brand" key:

```json
{
  "result_json": { ... },
  "brand": {
    "display_name": "...",
    "logo_url": "...",
    "primary_color": "#...",
    "accent_color": "#...",
    ...
  }
}
```

**Keep existing fields intact**

---

### W4.2 – Use brand in mapping (templates.ts)

**File:** `apps/web/lib/templates.ts`

**For each builder:**
- Accept data including brand
- Derive:
```typescript
const brand = data.brand || {};
const brandName = brand.display_name || "TrendyReports";
const logoUrl = brand.logo_url || "";
const primary = brand.primary_color || "#7C3AED";
const accent = brand.accent_color || "#F26B2B";
```

**Before placeholder replacement:**
- Inject an override style into the HTML head:
```typescript
const overrideStyle = `
  <style>
    :root {
      --pct-blue: ${primary};
      --pct-accent: ${accent};
    }
  </style>
`;
const htmlWithBrand = templateHtml.replace("</head>", `${overrideStyle}</head>`);
```

**Use brand placeholders:**
- Ensure templates have tokens like `{{brand_name}}`, `{{brand_logo_url}}`, `{{brand_tagline}}`
- Replace them via simple string replace:
```typescript
html = html.replace(/{{brand_name}}/g, brandName);
html = html.replace(/{{brand_logo_url}}/g, logoUrl);
html = html.replace(/{{brand_tagline}}/g, `${brandName} • Market Intelligence`);
```

---

### W4.3 – Update HTML templates to use brand tokens

**Files:**
- `apps/web/templates/trendy-market-snapshot.html`
- `apps/web/templates/trendy-new-listings.html`
- `apps/web/templates/trendy-inventory.html`
- `apps/web/templates/trendy-closed.html`
- `apps/web/templates/trendy-price-bands.html`

**Header:**
- Replace hardcoded "TrendyReports" with `{{brand_name}}`
- Logo `<img>` src="..." → src="`{{brand_logo_url}}`" and alt="`{{brand_name}}`"

**Footer:**
- Replace static brand name tagline with `{{brand_tagline}}`

**Do not change:** Layout, KPI labels, or table structures

---

**Status:** Ready to implement  
**Dependencies:** W1 (complete), branding service (exists)

