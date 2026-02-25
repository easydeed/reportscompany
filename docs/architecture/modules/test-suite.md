# Module: Test Suite

> `tests/test_property_templates.py`, `e2e/`, `pytest.ini`

---

## Purpose

Documents the automated test suite for TrendyReports. The test suite covers:
- **Unit / integration tests** — Jinja2 template rendering for all property report themes (pytest)
- **End-to-end tests** — Browser-based flows for authentication, affiliate management, billing, and plan management (Playwright)

---

## Test Files

| File | Framework | Coverage |
|------|-----------|----------|
| `tests/test_property_templates.py` | pytest | Property report HTML templates (5 themes × 6 test classes) |
| `e2e/auth.spec.ts` | Playwright | Login, signup, password reset, email verification flows |
| `e2e/affiliate.spec.ts` | Playwright | Affiliate dashboard, sponsored accounts, branding |
| `e2e/plan.spec.ts` | Playwright | Plan selection, limits, upgrade flows |
| `e2e/stripe.spec.ts` | Playwright | Stripe webhook handling, subscription events |

---

## Unit / Integration Tests: `tests/test_property_templates.py`

### Test Classes

| Class | Description |
|-------|-------------|
| `TestTemplateExistence` | Verifies all 5 theme template files exist at expected paths |
| `TestTemplateRendering` | Renders each theme with minimal context and full context; asserts no exception |
| `TestHTMLStructure` | Validates rendered HTML: well-formed, no unrendered `{{ }}` blocks, no `"undefined"` text |
| `TestContentRendering` | Asserts property address, agent name, comparables data, and currency formatting appear in output |
| `TestPrintCSS` | Checks for `@page`, `@media print`, and `page-break` CSS rules required for PDF output |
| `TestEdgeCases` | Tests empty comparables, missing optional fields, `None` value handling |

### Test Data

**Minimal context** (required fields only):
- Address: arbitrary placeholder
- 0 comparables
- Default agent info

**Full context** (La Verne property):
- `714 Vine St, La Verne, CA 91750`
- 4 comparables with full field set
- Detailed stats (low/mid/high price ranges)
- Agent: name, license, phone, email, headshot
- All 5 themes tested with this dataset

### Running Tests

```bash
# From repo root
pytest tests/test_property_templates.py -v

# With coverage
pytest tests/test_property_templates.py --cov=apps/worker/src/worker -v

# Run single theme
pytest tests/test_property_templates.py -k "teal" -v

# Run single test class
pytest tests/test_property_templates.py::TestPrintCSS -v
```

### `pytest.ini` Configuration

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

---

## E2E Tests: `e2e/` (Playwright)

### Setup

```bash
# Install Playwright browsers (first time)
npx playwright install

# Run all E2E tests
npx playwright test

# Run with UI mode
npx playwright test --ui

# Run specific spec
npx playwright test e2e/auth.spec.ts
```

### `playwright.config.ts`

```typescript
// Key settings:
baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
use: { trace: 'on-first-retry' }
```

---

## Test Scripts (Manual QA, not automated)

These scripts in `scripts/` are **manual smoke tests** run by developers, not part of `pytest` or Playwright:

| Script | Purpose |
|--------|---------|
| `scripts/test_simplyrets.py` | SimplyRETS API connectivity + query validation |
| `scripts/test_sitex.py` | SiteX API connectivity + field extraction |
| `scripts/test_property_report_flow.py` | Full property report flow (API → worker → PDF) |
| `scripts/test_all_reports.py` | All 8 market report types |
| `scripts/test_report_flow.py` | Single market report flow |
| `scripts/test_affiliates.py` | Affiliate management flows |

See [`modules/cli-tools.md`](./cli-tools.md) for full CLI reference.

---

## Dependencies

### pytest stack
| Package | Version |
|---------|---------|
| `pytest` | Latest |
| `pytest-cov` | Latest |
| `Jinja2` | Same as worker |
| `python-dotenv` | Latest |

### Playwright stack
| Package | Version |
|---------|---------|
| `@playwright/test` | Latest |
| `typescript` | 5.x |

---

## Coverage Gaps

| Area | Status |
|------|--------|
| Template rendering (all 5 themes) | ✅ Covered |
| API routes (unit tests) | ❌ No automated tests |
| Worker tasks (unit tests) | ❌ No automated tests |
| Filter resolver logic | ❌ No automated tests |
| Fallback ladder logic | ❌ No automated tests (manual via `test_property_report_flow.py`) |
| E2E auth flows | ✅ Playwright |
| E2E billing/Stripe | ✅ Playwright |

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02 | Added `TestEdgeCases` class for `None` value + empty comp handling |
| 2026-02 | Added `TestPrintCSS` to validate PDF-required CSS rules |
| 2026-01 | Added full context (La Verne property) test data with 4 comparables |
| 2025-12 | Initial test file with `TestTemplateExistence` + `TestTemplateRendering` |
