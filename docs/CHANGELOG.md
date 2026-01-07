# Changelog

All notable changes to TrendyReports are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- **AI-Powered Email Insights (V13)** - Exciting, personable market commentary using GPT-4o-mini
- **Gallery Insight Support** - New Listings Gallery and Featured Listings now include AI-generated blurbs
- **Display Limits Documentation** - New section in REPORT_TYPES_MATRIX.md explaining email (12) vs PDF (9) listing caps

### Changed
- Admin login page updated to light theme (matches admin dashboard)
- Admin login page and dashboard now use the actual TrendyReports logo
- **AI prompts completely rewritten** for warmth and excitement:
  - Leads with exciting findings, not "This report shows..."
  - Makes numbers human: "129 families found their home" not "129 closed sales"
  - Conversational tone like a knowledgeable friend
  - Context-aware for hot vs buyer-friendly markets
- Fallback templates (when AI unavailable) also rewritten to be personable

---

## [1.0.0] - 2026-01-07

### Email System (V12)
- **Gallery Metrics Fix**: Email cards now display correct listing counts, median prices, and starting prices
- **AI Insights**: Optional GPT-4o-mini integration for contextual market commentary
- **Filter Description**: Styled blurb after hero section showing applied filters for preset reports
- **Closed Sales Priority**: Listings table moved higher to avoid Gmail clipping

### Email System (V10-V11)
- Professional corporate redesign removing emojis and casual elements
- Adaptive gallery layouts (3-column, 2-column, vertical list)
- Consistent bordered metric rows with neutral colors

### Smart Presets
- Market-adaptive pricing using percentage of median (works in any market)
- Elastic widening safety net for low-result scenarios
- Custom preset display names in PDF headers

### White-Label Branding
- Separate logo uploads for PDF header, PDF footer, email header, email footer
- Primary and accent color customization
- Rep photo integration (Option A: uses profile avatar)

### Core Platform
- Multi-tenant architecture with Row-Level Security
- JWT authentication with httpOnly cookies
- Affiliate sponsorship system for title companies
- User onboarding wizard with step tracking
- Admin console with platform-wide visibility

### Integrations
- SimplyRETS MLS data integration
- SendGrid email delivery
- PDFShift PDF generation
- Cloudflare R2 file storage

---

*For detailed technical documentation, see the `/docs` folder.*

