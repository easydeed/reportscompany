"""HTML email template for scheduled report notifications.

V4: PDF-aligned redesign - email now mirrors the PDF report structure.
- NEW: Title format "Market Snapshot – [Area]" (matches PDF header)
- NEW: Subline "Period: Last X days • Source: Live MLS Data"  
- NEW: Insight paragraph with 1-2 sentence market summary
- NEW: 4-metric Hero Row (Median Price, Closed Sales, DOM, MOI)
- NEW: Core Indicators section (New Listings, Pending, Sale-to-List)
- IMPROVED: Structured segmentation sections (Property Type, Price Tier)
- Goal: Email feels like the cover page of the PDF report

V3.1: Monochromatic color refinement for mature, sophisticated design.
- UNIFIED metric colors: All 3 metrics use primary_color only
- REMOVED hardcoded teal (#0d9488) - now uses brand primary_color
- NEUTRAL extra stats: Values use dark gray (#1e293b) instead of colored text
- MONOCHROMATIC price tiers: All use primary_color with opacity variations
- Accent color reserved for header gradient only

V3: Professional styling refresh with enhanced Market Snapshot data.
- Table-based layout for maximum email client compatibility
- MSO/Outlook conditional comments for rounded buttons and circular photos
- VML fallback for Outlook gradient headers
- Dark mode support
- Mobile responsive (metrics stack on mobile)
- Full white-label branding support
"""
from typing import Dict, Optional, TypedDict, Tuple, List


class Brand(TypedDict, total=False):
    """Brand configuration for white-label emails."""
    display_name: str
    logo_url: Optional[str]
    email_logo_url: Optional[str]  # Separate logo for email headers (light version)
    primary_color: Optional[str]
    accent_color: Optional[str]
    rep_name: Optional[str]
    rep_title: Optional[str]
    rep_photo_url: Optional[str]
    rep_phone: Optional[str]
    rep_email: Optional[str]
    contact_line1: Optional[str]
    contact_line2: Optional[str]
    website_url: Optional[str]


# Report type display names and taglines
# V4: market_snapshot uses PDF-aligned structure with 4-metric hero + core indicators
REPORT_CONFIG = {
    "market_snapshot": {
        "label": "Market Snapshot",
        "tagline": None,  # V4: Uses "Market Snapshot – [Area]" instead of generic tagline
        "section": None,  # V4: No section label - structured sections instead
        "has_extra_stats": False,  # V4: MOI now in hero row
        "has_property_types": True,
        "has_price_tiers": True,
        "has_hero_4": True,  # V4: 4-metric hero row (Median, Closed, DOM, MOI)
        "has_core_indicators": True,  # V4: Core indicators section (New, Pending, CTL)
        "has_insight": True,  # V4: Insight paragraph
    },
    "new_listings": {
        "label": "New Listings",
        "tagline": None,  # V4: Uses PDF-aligned title
        "section": None,
        "has_extra_stats": False,
        "has_hero_4": True,  # V4: 4-metric hero row
        "has_insight": True,  # V4: Insight paragraph
    },
    "inventory": {
        "label": "Inventory Report",
        "tagline": None,  # V4: Uses PDF-aligned title
        "section": None,
        "has_extra_stats": False,
        "has_hero_4": True,  # V4: 4-metric hero row
        "has_insight": True,  # V4: Insight paragraph
    },
    "closed": {
        "label": "Closed Sales",
        "tagline": None,  # V4: Uses PDF-aligned title
        "section": None,
        "has_extra_stats": False,  # V4: Integrated into hero row
        "has_hero_4": True,  # V4: 4-metric hero row
        "has_insight": True,  # V4: Insight paragraph
    },
    "price_bands": {
        "label": "Price Analysis",
        "tagline": None,  # V4: Uses PDF-aligned title
        "section": None,
        "has_extra_stats": False,
        "has_price_bands": True,
        "has_hero_4": True,  # V4: 4-metric hero row
        "has_insight": True,  # V4: Insight paragraph
    },
    "open_houses": {
        "label": "Open Houses",
        "tagline": "Open This Weekend",
        "section": "Open Houses",
        "has_extra_stats": False,
    },
    "new_listings_gallery": {
        "label": "New Listings Gallery",
        "tagline": "The Newest Properties",
        "section": "Photo Gallery",
        "has_extra_stats": False,
    },
    "featured_listings": {
        "label": "Featured Listings",
        "tagline": "Premium Properties",
        "section": "Featured Properties",
        "has_extra_stats": False,
    },
}


def _format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None:
        return "N/A"
    if price >= 1_000_000:
        return f"${price / 1_000_000:.2f}M".rstrip('0').rstrip('.')  + "M" if price % 1_000_000 == 0 else f"${price / 1_000_000:.2f}M"
    if price >= 1_000:
        return f"${price / 1_000:.0f}K"
    return f"${price:,.0f}"


def _format_price_clean(price: Optional[float]) -> str:
    """Format price for display - cleaner version."""
    if price is None:
        return "N/A"
    if price >= 1_000_000:
        m = price / 1_000_000
        if m == int(m):
            return f"${int(m)}M"
        return f"${m:.1f}M"
    if price >= 1_000:
        k = price / 1_000
        if k == int(k):
            return f"${int(k)}K"
        return f"${k:.0f}K"
    return f"${price:,.0f}"


def _format_number(value: Optional[int]) -> str:
    """Format number for display."""
    if value is None:
        return "N/A"
    return f"{value:,}"


def _format_percent(value: Optional[float]) -> str:
    """Format percentage for display."""
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


def _format_decimal(value: Optional[float], decimals: int = 1) -> str:
    """Format decimal for display."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def _get_metrics_for_report_type(
    report_type: str, 
    metrics: Dict
) -> Tuple[Tuple[str, str], Tuple[str, str], Tuple[str, str]]:
    """
    Get the 3 main metrics to display based on report type.
    Returns: ((label1, value1), (label2, value2), (label3, value3))
    """
    # Extract common metrics with defaults
    total_active = metrics.get("total_active", 0)
    total_pending = metrics.get("total_pending", 0)
    total_closed = metrics.get("total_closed", 0)
    total_listings = metrics.get("total_listings", total_active)
    new_this_month = metrics.get("new_this_month", 0)
    median_list_price = metrics.get("median_list_price")
    median_close_price = metrics.get("median_close_price")
    avg_dom = metrics.get("avg_dom")
    median_dom = metrics.get("median_dom", avg_dom)
    
    # Format DOM
    dom_display = f"{avg_dom:.0f}" if avg_dom else "N/A"
    median_dom_display = f"{median_dom:.0f}" if median_dom else dom_display
    
    if report_type == "market_snapshot":
        return (
            ("Active Listings", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_close_price or median_list_price)),
            ("Avg DOM", f"{dom_display} days" if dom_display != "N/A" else "N/A"),
        )
    
    elif report_type == "new_listings":
        return (
            ("New Listings", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Avg DOM", f"{dom_display} days" if dom_display != "N/A" else "N/A"),
        )
    
    elif report_type == "closed":
        return (
            ("Homes Sold", _format_number(total_closed)),
            ("Median Price", _format_price_clean(median_close_price)),
            ("Avg Days to Sell", f"{dom_display}" if dom_display != "N/A" else "N/A"),
        )
    
    elif report_type == "new_listings_gallery":
        return (
            ("New Listings", _format_number(total_listings)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Starting At", _format_price_clean(metrics.get("min_price"))),
        )
    
    elif report_type == "featured_listings":
        return (
            ("Featured Homes", _format_number(total_listings)),
            ("Highest Price", _format_price_clean(metrics.get("max_price"))),
            ("Avg Sq Ft", _format_number(metrics.get("avg_sqft"))),
        )
    
    elif report_type == "inventory":
        return (
            ("Active Listings", _format_number(total_active)),
            ("New This Month", _format_number(new_this_month)),
            ("Median DOM", f"{median_dom_display} days" if median_dom_display != "N/A" else "N/A"),
        )
    
    elif report_type == "price_bands":
        band_count = len(metrics.get("bands", [])) or 3
        return (
            ("Total Listings", _format_number(total_active or total_listings)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Price Tiers", str(band_count)),
        )
    
    elif report_type == "open_houses":
        return (
            ("Open Houses", _format_number(total_active)),
            ("Saturday", _format_number(metrics.get("saturday_count", 0))),
            ("Sunday", _format_number(metrics.get("sunday_count", 0))),
        )
    
    else:
        # Generic fallback
        return (
            ("Properties", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Avg DOM", f"{dom_display} days" if dom_display != "N/A" else "N/A"),
        )


def _get_extra_stats(report_type: str, metrics: Dict) -> Optional[Tuple[Tuple[str, str], Tuple[str, str]]]:
    """
    Get extra stats for reports that support them.
    Returns: ((label1, value1), (label2, value2)) or None
    """
    if report_type == "market_snapshot":
        moi = metrics.get("months_of_inventory")
        ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
        moi_display = _format_decimal(moi) if moi else "N/A"
        ctl_display = _format_percent(ctl) if ctl else "N/A"
        return (
            (moi_display, "Months of Inventory"),
            (ctl_display, "Close-to-List Ratio"),
        )
    
    elif report_type == "closed":
        ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
        volume = metrics.get("total_volume")
        ctl_display = _format_percent(ctl) if ctl else "N/A"
        volume_display = _format_price_clean(volume) if volume else "N/A"
        return (
            (ctl_display, "Close-to-List Ratio"),
            (volume_display, "Total Volume"),
        )
    
    return None


def _get_price_bands(metrics: Dict) -> Optional[List[Dict]]:
    """
    Get price bands for price_bands report.
    Returns list of {name, range, count, color} or None
    
    V3.1: Uses monochromatic PRIMARY color for all bands for visual cohesion.
    """
    bands = metrics.get("bands", [])
    if not bands:
        # Try to construct from individual fields
        entry_count = metrics.get("entry_count")
        if entry_count is not None:
            return [
                {
                    "name": "Entry Level",
                    "range": metrics.get("entry_range", "$0 - Median"),
                    "count": entry_count,
                    "color": "PRIMARY",  # Monochromatic
                },
                {
                    "name": "Move-Up",
                    "range": metrics.get("moveup_range", "Median - 75th"),
                    "count": metrics.get("moveup_count", 0),
                    "color": "PRIMARY",  # Monochromatic
                },
                {
                    "name": "Luxury",
                    "range": metrics.get("luxury_range", "75th+"),
                    "count": metrics.get("luxury_count", 0),
                    "color": "PRIMARY",  # Monochromatic
                },
            ]
    
    # Map bands from metrics - all use PRIMARY for monochromatic design
    if bands:
        return [
            {
                "name": b.get("name", f"Band {i+1}"),
                "range": b.get("range", ""),
                "count": b.get("count", 0),
                "color": "PRIMARY",  # Monochromatic
            }
            for i, b in enumerate(bands)
        ]
    
    return None


def _get_property_type_breakdown(metrics: Dict) -> Optional[List[Dict]]:
    """
    Get property type breakdown for Market Snapshot.
    Returns list of {name, count, icon} or None
    
    V4.1: Updated to modern, minimal icons
    """
    # Try to get from metrics
    property_types = metrics.get("property_types", {})
    
    # Also check for individual fields
    sfr_count = property_types.get("sfr") or metrics.get("sfr_count", 0)
    condo_count = property_types.get("condo") or metrics.get("condo_count", 0)
    townhome_count = property_types.get("townhome") or metrics.get("townhome_count", 0)
    other_count = property_types.get("other") or metrics.get("other_type_count", 0)
    
    # If we have any counts, return the breakdown
    # V4.1: Modern icons - ◼ squares with labels
    if sfr_count or condo_count or townhome_count or other_count:
        result = []
        if sfr_count:
            result.append({"name": "Single Family", "count": sfr_count, "icon": "▪"})
        if condo_count:
            result.append({"name": "Condos", "count": condo_count, "icon": "▪"})
        if townhome_count:
            result.append({"name": "Townhomes", "count": townhome_count, "icon": "▪"})
        if other_count:
            result.append({"name": "Other", "count": other_count, "icon": "▪"})
        return result if result else None
    
    return None


def _get_price_tier_breakdown(metrics: Dict) -> Optional[List[Dict]]:
    """
    Get price tier breakdown for Market Snapshot.
    Returns list of {name, count, range, color} or None
    """
    # Try to get from metrics
    price_tiers = metrics.get("price_tiers", {})
    
    # Also check for individual fields
    entry_count = price_tiers.get("entry") or metrics.get("entry_tier_count", 0)
    moveup_count = price_tiers.get("moveup") or metrics.get("moveup_tier_count", 0)
    luxury_count = price_tiers.get("luxury") or metrics.get("luxury_tier_count", 0)
    
    # Get ranges if available
    entry_range = price_tiers.get("entry_range") or metrics.get("entry_tier_range", "Under $500K")
    moveup_range = price_tiers.get("moveup_range") or metrics.get("moveup_tier_range", "$500K - $1M")
    luxury_range = price_tiers.get("luxury_range") or metrics.get("luxury_tier_range", "$1M+")
    
    # If we have any counts, return the breakdown
    # Using PRIMARY for all tiers - opacity variations applied in template
    if entry_count or moveup_count or luxury_count:
        return [
            {"name": "Entry Level", "count": entry_count, "range": entry_range, "color": "PRIMARY", "opacity": "40"},
            {"name": "Move-Up", "count": moveup_count, "range": moveup_range, "color": "PRIMARY", "opacity": "70"},
            {"name": "Luxury", "count": luxury_count, "range": luxury_range, "color": "PRIMARY", "opacity": "100"},
        ]
    
    return None


# ============================================================================
# V4 FUNCTIONS: PDF-aligned email structure for Market Snapshot
# ============================================================================

def _get_hero_4_metrics(report_type: str, metrics: Dict) -> Tuple[
    Tuple[str, str], Tuple[str, str], Tuple[str, str], Tuple[str, str]
]:
    """
    V4: Get 4 hero metrics that match the PDF report header.
    Returns: ((label1, value1), (label2, value2), (label3, value3), (label4, value4))
    
    Each report type has its own relevant metrics matching the PDF ribbon.
    """
    # Extract common metrics
    median_close_price = metrics.get("median_close_price")
    median_list_price = metrics.get("median_list_price")
    total_active = metrics.get("total_active", 0)
    total_closed = metrics.get("total_closed", 0)
    avg_dom = metrics.get("avg_dom")
    moi = metrics.get("months_of_inventory")
    avg_ppsf = metrics.get("avg_ppsf")
    ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
    new_this_month = metrics.get("new_this_month", total_active)
    
    if report_type == "market_snapshot":
        # Matches PDF: Median Sale Price, Closed Sales, Avg DOM, MOI
        return (
            ("Median Sale Price", _format_price_clean(median_close_price or median_list_price)),
            ("Closed Sales", _format_number(total_closed)),
            ("Avg Days on Market", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Months of Inventory", f"{moi:.1f}" if moi else "N/A"),
        )
    
    elif report_type == "new_listings":
        # Matches PDF: Total Listings, Median List Price, Avg DOM, Avg $/SqFt
        return (
            ("New Listings", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Avg DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Avg $/SqFt", _format_price_clean(avg_ppsf) if avg_ppsf else "N/A"),
        )
    
    elif report_type == "inventory":
        # Matches PDF: Active Listings, New This Month, Median DOM, MOI
        return (
            ("Active Listings", _format_number(total_active)),
            ("New This Month", _format_number(new_this_month)),
            ("Median DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Months of Inventory", f"{moi:.1f}" if moi else "N/A"),
        )
    
    elif report_type == "closed":
        # Matches PDF: Total Closed, Median Close Price, Avg DOM, Close-to-List
        return (
            ("Total Closed", _format_number(total_closed)),
            ("Median Price", _format_price_clean(median_close_price)),
            ("Avg DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Close-to-List", f"{ctl:.1f}%" if ctl else "N/A"),
        )
    
    elif report_type == "price_bands":
        # Matches PDF: Total Listings, Median Price, Avg DOM, Price Range
        min_price = metrics.get("min_price")
        max_price = metrics.get("max_price")
        price_range = f"{_format_price_clean(min_price)}-{_format_price_clean(max_price)}" if min_price and max_price else "N/A"
        return (
            ("Total Listings", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Avg DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Price Range", price_range),
        )
    
    else:
        # Generic fallback
        return (
            ("Properties", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price or median_close_price)),
            ("Avg DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("MOI", f"{moi:.1f}" if moi else "N/A"),
        )


def _get_core_indicators(metrics: Dict) -> Tuple[
    Tuple[str, str], Tuple[str, str], Tuple[str, str]
]:
    """
    V4: Get 3 core indicator metrics that match the PDF report.
    Returns: ((label1, value1), (label2, value2), (label3, value3))
    
    PDF Core Indicators:
    1. New Listings (or Active Listings if new not available)
    2. Pending Sales
    3. Sale-to-List Ratio
    """
    # Extract metrics
    new_listings = metrics.get("new_listings_7d") or metrics.get("total_active", 0)
    total_pending = metrics.get("total_pending", 0)
    ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
    
    # Format values
    new_val = _format_number(new_listings)
    pending_val = _format_number(total_pending)
    ctl_val = f"{ctl:.1f}%" if ctl else "N/A"
    
    return (
        ("New Listings", new_val),
        ("Pending Sales", pending_val),
        ("Sale-to-List Ratio", ctl_val),
    )


def _get_insight_paragraph(report_type: str, area: str, metrics: Dict, lookback_days: int) -> str:
    """
    V4: Generate insight paragraph for reports.
    This mirrors the PDF's introductory narrative paragraph.
    
    Can be enhanced with AI later, but starts with template-based text.
    """
    # Extract key metrics for narrative
    total_active = metrics.get("total_active", 0)
    total_closed = metrics.get("total_closed", 0)
    median_price = metrics.get("median_close_price") or metrics.get("median_list_price")
    avg_dom = metrics.get("avg_dom")
    moi = metrics.get("months_of_inventory")
    avg_ppsf = metrics.get("avg_ppsf")
    ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
    
    # Build insight text based on report type
    price_str = _format_price_clean(median_price) if median_price else "varying prices"
    dom_str = f"{avg_dom:.0f} days" if avg_dom else "average time"
    
    if report_type == "market_snapshot":
        # Market condition based on MOI
        if moi and moi < 3:
            market_condition = "a seller's market with limited inventory"
        elif moi and moi > 6:
            market_condition = "a buyer's market with ample inventory"
        else:
            market_condition = "a balanced market"
        
        return (
            f"This snapshot provides key market indicators for {area} over the last {lookback_days} days. "
            f"With {total_closed} closed sales at a median of {price_str} and homes averaging {dom_str} on market, "
            f"the data suggests {market_condition}."
        )
    
    elif report_type == "new_listings":
        ppsf_str = _format_price_clean(avg_ppsf) if avg_ppsf else "competitive"
        return (
            f"Discover the newest properties listed in {area} over the last {lookback_days} days. "
            f"With {total_active} fresh listings at a median of {price_str} and {ppsf_str} per square foot, "
            f"there are opportunities across all price points."
        )
    
    elif report_type == "inventory":
        if moi and moi < 3:
            supply_condition = "supply is tight and competition may be high"
        elif moi and moi > 6:
            supply_condition = "buyers have plenty of options to choose from"
        else:
            supply_condition = "there's a healthy balance of supply and demand"
        
        return (
            f"Current inventory snapshot for {area}. "
            f"With {total_active} active listings at a median of {price_str} and homes averaging {dom_str} on market, "
            f"{supply_condition}."
        )
    
    elif report_type == "closed":
        ctl_str = f"{ctl:.1f}%" if ctl else "competitive"
        return (
            f"Recent sales activity in {area} over the last {lookback_days} days. "
            f"{total_closed} homes sold at a median of {price_str}, averaging {dom_str} to close. "
            f"The close-to-list ratio of {ctl_str} indicates market strength."
        )
    
    elif report_type == "price_bands":
        return (
            f"Price analysis for {area} over the last {lookback_days} days. "
            f"This report segments the market into price ranges to identify where inventory and buyer activity "
            f"are concentrated. Faster-moving bands indicate stronger demand."
        )
    
    else:
        return (
            f"Market report for {area} covering the last {lookback_days} days. "
            f"Median price: {price_str}. Average days on market: {dom_str}."
        )


def _build_preheader(report_type: str, area: str, metrics: Dict) -> str:
    """Build preheader text for email preview."""
    config = REPORT_CONFIG.get(report_type, {})
    label = config.get("label", "Report")
    
    # Get a key metric for the preheader
    if report_type == "market_snapshot":
        count = metrics.get("total_active", 0)
        return f"📊 {label} for {area}: {count} active listings, see median prices and market trends"
    elif report_type == "new_listings":
        count = metrics.get("total_active", 0)
        return f"🏠 {count} new listings in {area} - see prices, photos, and details"
    elif report_type == "closed":
        count = metrics.get("total_closed", 0)
        return f"🔑 {count} homes sold in {area} - see sale prices and market activity"
    elif report_type == "price_bands":
        return f"💰 Price analysis for {area} - see entry, move-up, and luxury tiers"
    elif report_type == "inventory":
        count = metrics.get("total_active", 0)
        return f"📋 {count} active listings in {area} - current market availability"
    else:
        return f"📊 Your {label} for {area} is ready to view"


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
) -> str:
    """
    Generate HTML email for a scheduled report notification.
    
    V2: Complete redesign with V0-generated email-safe template.
    Features:
    - Gradient header with Outlook VML fallback
    - Dark mode support
    - Mobile responsive (metrics stack)
    - Extra stats row for Market Snapshot & Closed Sales
    - Price bands section for Price Bands report
    - Preheader text for email preview
    - Polished agent footer with circular photo
    
    Args:
        account_name: Name of the account (for personalization)
        report_type: Type of report (market_snapshot, new_listings, etc.)
        city: City name (if city-based report)
        zip_codes: List of ZIP codes (if ZIP-based report)
        lookback_days: Number of days covered by the report
        metrics: Dictionary of key metrics to display
        pdf_url: Direct link to the PDF report
        unsubscribe_url: Link to unsubscribe from future emails
        brand: Optional brand configuration (for white-label output)
    
    Returns:
        HTML string for the email body
    """
    # Extract brand values with defaults
    brand = brand or {}
    brand_name = brand.get("display_name") or account_name or "Market Reports"
    logo_url = brand.get("logo_url")
    email_logo_url = brand.get("email_logo_url")  # Separate logo for email headers
    primary_color = brand.get("primary_color") or "#6366f1"  # Indigo
    accent_color = brand.get("accent_color") or "#8b5cf6"    # Purple
    rep_name = brand.get("rep_name")
    rep_title = brand.get("rep_title")
    rep_photo_url = brand.get("rep_photo_url")
    rep_phone = brand.get("rep_phone")
    rep_email = brand.get("rep_email")
    contact_line1 = brand.get("contact_line1") or rep_name
    contact_line2 = brand.get("contact_line2") or rep_title
    website_url = brand.get("website_url")
    
    # Get report config
    config = REPORT_CONFIG.get(report_type, {
        "label": report_type.replace("_", " ").title(),
        "tagline": "Your Market Report",
        "section": "Market Overview",
    })
    report_label = config.get("label")
    tagline = config.get("tagline")
    section_label = config.get("section")
    has_extra_stats = config.get("has_extra_stats", False)
    has_price_bands = config.get("has_price_bands", False)
    has_property_types = config.get("has_property_types", False)
    has_price_tiers = config.get("has_price_tiers", False)
    
    # V4 features
    has_hero_4 = config.get("has_hero_4", False)
    has_core_indicators = config.get("has_core_indicators", False)
    has_insight = config.get("has_insight", False)
    
    # Format area for display
    if city:
        area_display = city
    elif zip_codes and len(zip_codes) > 0:
        if len(zip_codes) == 1:
            area_display = f"ZIP {zip_codes[0]}"
        elif len(zip_codes) <= 3:
            area_display = f"ZIPs {', '.join(zip_codes)}"
        else:
            area_display = f"{len(zip_codes)} ZIP codes"
    else:
        area_display = "Your Area"
    
    # Date range display
    date_range = f"Last {lookback_days} Days"
    
    # V4: Get 4-metric hero row (for all V4 report types)
    if has_hero_4:
        (h1_label, h1_value), (h2_label, h2_value), (h3_label, h3_value), (h4_label, h4_value) = \
            _get_hero_4_metrics(report_type, metrics)
    
    # V4: Get core indicators for Market Snapshot
    if has_core_indicators:
        (ci1_label, ci1_value), (ci2_label, ci2_value), (ci3_label, ci3_value) = \
            _get_core_indicators(metrics)
    
    # V4: Get insight paragraph
    insight_text = _get_insight_paragraph(report_type, area_display, metrics, lookback_days) if has_insight else None
    
    # Legacy: Get 3 metrics for non-V4 reports
    (m1_label, m1_value), (m2_label, m2_value), (m3_label, m3_value) = \
        _get_metrics_for_report_type(report_type, metrics)
    
    # Get extra stats if applicable (not used in V4 Market Snapshot)
    extra_stats = _get_extra_stats(report_type, metrics) if has_extra_stats else None
    
    # Get price bands if applicable
    price_bands = _get_price_bands(metrics) if has_price_bands else None
    
    # Get property type breakdown if applicable (Market Snapshot)
    property_types = _get_property_type_breakdown(metrics) if has_property_types else None
    
    # Get price tier breakdown if applicable (Market Snapshot)
    price_tiers = _get_price_tier_breakdown(metrics) if has_price_tiers else None
    
    # Build preheader
    preheader = _build_preheader(report_type, area_display, metrics)
    
    # Build logo HTML for email header
    # Use email_logo_url if available (light version for gradient headers)
    # Otherwise, use logo_url (will be displayed on gradient, may need inversion via CSS)
    header_logo = email_logo_url or logo_url
    if header_logo:
        logo_html = f'<img src="{header_logo}" alt="{brand_name}" width="160" style="display: block; max-width: 160px; height: auto;">'
    else:
        logo_html = f'<span style="font-size: 24px; font-weight: 700; color: #ffffff;">{brand_name}</span>'
    
    # Build extra stats HTML (legacy V3)
    extra_stats_html = ""
    if extra_stats:
        (es1_value, es1_label), (es2_value, es2_label) = extra_stats
        extra_stats_html = f'''
              <!-- Extra Stats Row -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px; background-color: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0;">
                <tr>
                  <td align="center" style="padding: 16px 24px;">
                    <span style="font-size: 14px; color: #475569;">
                      <strong style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; color: #1e293b;">{es1_value}</strong>
                      <span style="color: #64748b;"> {es1_label}</span>
                      &nbsp;&nbsp;<span style="color: #cbd5e1;">|</span>&nbsp;&nbsp;
                      <strong style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; color: #1e293b;">{es2_value}</strong>
                      <span style="color: #64748b;"> {es2_label}</span>
                    </span>
                  </td>
                </tr>
              </table>
'''
    
    # ============================================================================
    # V4 HTML SECTIONS (Market Snapshot)
    # ============================================================================
    
    # V4: Insight Paragraph
    insight_html = ""
    if insight_text:
        insight_html = f'''
              <!-- V4: Insight Paragraph -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td style="padding: 16px 20px; background-color: #f8fafc; border-radius: 8px; border-left: 3px solid {primary_color};">
                    <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #475569; font-style: italic;">
                      {insight_text}
                    </p>
                  </td>
                </tr>
              </table>
'''
    
    # V4: 4-Metric Hero Row
    hero_4_html = ""
    if has_hero_4:
        hero_4_html = f'''
              <!-- V4: 4-Metric Hero Row (matches PDF) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <!-- Hero Metric 1: Median Sale Price -->
                  <td width="25%" class="metric-card" style="padding: 0 4px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0;" class="dark-card dark-border">
                      <tr>
                        <td align="center" style="padding: 16px 8px;">
                          <p style="margin: 0 0 4px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 24px; font-weight: 400; color: {primary_color};">
                            {h1_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h1_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <!-- Hero Metric 2: Closed Sales -->
                  <td width="25%" class="metric-card" style="padding: 0 4px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0;" class="dark-card dark-border">
                      <tr>
                        <td align="center" style="padding: 16px 8px;">
                          <p style="margin: 0 0 4px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 24px; font-weight: 400; color: {primary_color};">
                            {h2_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h2_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <!-- Hero Metric 3: Avg DOM -->
                  <td width="25%" class="metric-card" style="padding: 0 4px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0;" class="dark-card dark-border">
                      <tr>
                        <td align="center" style="padding: 16px 8px;">
                          <p style="margin: 0 0 4px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 24px; font-weight: 400; color: {primary_color};">
                            {h3_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h3_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <!-- Hero Metric 4: MOI -->
                  <td width="25%" class="metric-card" style="padding: 0 4px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0;" class="dark-card dark-border">
                      <tr>
                        <td align="center" style="padding: 16px 8px;">
                          <p style="margin: 0 0 4px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 24px; font-weight: 400; color: {primary_color};">
                            {h4_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h4_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
'''
    
    # V4: Core Indicators Section
    core_indicators_html = ""
    if has_core_indicators:
        core_indicators_html = f'''
              <!-- V4: Core Indicators Section (matches PDF) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td style="padding-bottom: 12px;">
                    <p style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1.5px;">
                      Core Indicators
                    </p>
                  </td>
                </tr>
                <tr>
                  <!-- Indicator 1: New Listings -->
                  <td width="33%" class="metric-card" style="padding: 0 4px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                      <tr>
                        <td align="center" style="padding: 14px 8px;">
                          <p style="margin: 0 0 2px 0; font-size: 20px; font-weight: 700; color: {primary_color};">
                            {ci1_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase;">
                            {ci1_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <!-- Indicator 2: Pending Sales -->
                  <td width="33%" class="metric-card" style="padding: 0 4px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                      <tr>
                        <td align="center" style="padding: 14px 8px;">
                          <p style="margin: 0 0 2px 0; font-size: 20px; font-weight: 700; color: {primary_color};">
                            {ci2_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase;">
                            {ci2_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <!-- Indicator 3: Sale-to-List -->
                  <td width="33%" class="metric-card" style="padding: 0 4px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                      <tr>
                        <td align="center" style="padding: 14px 8px;">
                          <p style="margin: 0 0 2px 0; font-size: 20px; font-weight: 700; color: {primary_color};">
                            {ci3_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase;">
                            {ci3_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
'''
    
    # Build price bands HTML - monochromatic design using primary_color only
    price_bands_html = ""
    if price_bands:
        bands_rows = ""
        for i, band in enumerate(price_bands):
            # All bands use primary_color for monochromatic design
            color = primary_color
            
            border = 'border-bottom: 1px solid #e5e7eb;' if i < len(price_bands) - 1 else ''
            bands_rows += f'''
                <!-- {band["name"]} -->
                <tr>
                  <td class="band-row" style="padding: 10px 0; {border}">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td width="12" style="vertical-align: middle;">
                          <div style="width: 10px; height: 10px; background-color: {color}; border-radius: 50%;"></div>
                        </td>
                        <td style="padding-left: 12px; vertical-align: middle;">
                          <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 15px; font-weight: 600; color: #1f2937;">{band["name"]}</span>
                          <span style="font-size: 13px; color: #6b7280; margin-left: 8px;">{band["range"]}</span>
                        </td>
                        <td align="right" style="vertical-align: middle;">
                          <span style="font-size: 15px; font-weight: 600; color: {primary_color};">{band["count"]} listings</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
'''
        
        price_bands_html = f'''
              <!-- Price Bands Section -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td style="padding-bottom: 12px;">
                    <p style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 13px; font-weight: 600; color: #4b5563; text-transform: uppercase; letter-spacing: 1px;">
                      Price Tiers
                    </p>
                  </td>
                </tr>
                {bands_rows}
              </table>
'''
    
    # Build property type breakdown HTML (Market Snapshot)
    # V4.1: Modern styling with colored dots instead of emoji
    property_types_html = ""
    if property_types:
        # Build individual type cards with colored indicators
        type_cards = ""
        type_colors = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b"]  # Blue, Purple, Pink, Amber
        
        for i, ptype in enumerate(property_types):
            color = type_colors[i % len(type_colors)]
            type_cards += f'''
                  <td align="center" style="padding: 8px 12px;">
                    <span style="display: inline-block; width: 8px; height: 8px; background-color: {color}; border-radius: 50%; margin-right: 6px; vertical-align: middle;"></span>
                    <span style="font-size: 14px; color: #374151;">
                      <strong style="color: {primary_color};">{ptype["count"]}</strong> {ptype["name"]}
                    </span>
                  </td>'''
        
        property_types_html = f'''
              <!-- Property Type Breakdown -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px;">
                <tr>
                  <td style="padding: 16px 20px; background-color: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0;">
                    <p style="margin: 0 0 12px 0; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1.5px; text-align: center;">
                      Property Types
                    </p>
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        {type_cards}
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
'''
    
    # Build price tier breakdown HTML (Market Snapshot)
    # V4.1: Added icons, centered text, modern styling
    price_tiers_html = ""
    if price_tiers:
        # Icons for each tier level
        tier_icons = {"Entry Level": "◇", "Move-Up": "◈", "Luxury": "◆"}
        
        tier_items = ""
        for i, tier in enumerate(price_tiers):
            # All tiers use primary_color - opacity creates visual hierarchy
            opacity = tier.get("opacity", "100")
            opacity_hex = {"40": "66", "70": "B3", "100": ""}.get(opacity, "")
            border_color = f"{primary_color}{opacity_hex}"
            icon = tier_icons.get(tier["name"], "▪")
            
            tier_items += f'''
                  <td width="33%" class="metric-card" style="padding: 0 4px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td align="center" style="padding: 14px 8px; background-color: #ffffff; border-radius: 8px; border-top: 3px solid {border_color};">
                          <p style="margin: 0 0 4px 0; font-size: 22px; font-weight: 700; color: {primary_color};">{tier["count"]}</p>
                          <p style="margin: 0 0 2px 0; font-size: 12px; font-weight: 600; color: #374151;">
                            <span style="color: {border_color};">{icon}</span> {tier["name"]}
                          </p>
                          <p style="margin: 0; font-size: 10px; color: #9ca3af;">{tier["range"]}</p>
                        </td>
                      </tr>
                    </table>
                  </td>
'''
        
        price_tiers_html = f'''
              <!-- Price Tier Breakdown -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px; background-color: #f8fafc; border-radius: 10px; padding: 16px; border: 1px solid #e2e8f0;">
                <tr>
                  <td style="padding-bottom: 12px;" colspan="3">
                    <p style="margin: 0; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1.5px; text-align: center;">
                      Price Tier Distribution
                    </p>
                  </td>
                </tr>
                <tr>
                  {tier_items}
                </tr>
              </table>
'''
    
    # Build agent footer HTML
    if rep_photo_url and (contact_line1 or rep_name):
        # Full footer with photo
        contact_info = ""
        if rep_phone or rep_email:
            phone_html = f'<a href="tel:{rep_phone}" style="color: {primary_color}; text-decoration: none;">{rep_phone}</a>' if rep_phone else ""
            email_html = f'<a href="mailto:{rep_email}" style="color: {primary_color}; text-decoration: none;">{rep_email}</a>' if rep_email else ""
            separator = " &bull; " if phone_html and email_html else ""
            contact_info = f'''
                          <p style="margin: 0; font-size: 13px;">
                            {phone_html}{separator}{email_html}
                          </p>'''
        
        agent_footer_html = f'''
              <!-- Agent Footer -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <table role="presentation" cellpadding="0" cellspacing="0">
                      <tr>
                        <!-- Agent Photo -->
                        <td style="vertical-align: middle; padding-right: 20px;">
                          <!--[if mso]>
                          <v:oval xmlns:v="urn:schemas-microsoft-com:vml" style="width:70px;height:70px;" stroke="f">
                            <v:fill type="frame" src="{rep_photo_url}"/>
                          </v:oval>
                          <![endif]-->
                          <!--[if !mso]><!-->
                          <img src="{rep_photo_url}" alt="{contact_line1 or rep_name}" width="70" height="70" style="display: block; width: 70px; height: 70px; border-radius: 50%; object-fit: cover; border: 3px solid {primary_color}20;">
                          <!--<![endif]-->
                        </td>
                        <!-- Agent Info -->
                        <td style="vertical-align: middle;">
                          <p style="margin: 0 0 2px 0; font-size: 17px; font-weight: 600; color: #1a1a2e;" class="dark-text">
                            {contact_line1 or rep_name}
                          </p>
                          {f'<p style="margin: 0 0 8px 0; font-size: 13px; color: #6b7280;">{contact_line2 or rep_title}</p>' if (contact_line2 or rep_title) else ''}
                          {contact_info}
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>'''
    elif contact_line1 or website_url:
        # Contact without photo
        agent_footer_html = f'''
              <!-- Agent Footer -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    {f'<p style="margin: 0 0 4px 0; font-size: 16px; font-weight: 600; color: #1a1a2e;">{contact_line1}</p>' if contact_line1 else ''}
                    {f'<p style="margin: 0 0 8px 0; font-size: 14px; color: #6b7280;">{contact_line2}</p>' if contact_line2 else ''}
                    {f'<a href="{website_url}" style="color: {primary_color}; text-decoration: none; font-weight: 500;">{website_url.replace("https://", "").replace("http://", "")}</a>' if website_url else ''}
                  </td>
                </tr>
              </table>'''
    else:
        # Minimal footer
        agent_footer_html = f'''
              <!-- Agent Footer -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <p style="margin: 0; font-size: 16px; font-weight: 600; color: #1a1a2e;">{brand_name}</p>
                  </td>
                </tr>
              </table>'''
    
    # Powered by (only if not white-labeled)
    powered_by = ""
    if not brand.get("display_name"):
        powered_by = '''
                    <p style="margin: 10px 0 0 0; font-size: 11px; color: #d1d5db;">
                      Powered by TrendyReports
                    </p>'''
    
    # Build the complete HTML email
    html = f'''<!DOCTYPE html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="x-apple-disable-message-reformatting">
  <meta name="color-scheme" content="light dark">
  <meta name="supported-color-schemes" content="light dark">
  <title>{brand_name} - {report_label}</title>
  
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:AllowPNG/>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
  
  <style>
    /* Reset */
    body, table, td, p, a, li {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
    table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
    img {{ -ms-interpolation-mode: bicubic; border: 0; height: auto; line-height: 100%; outline: none; text-decoration: none; }}
    body {{ margin: 0 !important; padding: 0 !important; width: 100% !important; }}
    
    /* Dark Mode */
    @media (prefers-color-scheme: dark) {{
      .dark-bg {{ background-color: #1a1a2e !important; }}
      .dark-text {{ color: #e5e5e5 !important; }}
      .dark-card {{ background-color: #262640 !important; }}
      .dark-border {{ border-color: #3d3d5c !important; }}
    }}
    
    /* Mobile */
    @media only screen and (max-width: 600px) {{
      .wrapper {{ width: 100% !important; }}
      .mobile-padding {{ padding: 20px !important; }}
      .mobile-stack {{ display: block !important; width: 100% !important; }}
      .mobile-center {{ text-align: center !important; }}
      .mobile-hide {{ display: none !important; }}
      .metric-card {{ display: block !important; width: 100% !important; margin-bottom: 12px !important; }}
      .band-row {{ display: block !important; width: 100% !important; }}
    }}
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
  
  <!-- Preheader Text (hidden preview text) -->
  <div style="display: none; max-height: 0; overflow: hidden; mso-hide: all;">
    {preheader} &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
  </div>
  
  <!-- Email Container -->
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc;" class="dark-bg">
    <tr>
      <td align="center" style="padding: 40px 20px;">
        
        <!-- Email Wrapper -->
        <table role="presentation" cellpadding="0" cellspacing="0" width="600" class="wrapper" style="max-width: 600px; width: 100%;">
          
          <!-- ========== HEADER WITH GRADIENT ========== -->
          <tr>
            <td>
              <!--[if mso]>
              <v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" style="width:600px;height:180px;">
                <v:fill type="gradient" color="{primary_color}" color2="{accent_color}" angle="135"/>
                <v:textbox inset="0,0,0,0" style="mso-fit-shape-to-text:true">
              <![endif]-->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 100%); border-radius: 12px 12px 0 0;">
                <tr>
                  <td align="center" style="padding: 28px 40px 16px 40px;">
                    {logo_html}
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding: 0 40px 8px 40px;">
                    <!-- V4: Brand pill for Market Snapshot, Report label for others -->
                    <span style="display: inline-block; background-color: rgba(255,255,255,0.2); color: #ffffff; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; padding: 6px 14px; border-radius: 20px;">
                      {brand_name if has_hero_4 else report_label}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding: 0 40px;">
                    <!-- V4: "Market Snapshot – [Area]" title format for Market Snapshot -->
                    <h1 style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 28px; font-weight: 400; color: #ffffff; line-height: 1.3; letter-spacing: -0.5px;">
                      {f"{report_label} – {area_display}" if has_hero_4 else (tagline or report_label)}
                    </h1>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding: 10px 40px 28px 40px;">
                    <!-- V4: "Period: Last X days • Source: Live MLS Data" for Market Snapshot -->
                    <p style="margin: 0; font-size: 14px; color: rgba(255,255,255,0.9);">
                      {"Period: " + date_range + " • Source: Live MLS Data" if has_hero_4 else (area_display + " • " + date_range)}
                    </p>
                  </td>
                </tr>
              </table>
              <!--[if mso]>
                </v:textbox>
              </v:rect>
              <![endif]-->
            </td>
          </tr>
          
          <!-- ========== MAIN CONTENT ========== -->
          <tr>
            <td style="background-color: #ffffff; padding: 40px;" class="dark-card mobile-padding">
              
              {"" if has_hero_4 else f'''<!-- Section Label (V3 style) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 20px;">
                    <p style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1.5px;">
                      {section_label}
                    </p>
                  </td>
                </tr>
              </table>
'''}
{insight_html if has_hero_4 else ""}{hero_4_html if has_hero_4 else f'''              <!-- ========== 3-COLUMN METRICS (V3 style) ========== -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <!-- Metric 1 -->
                  <td width="33%" class="metric-card" style="padding: 0 6px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);" class="dark-card dark-border">
                      <tr>
                        <td align="center" style="padding: 20px 12px;">
                          <p style="margin: 0 0 6px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 30px; font-weight: 400; color: {primary_color};">
                            {m1_value}
                          </p>
                          <p style="margin: 0; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">
                            {m1_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <!-- Metric 2 -->
                  <td width="33%" class="metric-card" style="padding: 0 6px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);" class="dark-card dark-border">
                      <tr>
                        <td align="center" style="padding: 20px 12px;">
                          <p style="margin: 0 0 6px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 30px; font-weight: 400; color: {primary_color};">
                            {m2_value}
                          </p>
                          <p style="margin: 0; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">
                            {m2_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <!-- Metric 3 -->
                  <td width="33%" class="metric-card" style="padding: 0 6px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);" class="dark-card dark-border">
                      <tr>
                        <td align="center" style="padding: 20px 12px;">
                          <p style="margin: 0 0 6px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 30px; font-weight: 400; color: {primary_color};">
                            {m3_value}
                          </p>
                          <p style="margin: 0; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">
                            {m3_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
'''}{core_indicators_html if has_hero_4 else ""}{extra_stats_html}{property_types_html}{price_tiers_html}{price_bands_html}
              <!-- ========== CTA BUTTON ========== -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding: 8px 0 32px 0;">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{pdf_url}" style="height:52px;v-text-anchor:middle;width:200px;" arcsize="10%" stroke="f" fillcolor="{primary_color}">
                      <w:anchorlock/>
                      <center style="color:#ffffff;font-family:Georgia,serif;font-size:15px;font-weight:normal;">View Full Report</center>
                    </v:roundrect>
                    <![endif]-->
                    <!--[if !mso]><!-->
                    <a href="{pdf_url}" target="_blank" style="display: inline-block; background-color: {primary_color}; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 15px; font-weight: 400; text-decoration: none; padding: 14px 32px; border-radius: 6px; box-shadow: 0 2px 8px {primary_color}30; letter-spacing: 0.3px;">
                      View Full Report →
                    </a>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>
              
              <!-- Divider -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td style="border-top: 1px solid #e5e7eb; padding-top: 32px;" class="dark-border"></td>
                </tr>
              </table>
              
{agent_footer_html}
              
            </td>
          </tr>
          
          <!-- ========== FOOTER ========== -->
          <tr>
            <td style="background-color: #f9fafb; padding: 24px 40px; border-radius: 0 0 12px 12px; border-top: 1px solid #e5e7eb;" class="dark-card dark-border mobile-padding">
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <p style="margin: 0 0 8px 0; font-size: 13px; color: #9ca3af;">
                      {f'Powered by <a href="{website_url or "#"}" style="color: {primary_color}; text-decoration: none; font-weight: 500;">{brand_name}</a>' if brand.get("display_name") else f'Powered by <span style="color: {primary_color}; font-weight: 500;">TrendyReports</span>'}
                    </p>
                    <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                      <a href="{unsubscribe_url}" style="color: #9ca3af; text-decoration: underline;">Unsubscribe</a>
                      from these notifications
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
        </table>
        <!-- End Wrapper -->
        
      </td>
    </tr>
  </table>
  <!-- End Container -->
  
</body>
</html>'''
    
    return html


def schedule_email_subject(
    report_type: str, 
    city: Optional[str], 
    zip_codes: Optional[list]
) -> str:
    """Generate email subject line for a scheduled report."""
    # Get report label
    config = REPORT_CONFIG.get(report_type, {})
    report_label = config.get("label", report_type.replace("_", " ").title())
    
    # Format area
    if city:
        area = city
    elif zip_codes and len(zip_codes) > 0:
        if len(zip_codes) == 1:
            area = f"ZIP {zip_codes[0]}"
        else:
            area = f"{len(zip_codes)} ZIP codes"
    else:
        area = "Your Area"
    
    return f"📊 Your {report_label} for {area} is Ready!"
