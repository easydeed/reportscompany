# CMA Funnel — Remaining Tasks

> Updated March 2026. Previous CMA data pipeline fixes are resolved and documented in `docs/CMA_PIPELINE.md`.

## Completed (for reference)

- [x] **CMA data pipeline rewrite** — Comps, market stats, value estimate all working
- [x] **Property type filtering** — SiteX UseCode → SimplyRETS type/subtype mapping + post-filter
- [x] **Lat/lng flow** — SiteX → frontend → API → consumer_reports.property_data → worker
- [x] **Distance calculation** — Haversine using subject lat/lng
- [x] **Mobile viewer field mapping** — sold_date, price_per_sqft, distance computed from canonical format
- [x] **Agent SMS notification** — Agent receives SMS with lead details after report delivery
- [x] **Branding** — Agent's theme, colors, logo flow from accounts table into PDF

---

## Task 1: Remove QR Code + Lead Page from Property Report Flow

When an agent creates a property report through the property wizard, the system currently auto-generates a QR code and lead landing page (`/p/{short_code}`). This is redundant now that agents have the dedicated CMA lead page (`/cma/{agent_code}`).

### What to Remove

**In the property report creation API handler** (`apps/api/src/api/routes/property.py`):

1. Remove the call to `generate_qr_code()` during report creation
2. Remove the `short_code` generation trigger if triggered in the API handler (DB trigger is harmless)
3. Remove any R2 upload of QR code PNG during report creation

**In the property wizard frontend** (`step-review.tsx` or report success page):

- Remove QR code image display
- Remove "Share Landing Page" / "Copy Link" buttons referencing `/p/{short_code}`
- Remove "Landing Page" section from report detail page
- Keep PDF download and "View in Browser"

**In the report detail page** (`apps/web/app/app/property/[id]/page.tsx`):

- Remove QR code display section
- Remove landing page URL display
- Remove landing page analytics (view count, visitors)
- Remove lead list associated with the property report

**Do NOT remove:**

- The `/p/{short_code}` route — existing QR codes should still work
- The `property_reports.short_code` column — backwards compatibility
- The `qr_service.py` file — may be reused
- The `leads` table or lead capture endpoint — still used by CMA funnel

---

## Task 2: Email Delivery Integration

The `process_consumer_report` email branch currently marks the report as "sent" without sending an actual email:

```python
elif delivery_method == "email" and consumer_email:
    # TODO: integrate Resend for email delivery
    logger.info(f"Email delivery requested for {consumer_email} — marking as sent")
```

Need to integrate Resend (or similar) to actually deliver the report link via email.
