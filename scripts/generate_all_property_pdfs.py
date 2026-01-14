#!/usr/bin/env python3
"""
generate_all_property_pdfs.py — Generate PDF reports for all 5 property themes

This script generates HTML and PDF files for each property report theme
so you can review them visually.

Usage:
    python scripts/generate_all_property_pdfs.py

Output:
    - output/property_reports/teal_report.html
    - output/property_reports/teal_report.pdf
    - (etc for all 5 themes)

Requirements:
    pip install jinja2 httpx

PDF Generation:
    Uses PDFShift API (same as production). Requires PDFSHIFT_API_KEY env var.
    If not available, only HTML files are generated (open in browser to print).
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import sys
import os

# ============================================================================
# Configuration
# ============================================================================

TEMPLATES_DIR = Path(__file__).parent.parent / "apps/worker/src/worker/templates"
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "property_reports_v2"

# Check both env var names (production uses PDFSHIFT_API_KEY, template shows PDF_API_KEY)
PDFSHIFT_API_KEY = os.getenv("PDFSHIFT_API_KEY") or os.getenv("PDF_API_KEY", "")
PDFSHIFT_API_URL = "https://api.pdfshift.io/v3/convert/pdf"

THEME_TEMPLATES = {
    "teal": "property/teal/teal_report.jinja2",
    "bold": "property/bold/bold_report.jinja2",
    "classic": "property/classic/classic_report.jinja2",
    "modern": "property/modern/modern_report.jinja2",
    "elegant": "property/elegant/elegant_report.jinja2",
}

# ============================================================================
# Custom Jinja2 Filters (must match production)
# ============================================================================

def format_currency(value):
    """Format as $XXX,XXX"""
    if value is None:
        return "-"
    try:
        return f"${int(value):,}"
    except (ValueError, TypeError):
        return "-"


def format_currency_short(value):
    """Format as $XXXk or $X.Xm"""
    if value is None:
        return "-"
    try:
        val = float(value)
        if val >= 1_000_000:
            return f"${val/1_000_000:.1f}m"
        elif val >= 1_000:
            return f"${int(val/1_000)}k"
        return f"${int(val)}"
    except (ValueError, TypeError):
        return "-"


def format_number(value):
    """Format with commas: 1,234"""
    if value is None:
        return "-"
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return "-"


# ============================================================================
# Sample Data (realistic La Verne property)
# ============================================================================

SAMPLE_CONTEXT = {
    "property": {
        "street_address": "1358 5th Street",
        "city": "La Verne",
        "state": "CA",
        "zip_code": "91750",
        "full_address": "1358 5th St, La Verne, CA 91750",
        "owner_name": "HERNANDEZ GERARDO J",
        "secondary_owner": "MENDOZA YESSICA S",
        "mailing_address": "1358 5th St, La Verne, CA 91750",
        "apn": "8381-021-001",
        "county": "LOS ANGELES",
        "census_tract": "4089.00",
        "legal_description": "LOT 44 TR#6654",
        "bedrooms": 2,
        "bathrooms": 1.0,
        "sqft": 786,
        "lot_size": 6155,
        "year_built": 1949,
        "property_type": "Single Family Residential",
        "zoning": "LVPR4.5D*",
        "pool": "None",
        "garage": "1",
        "fireplace": "No",
        "assessed_value": 428248,
        "land_value": 337378,
        "improvement_value": 90870,
        "tax_amount": 5198,
        "tax_year": 2024,
    },
    "agent": {
        "name": "Zoe Noelle",
        "title": "Real Estate Specialist",
        "license": "DRE #01234567",
        "phone": "(213) 309-7286",
        "email": "zoe@trendyreports.com",
        "address": "123 Main St, Los Angeles, CA 90012",
        "photo_url": None,
        "company_name": "TrendyReports",
        "company_short": "TR",
        "company_tagline": "Your Property Partner",
    },
    "images": {
        "hero": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&h=600&fit=crop",
        "aerial_map": "https://images.unsplash.com/photo-1524813686514-a57563d77965?w=800&h=600&fit=crop",
    },
    "comparables": [
        {
            "address": "1889 Bonita Ave, La Verne",
            "sale_price": 631500,
            "sold_date": "5/10/23",
            "sqft": 940,
            "bedrooms": 2,
            "bathrooms": 1,
            "year_built": 1953,
            "lot_size": 7446,
            "price_per_sqft": 671,
            "distance_miles": 0.58,
            "pool": False,
            "map_image_url": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=400&h=300&fit=crop",
        },
        {
            "address": "1507 2nd St, La Verne",
            "sale_price": 635000,
            "sold_date": "3/15/23",
            "sqft": 912,
            "bedrooms": 3,
            "bathrooms": 1,
            "year_built": 1952,
            "lot_size": 6261,
            "price_per_sqft": 696,
            "distance_miles": 0.54,
            "pool": False,
            "map_image_url": "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=400&h=300&fit=crop",
        },
        {
            "address": "1845 Walnut St, La Verne",
            "sale_price": 470000,
            "sold_date": "4/25/22",
            "sqft": 770,
            "bedrooms": 3,
            "bathrooms": 1,
            "year_built": 1910,
            "lot_size": 4917,
            "price_per_sqft": 610,
            "distance_miles": 0.24,
            "pool": False,
            "map_image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&h=300&fit=crop",
        },
        {
            "address": "1848 1st St, La Verne",
            "sale_price": 590000,
            "sold_date": "4/8/22",
            "sqft": 698,
            "bedrooms": 1,
            "bathrooms": 1,
            "year_built": 1950,
            "lot_size": 5500,
            "price_per_sqft": 845,
            "distance_miles": 0.30,
            "pool": True,
            "map_image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=400&h=300&fit=crop",
        },
    ],
    "stats": {
        "total_comps": 4,
        "avg_sqft": 830,
        "avg_beds": 2.25,
        "avg_baths": 1.0,
        "price_low": 470000,
        "price_high": 635000,
        "piq": {
            "distance": "0",
            "sqft": 786,
            "price_per_sqft": 469,
            "year_built": 1949,
            "lot_size": 6155,
            "bedrooms": 2,
            "bathrooms": 1,
            "price": 369000,
            "stories": 1,
            "pools": 0,
        },
        "low": {
            "distance": "0.24",
            "sqft": 698,
            "price_per_sqft": 610,
            "year_built": 1910,
            "lot_size": 4917,
            "bedrooms": 1,
            "bathrooms": 1,
            "price": 470000,
            "stories": 1,
            "pools": 0,
        },
        "medium": {
            "distance": "0.54",
            "sqft": 912,
            "price_per_sqft": 696,
            "year_built": 1952,
            "lot_size": 6261,
            "bedrooms": 3,
            "bathrooms": 1,
            "price": 610750,
            "stories": 1,
            "pools": 0,
        },
        "high": {
            "distance": "0.58",
            "sqft": 940,
            "price_per_sqft": 845,
            "year_built": 1953,
            "lot_size": 7446,
            "bedrooms": 3,
            "bathrooms": 1,
            "price": 635000,
            "stories": 1,
            "pools": 1,
        },
    },
}


# ============================================================================
# Main Generation Logic
# ============================================================================

def create_jinja_env():
    """Create Jinja2 environment with custom filters."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True
    )
    env.filters['format_currency'] = format_currency
    env.filters['format_currency_short'] = format_currency_short
    env.filters['format_number'] = format_number
    return env


def generate_html(env, theme: str) -> str:
    """Generate HTML for a theme."""
    template_path = THEME_TEMPLATES[theme]
    template = env.get_template(template_path)
    return template.render(**SAMPLE_CONTEXT)


def generate_pdf_pdfshift(html: str, output_path: Path) -> bool:
    """Generate PDF using PDFShift API (same as production)."""
    try:
        import httpx
    except ImportError:
        print("  [WARN] httpx not installed. Run: pip install httpx")
        return False
    
    if not PDFSHIFT_API_KEY:
        return False
    
    payload = {
        "source": html,
        "sandbox": False,
        "use_print": True,
        "format": "Letter",
        "margin": {"top": "0", "right": "0", "bottom": "0", "left": "0"},
        "remove_blank": True,
        "delay": 3000,
        "wait_for_network": True,
        "lazy_load_images": True,
        "timeout": 60,
    }
    
    headers = {
        "X-API-Key": PDFSHIFT_API_KEY,
        "Content-Type": "application/json",
        "X-Processor-Version": "142"
    }
    
    try:
        response = httpx.post(
            PDFSHIFT_API_URL,
            json=payload,
            headers=headers,
            timeout=90.0
        )
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        print(f"  [WARN] PDFShift error: {e}")
        return False


def main():
    """Generate all theme reports."""
    print("=" * 60)
    print("Property Report Template Generator")
    print("=" * 60)
    print()
    
    # Check templates directory exists
    if not TEMPLATES_DIR.exists():
        print(f"[ERROR] Templates directory not found: {TEMPLATES_DIR}")
        sys.exit(1)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OUTPUT] Output directory: {OUTPUT_DIR}")
    print()
    
    # Create Jinja2 environment
    env = create_jinja_env()
    
    # Check if PDFShift is available
    if PDFSHIFT_API_KEY:
        print("[OK] PDFShift API key found - will generate PDFs")
        pdf_available = True
    else:
        print("[INFO] No PDFSHIFT_API_KEY found")
        print("       HTML files will be generated - open in browser and Print to PDF")
        print("       Or set PDFSHIFT_API_KEY env var to generate PDFs automatically")
        pdf_available = False
    print()
    
    # Generate for each theme
    results = []
    for theme in THEME_TEMPLATES.keys():
        print(f"[THEME] Generating {theme.upper()} theme...")
        
        try:
            # Generate HTML
            html = generate_html(env, theme)
            html_path = OUTPUT_DIR / f"{theme}_report.html"
            html_path.write_text(html, encoding='utf-8')
            print(f"   [OK] HTML: {html_path.name}")
            
            # Generate PDF if PDFShift is available
            if pdf_available:
                pdf_path = OUTPUT_DIR / f"{theme}_report.pdf"
                if generate_pdf_pdfshift(html, pdf_path):
                    size_kb = pdf_path.stat().st_size / 1024
                    print(f"   [OK] PDF:  {pdf_path.name} ({size_kb:.1f} KB)")
                    results.append((theme, True, True))
                else:
                    results.append((theme, True, False))
            else:
                results.append((theme, True, None))
                
        except Exception as e:
            print(f"   [ERROR] {e}")
            results.append((theme, False, False))
        
        print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()
    print(f"{'Theme':<12} {'HTML':<10} {'PDF':<10}")
    print("-" * 32)
    for theme, html_ok, pdf_ok in results:
        html_status = "OK" if html_ok else "FAIL"
        if pdf_ok is None:
            pdf_status = "N/A"
        elif pdf_ok:
            pdf_status = "OK"
        else:
            pdf_status = "FAIL"
        print(f"{theme:<12} {html_status:<10} {pdf_status:<10}")
    
    print()
    print(f"[OUTPUT] Files saved to: {OUTPUT_DIR}")
    
    if not pdf_available:
        print()
        print("[TIP] To generate PDFs:")
        print("      1. Open the HTML files in Chrome/Edge")
        print("      2. Press Ctrl+P (or Cmd+P on Mac)")
        print("      3. Select 'Save as PDF'")
        print("      4. Set margins to 'None' and enable 'Background graphics'")
    
    print()


if __name__ == "__main__":
    main()
