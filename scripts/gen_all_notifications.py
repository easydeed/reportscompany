#!/usr/bin/env python3
"""
Generate ALL notification emails as HTML for visual review.

Covers every email TrendyReports sends:
  1. Email Verification (new signup)
  2. Welcome (post-verify)
  3. Agent Invite (affiliate invites agent)
  4. Password Reset
  5-12. Market Report Delivery (8 report types)

Usage:
    python scripts/gen_all_notifications.py
    python scripts/gen_all_notifications.py --no-open
"""

import argparse
import os
import sys
import platform
import subprocess
from pathlib import Path

WORKER_SRC = Path(__file__).resolve().parent.parent / "apps" / "worker" / "src"
sys.path.insert(0, str(WORKER_SRC))

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "all_notifications"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

APP_BASE = "https://www.trendyreports.io"


def _render_transactional(template_name, **kw):
    """Render one of the 4 transactional email templates via the source file."""
    # Import the API email module by exec-ing only the function bodies
    email_py = Path(__file__).resolve().parent.parent / "apps" / "api" / "src" / "api" / "services" / "email.py"
    src = email_py.read_text(encoding="utf-8")

    # Find and extract just the target function
    import re
    pattern = rf"^(def {template_name}\(.*?)(?=\ndef |\Z)"
    m = re.search(pattern, src, re.MULTILINE | re.DOTALL)
    if not m:
        raise ValueError(f"Could not find {template_name} in email.py")

    func_code = m.group(1).rstrip()
    # Provide a stub for email_service.app_base used in some templates
    stub = f'class _S:\n    app_base = "{APP_BASE}"\nemail_service = _S()\n\n'
    ns = {}
    exec(compile(stub + func_code, str(email_py), "exec"), ns)
    return ns[template_name](**kw)


def gen_transactional():
    """Generate the 4 transactional email types (Resend)."""
    results = []

    items = [
        ("get_verification_email_html", "01_verification.html",
         "Email Verification", "New user signs up",
         {"user_name": "Sarah Chen", "verify_url": f"{APP_BASE}/verify-email?token=sample-token-abc123"}),
        ("get_welcome_email_html", "02_welcome.html",
         "Welcome", "After email verified (currently unused)",
         {"user_name": "Sarah Chen", "login_url": f"{APP_BASE}/app"}),
        ("get_invite_email_html", "03_invite.html",
         "Agent Invite", "Affiliate invites a sponsored agent",
         {"inviter_name": "Jerry Hernandez", "company_name": "Demo Title Company",
          "invite_url": f"{APP_BASE}/welcome?token=sample-invite-token"}),
        ("get_password_reset_email_html", "04_password_reset.html",
         "Password Reset", "User requests password reset",
         {"user_name": "Sarah Chen", "reset_url": f"{APP_BASE}/reset-password?token=sample-reset-token"}),
    ]

    for func_name, filename, label, trigger, kwargs in items:
        html = _render_transactional(func_name, **kwargs)
        p = OUTPUT_DIR / filename
        p.write_text(html, encoding="utf-8")
        results.append((label, trigger, p))

    return results


def gen_report_emails():
    """Generate the 8 market report email types (SendGrid)."""
    from worker.email.template import schedule_email_html

    BRAND = {
        "display_name": "Demo Title Company",
        "logo_url": "https://pub-27b57b762ed14d04b4611ae33705aa02.r2.dev/branding/6588ca4a-9509-4118-9359-d1cbf72dcd52/logo_20260309222300_f3c4f4b6.png",
        "email_logo_url": "https://pub-27b57b762ed14d04b4611ae33705aa02.r2.dev/branding/6588ca4a-9509-4118-9359-d1cbf72dcd52/logo_20260309222300_f3c4f4b6.png",
        "email_footer_logo_url": "https://pub-27b57b762ed14d04b4611ae33705aa02.r2.dev/branding/6588ca4a-9509-4118-9359-d1cbf72dcd52/logo_20260309222308_7738fd92.png",
        "primary_color": "#DC2626",
        "accent_color": "#1D4ED8",
        "rep_name": "Jerry Hernandez",
        "rep_title": "Realtor",
        "rep_photo_url": "https://pub-27b57b762ed14d04b4611ae33705aa02.r2.dev/branding/6588ca4a-9509-4118-9359-d1cbf72dcd52/headshot_20260309222215_b0b1ed62.png",
        "rep_phone": "(213) 309-7286",
        "rep_email": "affiliate@trendyreports-demo.com",
        "contact_line1": "Jerry Hernandez",
        "contact_line2": "Realtor",
    }

    LISTINGS = [
        {"hero_photo_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop",
         "street_address": "1305 Hilldale Avenue", "city": "Los Angeles", "zip_code": "90046",
         "list_price": 1375000, "bedrooms": 4, "bathrooms": 2.5, "sqft": 2600,
         "days_on_market": 28, "close_price": 1350000, "sale_to_list_ratio": 98.2},
        {"hero_photo_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop",
         "street_address": "8742 Wonderland Avenue", "city": "Los Angeles", "zip_code": "90046",
         "list_price": 1625000, "bedrooms": 5, "bathrooms": 3.5, "sqft": 3200,
         "days_on_market": 14, "close_price": 1650000, "sale_to_list_ratio": 101.5},
        {"hero_photo_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop",
         "street_address": "2190 Laurel Canyon Blvd", "city": "Los Angeles", "zip_code": "90046",
         "list_price": 1195000, "bedrooms": 3, "bathrooms": 2, "sqft": 2200,
         "days_on_market": 42, "close_price": 1175000, "sale_to_list_ratio": 98.3},
        {"hero_photo_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=600&h=400&fit=crop",
         "street_address": "1478 N Kings Road", "city": "West Hollywood", "zip_code": "90069",
         "list_price": 1545000, "bedrooms": 4, "bathrooms": 3, "sqft": 2950,
         "days_on_market": 21, "close_price": 1530000, "sale_to_list_ratio": 99.0},
        {"hero_photo_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=600&h=400&fit=crop",
         "street_address": "3201 Sunset Plaza Drive", "city": "Los Angeles", "zip_code": "90069",
         "list_price": 2150000, "bedrooms": 5, "bathrooms": 4, "sqft": 3800,
         "days_on_market": 7, "close_price": 2175000, "sale_to_list_ratio": 101.2},
        {"hero_photo_url": "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600&h=400&fit=crop",
         "street_address": "945 Palm Avenue", "city": "Los Angeles", "zip_code": "90069",
         "list_price": 895000, "bedrooms": 2, "bathrooms": 2, "sqft": 1450,
         "days_on_market": 35, "close_price": 880000, "sale_to_list_ratio": 98.3},
    ]

    METRICS = {
        "total_active": 347, "total_pending": 89, "total_closed": 124,
        "total_listings": 347, "new_this_month": 58,
        "median_list_price": 1285000, "median_close_price": 1245000,
        "avg_list_price": 1420000, "avg_close_price": 1380000,
        "avg_dom": 32, "median_dom": 28, "months_of_inventory": 2.8,
        "sale_to_list_ratio": 98.7, "close_to_list_ratio": 98.7,
        "avg_ppsf": 628, "min_price": 495000, "max_price": 4250000,
        "avg_sqft": 2340, "new_listings_7d": 23, "total_volume": 171180000,
        "property_types": {"sfr": 218, "condo": 72, "townhome": 41, "other": 16},
        "price_tiers": {"entry": 127, "moveup": 148, "luxury": 72,
                        "entry_range": "Under $750K", "moveup_range": "$750K - $1.5M", "luxury_range": "$1.5M+"},
        "saturday_count": 18, "sunday_count": 24,
        "bands": [
            {"name": "Entry Level", "range": "$400K - $750K", "count": 127},
            {"name": "Move-Up", "range": "$750K - $1.5M", "count": 148},
            {"name": "Premium", "range": "$1.5M - $2.5M", "count": 52},
            {"name": "Luxury", "range": "$2.5M+", "count": 20},
        ],
    }

    REPORT_TYPES = [
        ("market_snapshot",      "Market Snapshot"),
        ("new_listings",         "New Listings"),
        ("inventory",            "Inventory"),
        ("closed",               "Closed Sales"),
        ("price_bands",          "Price Bands"),
        ("open_houses",          "Open Houses"),
        ("new_listings_gallery", "New Listings Gallery"),
        ("featured_listings",    "Featured Listings"),
    ]

    NEEDS_LISTINGS = {"new_listings_gallery", "featured_listings", "inventory", "closed"}

    results = []
    for i, (rt, label) in enumerate(REPORT_TYPES, start=5):
        listings = LISTINGS if rt in NEEDS_LISTINGS else None
        html = schedule_email_html(
            account_name="Demo Title Company",
            report_type=rt,
            city="Los Angeles",
            zip_codes=["90046", "90069"],
            lookback_days=30,
            metrics=METRICS,
            pdf_url="https://example.com/report.pdf",
            unsubscribe_url="https://example.com/unsubscribe",
            brand=BRAND,
            listings=listings,
            sender_type="INDUSTRY_AFFILIATE",
            total_found=len(listings) if listings else 0,
            total_shown=len(listings) if listings else 0,
        )
        p = OUTPUT_DIR / f"{i:02d}_report_{rt}.html"
        p.write_text(html, encoding="utf-8")
        results.append((f"Report: {label}", f"Scheduled or ad-hoc delivery", p))

    return results


def build_index(all_results):
    """Build an HTML index page linking to all notifications."""
    rows = ""
    for i, (name, trigger, path) in enumerate(all_results, 1):
        category = "Transactional" if i <= 4 else "Report Delivery"
        cat_color = "#7C3AED" if i <= 4 else "#DC2626"
        rows += f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;">
            <span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;
              background:{cat_color}12;color:{cat_color};">{category}</span>
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;">
            <a href="{path.name}" style="color:#1d4ed8;text-decoration:none;font-weight:600;">{name}</a>
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;color:#6b7280;font-size:13px;">{trigger}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;color:#9ca3af;font-size:12px;font-family:monospace;">{path.name}</td>
        </tr>"""

    index = f"""<!DOCTYPE html>
<html><head><title>All TrendyReports Notifications</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 960px; margin: 40px auto; padding: 0 20px; color: #1e293b; }}
  h1 {{ font-size: 28px; margin-bottom: 4px; }}
  .sub {{ color: #64748b; margin-bottom: 32px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ text-align: left; padding: 10px 16px; background: #f8fafc; font-size: 12px; text-transform: uppercase;
       letter-spacing: 0.5px; color: #64748b; border-bottom: 2px solid #e2e8f0; }}
  tr:hover {{ background: #f8fafc; }}
  a:hover {{ text-decoration: underline; }}
</style></head><body>
<h1>TrendyReports — All Notifications</h1>
<p class="sub">{len(all_results)} email templates &bull; Transactional (Resend) + Report Delivery (SendGrid)</p>
<table>
  <thead><tr><th>Category</th><th>Email</th><th>Trigger</th><th>File</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
</body></html>"""

    p = OUTPUT_DIR / "index.html"
    p.write_text(index, encoding="utf-8")
    return p


def main():
    parser = argparse.ArgumentParser(description="Generate all TrendyReports notification emails")
    parser.add_argument("--no-open", action="store_true", help="Don't open in browser")
    args = parser.parse_args()

    print("=" * 60)
    print("  TrendyReports — All Notifications Generator")
    print("=" * 60)
    print()

    print("  Transactional emails (Resend):")
    transactional = gen_transactional()
    for name, trigger, path in transactional:
        print(f"    [OK] {name:30s} -> {path.name}")

    print()
    print("  Report delivery emails (SendGrid):")
    reports = gen_report_emails()
    for name, trigger, path in reports:
        print(f"    [OK] {name:30s} -> {path.name}")

    all_results = transactional + reports
    index_path = build_index(all_results)

    print()
    print("=" * 60)
    print(f"  Done! {len(all_results)} notifications generated")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Index:  {index_path}")
    print("=" * 60)

    if not args.no_open:
        system = platform.system()
        if system == "Windows":
            os.startfile(str(index_path))
        elif system == "Darwin":
            subprocess.run(["open", str(index_path)])
        else:
            subprocess.run(["xdg-open", str(index_path)])


if __name__ == "__main__":
    main()
