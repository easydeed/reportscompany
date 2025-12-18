# TrendyReports — Single Source of Truth
_Project Status & Architecture_

## Executive Summary

**TrendyReports** is a SaaS platform that transforms live MLS data into photo-rich, branded **PDF reports** and matching **email-ready reports** with automated scheduling and delivery.

The platform serves:
- Individual real estate agents
- Industry affiliates (title companies, lenders, brokerages) who sponsor agents and control white-label branding

---

## Core System Status

| System | Status | Notes |
|------|------|------|
| People (Contacts & Groups) | COMPLETE | Full CRUD, CSV import, group targeting |
| Billing (Stripe Integration) | COMPLETE | Plans DB, webhooks, subscription state |
| Schedules (Automated Reports) | HARDENED | Plan limits, timezone support, auto-pause on failure |
| Reports (Generation & Preview) | WORKING | All 8 report types, PDF pipeline, branding |
| Authentication & RLS | COMPLETE | JWT, multi-tenant row-level security |
| Branding (White-Label) | IN PROGRESS | Major overhaul planned |

---

## Current Focus

### Branding System Overhaul (Highest Priority)

While basic branding works (name, colors, contact info), affiliates need a real white-label experience:
- File uploads (logo, headshot)
- Live template previews
- Downloadable branded samples

This is **critical for affiliate revenue**.

---

## Architecture Overview

### Infrastructure Stack

| Layer | Technology | Location |
|----|----|----|
| Frontend | Next.js 16 (App Router) | Vercel — trendyreports.io |
| API | FastAPI + Poetry | Render — reportscompany.onrender.com |
| Worker | Celery | Render Background Worker |
| Scheduler | Python (schedules_tick.py) | Render Background Worker |
| Database | PostgreSQL 15 + RLS | Render Postgres |
| File Storage | Cloudflare R2 | R2 Bucket |
| Email | SendGrid | API |
| Payments | Stripe | Checkout + Webhooks |
| MLS Data | SimplyRETS | Demo + Production |

---

## Data Model (Core Tables)

accounts, users, account_users, plans, report_generations, schedules, contacts, contact_groups, affiliate_branding

---

## Branding System — 5 Pass Implementation Plan

**PASS B1:** Backend file uploads to R2  
**PASS B2:** Frontend drag-and-drop upload UI  
**PASS B3:** Live report & email previews  
**PASS B4:** Download sample PDFs + test emails  
**PASS B5:** Polish, headshot integration, UX

---

## Report Types

market_snapshot, new_listings, new_listings_gallery, featured_listings, inventory, closed, price_bands, open_houses

---

## Recommended Next Steps

Immediate Priority: **Complete Branding Overhaul (2–3 weeks)**

Followed by:
- Schedules UI
- Admin Console
- Template polish
- Plan enforcement

---

_Last Updated: November 25, 2025_
