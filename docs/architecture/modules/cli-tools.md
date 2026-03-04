# Module: CLI & QA Tools

> `qa_deliver_reports.py`, `scripts/test_simplyrets.py`, `scripts/test_sitex.py`, `scripts/test_property_report_flow.py`, `scripts/test_all_reports.py`, `scripts/generate_all_property_pdfs.py`, `scripts/generate_theme_previews.py`

---

## Purpose

A collection of command-line tools for manual QA, smoke testing, and development workflows. These are **not part of the production application** — they are standalone Python scripts run by developers and QA engineers against staging or production environments.

---

## Tool Reference

---

### `qa_deliver_reports.py` (root)

**Full end-to-end QA delivery tool.** Creates temporary schedules, triggers report generation, polls for completion, delivers reports to a QA inbox, and cleans up.

**Usage:**
```bash
python qa_deliver_reports.py \
  --base-url https://reportscompany.onrender.com \
  --token $JWT_TOKEN \
  --deliver-to qa@example.com \
  --city Irvine \
  [--report-types all|market_snapshot|closed_sales|new_listings_gallery] \
  [--timeout 120]
```

**Supported `--report-types` values:**

| Value | Description |
|-------|-------------|
| `all` (default) | Runs all 8 configurations below |
| `market_snapshot` | Market Update report |
| `closed_sales` | Closed Sales report |
| `new_listings_gallery` | New Listings Gallery |

**Report configurations (when `--report-types all`):**

| Config | Report type | Audience preset |
|--------|-------------|-----------------|
| 1 | Market Update | All Listings |
| 2 | Market Update | First-Time Buyers (2+ bed/bath, SFR, ≤70% median) |
| 3 | Market Update | Luxury (SFR, ≥150% median) |
| 4 | Market Update | Families (3+ beds, 2+ baths, SFR) |
| 5 | New Listings Gallery | Condo (Condominium) |
| 6 | New Listings Gallery | Investors (≤50% median) |
| 7 | Closed Sales | All Listings |
| 8 | Closed Sales | First-Time Buyers |

**Authentication options:**
- `--token JWT_TOKEN` — pre-obtained JWT
- `--email EMAIL --password PASSWORD` — login and obtain token automatically

**What it does internally:**
1. `POST /v1/schedules` — creates temporary schedule (weekly cadence)
2. `POST /v1/schedules/{id}/run` — triggers immediate generation
3. Polls `GET /v1/schedules/{id}/runs` until `status = "complete"` or timeout
4. `DELETE /v1/schedules/{id}` — cleans up temporary schedule

---

### `scripts/test_simplyrets.py`

**Smoke test for the SimplyRETS API connection** and query capabilities.

**Usage:**
```bash
cd apps/worker
python ../../scripts/test_simplyrets.py
```

**What it tests:**
- Connectivity and authentication (Basic Auth)
- Property type/subtype discovery for a given city
- Active vs. Closed listing queries separately
- Subtype filters: SFR, Condominium, Townhouse
- `query_builders` module validation

**Output:** Prints status/type/subtype breakdown tables for each query.

**Requires:** `SIMPLYRETS_API_KEY` + `SIMPLYRETS_API_SECRET` in environment.

---

### `scripts/test_sitex.py`

**Smoke test for the SiteX Pro API connection.**

**Usage:**
```bash
python scripts/test_sitex.py
```

**What it tests:**
- OAuth2 token acquisition
- Address-based property search (714 Vine St, Anaheim, CA 92805)
- Full field extraction: address, owner, APN, FIPS, beds, baths, sqft, assessed value, legal description

**Requires:** `SITEX_CLIENT_ID` + `SITEX_CLIENT_SECRET` in environment.

---

### `scripts/test_property_report_flow.py`

**End-to-end property report generation test** against the live API.

**Usage:**
```bash
python scripts/test_property_report_flow.py \
  --base-url https://reportscompany.onrender.com \
  --token $JWT_TOKEN
```

**Flow tested:**
1. `POST /v1/property/search` — address lookup
2. `POST /v1/property/comparables` — fallback ladder
3. `POST /v1/property/reports` — create report
4. `POST /v1/property/reports/{id}/generate` — enqueue PDF
5. Poll until `status = "complete"`

---

### `scripts/test_all_reports.py`

**Comprehensive market report generation test** — exercises all 8 report types for a given city.

**Usage:**
```bash
python scripts/test_all_reports.py \
  --base-url $API_URL \
  --token $TOKEN \
  --city Irvine
```

---

### `scripts/test_report_flow.py`

**Simpler market report flow test** — single report type, validates full worker pipeline.

---

### `scripts/gen_la_verne_all_themes.py`

**Primary theme validation script.** Fetches live data from SiteX + SimplyRETS for a La Verne sample property, renders all 5 themes to HTML + optional PDF. Includes AI Executive Summary and Market Trends pages with pre-injected sample data.

**Usage:**
```bash
python scripts/gen_la_verne_all_themes.py                # HTML + PDF (uses PDFShift if key set, else Playwright)
python scripts/gen_la_verne_all_themes.py --html-only    # HTML only (fast, no PDF renderer needed)
python scripts/gen_la_verne_all_themes.py --theme bold    # Single theme
python scripts/gen_la_verne_all_themes.py --open          # Open output after generation
```

**Output:** `output/la_verne_themes/{theme}_report.html` (and `.pdf` if not `--html-only`)

**Pages rendered:** `cover`, `overview`, `contents`, `aerial`, `property`, `analysis`, `comparables`, `range`, `market_trends` (9 pages).

**Data:** Pre-injects `overview_text` and `market_trends_data` so the script works without `OPENAI_API_KEY`. Falls back to hardcoded property/comp data when SiteX/SimplyRETS are unavailable.

**Requires:** `PDFSHIFT_API_KEY` for PDFShift PDF rendering (optional — falls back to Playwright, or use `--html-only`).

---

### `scripts/generate_all_property_pdfs.py`

**Batch HTML/PDF generation** for all 5 themes using static sample data. Does **not** include AI overview page. Outputs to `output/property_reports_v2/`.

**Usage:**
```bash
python scripts/generate_all_property_pdfs.py
```

**Requires:** `PDFSHIFT_API_KEY` in environment (optional).

---

### `scripts/generate_theme_preview_jpgs.py`

**Generates JPG thumbnail previews** for all 5 property report themes. Used by the wizard UI theme selector (`/previews/1.jpg` … `5.jpg`). Extracts the cover page from generated HTML and screenshots it via headless Chromium (Playwright).

**Usage:**
```bash
# Prerequisite: generate theme HTML first
python scripts/gen_la_verne_all_themes.py --html-only

# Then generate previews
python scripts/generate_theme_preview_jpgs.py
```

**Input:** Reads from `output/la_verne_themes/` (preferred), falls back to `output/property_reports_v2/` or `output/property_reports/`.

**Output:** `apps/web/public/previews/1.jpg` … `5.jpg` (510×660 px, letter-size aspect ratio)

**Requires:** Playwright (`pip install playwright && playwright install chromium`). Optional: Pillow for PNG→JPG conversion.

---

### `scripts/generate_theme_previews.py` (legacy)

**Generates PNG thumbnail previews.** Superseded by `generate_theme_preview_jpgs.py`.

**Output:** `output/theme_previews/<theme>.png`

---

## Environment Requirements

All tools read from `.env` (or environment variables). Minimum required:

| Variable | Used by |
|----------|---------|
| `SIMPLYRETS_API_KEY` | `test_simplyrets.py`, `test_property_report_flow.py` |
| `SIMPLYRETS_API_SECRET` | Same |
| `SITEX_CLIENT_ID` | `test_sitex.py`, `test_property_report_flow.py` |
| `SITEX_CLIENT_SECRET` | Same |
| `PDFSHIFT_API_KEY` | `generate_all_property_pdfs.py`, `gen_la_verne_all_themes.py` (optional) |
| `DATABASE_URL` | DB-interacting scripts |

See `.env.example` in repo root for full list.

---

## Dependencies

### Internal
All scripts import from `apps/api/src/api/services/` or `apps/worker/src/worker/` as needed.

### External
| Library | Usage |
|---------|-------|
| `requests` | HTTP calls to API |
| `argparse` | CLI argument parsing |
| `python-dotenv` | `.env` loading |
| `tabulate` | Pretty-print output tables |
| `playwright` | Headless Chromium for PDF rendering and JPG preview screenshots |
| `Pillow` | PNG→JPG conversion for theme previews (optional) |

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| Missing credentials | Script prints clear error and exits with code 1 |
| API returns 401 | Prints "Authentication failed" and exits |
| Poll timeout | Prints "Timed out waiting for report" and exits with code 1 |
| Cleanup failure | Prints warning but does not fail — schedules may need manual deletion |

---

## Change Log

| Date | Change |
|------|--------|
| 2026-03 | Added `gen_la_verne_all_themes.py` — primary theme validation script with AI overview and market trends pages |
| 2026-03 | Added `generate_theme_preview_jpgs.py` — Playwright-based JPG previews replacing `html2image`-based `generate_theme_previews.py` |
| 2026-02 | Added `--report-types` filter to `qa_deliver_reports.py` |
| 2026-01 | Added `test_property_report_flow.py` with fallback ladder validation |
| 2025-12 | Added `generate_theme_previews.py` |
| 2025-11 | Added `qa_deliver_reports.py` |
| 2025-10 | Initial `test_simplyrets.py`, `test_sitex.py` |
