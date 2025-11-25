"""HTML email template for scheduled report notifications."""
from typing import Dict, Optional, TypedDict


class Brand(TypedDict, total=False):
    """Brand configuration for white-label emails (Phase 30)."""
    display_name: str
    logo_url: Optional[str]
    primary_color: Optional[str]
    accent_color: Optional[str]
    rep_photo_url: Optional[str]
    contact_line1: Optional[str]
    contact_line2: Optional[str]
    website_url: Optional[str]


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
    
    Phase 30: Now supports white-label branding for affiliate accounts.
    
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
    # Phase 30: Extract brand values
    brand_name = (brand.get("display_name") if brand else None) or account_name or "Market Reports"
    logo_url = brand.get("logo_url") if brand else None
    primary_color = (brand.get("primary_color") if brand else None) or "#667eea"
    accent_color = (brand.get("accent_color") if brand else None) or "#764ba2"
    rep_photo_url = (brand.get("rep_photo_url") if brand else None)  # Pass B5: Headshot
    contact_line1 = (brand.get("contact_line1") if brand else None)
    contact_line2 = (brand.get("contact_line2") if brand else None)
    website_url = (brand.get("website_url") if brand else None)
    # Format report type for display
    # IMPORTANT: Keep this map in sync with:
    # - Frontend: apps/web/app/lib/reportTypes.ts (reportTypes array)
    # - Backend: apps/api/src/api/routes/schedules.py (report_type Literal)
    # - Worker: apps/worker/src/worker/report_builders.py (builders dict)
    report_type_display = {
        "market_snapshot": "Market Snapshot",
        "new_listings": "New Listings",
        "inventory": "Inventory Report",
        "closed": "Closed Sales",
        "price_bands": "Price Bands Analysis",
        "open_houses": "Open Houses",
        "new_listings_gallery": "New Listings Gallery",
        "featured_listings": "Featured Listings",
    }.get(report_type, report_type.replace("_", " ").title())
    
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
        area_display = "your area"
    
    # Extract key metrics
    total_active = metrics.get("total_active", 0)
    total_pending = metrics.get("total_pending", 0)
    total_closed = metrics.get("total_closed", 0)
    median_list_price = metrics.get("median_list_price")
    median_close_price = metrics.get("median_close_price")
    avg_dom = metrics.get("avg_dom")
    
    # Format prices
    def format_price(price):
        if price is None:
            return "N/A"
        return f"${price:,.0f}"
    
    # Build metrics HTML based on report type
    metrics_html = ""
    
    if report_type == "market_snapshot":
        metrics_html = f"""
        <tr>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Active Listings</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{total_active:,}</div>
          </td>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Pending</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{total_pending:,}</div>
          </td>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Closed</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{total_closed:,}</div>
          </td>
        </tr>
        """
    elif report_type == "new_listings":
        metrics_html = f"""
        <tr>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">New Listings</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{total_active:,}</div>
          </td>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Median Price</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{format_price(median_list_price)}</div>
          </td>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Avg. DOM</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{avg_dom or 'N/A'}</div>
          </td>
        </tr>
        """
    elif report_type == "closed":
        metrics_html = f"""
        <tr>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Closed Sales</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{total_closed:,}</div>
          </td>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Median Price</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{format_price(median_close_price)}</div>
          </td>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Avg. DOM</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{avg_dom or 'N/A'}</div>
          </td>
        </tr>
        """
    elif report_type == "new_listings_gallery":
        # Phase P3: Gallery email with photo grid emphasis
        total_listings = metrics.get("total_listings", total_active)
        metrics_html = f"""
        <tr>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">📸 New Properties</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{total_listings:,}</div>
          </td>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Median Price</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{format_price(median_list_price)}</div>
          </td>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Avg. DOM</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{avg_dom or 'N/A'}</div>
          </td>
        </tr>
        """
    elif report_type == "featured_listings":
        # Phase P3: Featured listings with premium feel
        total_listings = metrics.get("total_listings", 4)
        metrics_html = f"""
        <tr>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">✨ Featured Properties</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{total_listings:,}</div>
          </td>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Median Price</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{format_price(median_list_price)}</div>
          </td>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Avg. DOM</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{avg_dom or 'N/A'}</div>
          </td>
        </tr>
        """
    else:
        # Generic metrics for other report types
        metrics_html = f"""
        <tr>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Properties</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{total_active:,}</div>
          </td>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Median Price</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{format_price(median_list_price)}</div>
          </td>
          <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Days on Market</div>
            <div style="font-size: 24px; font-weight: 600; color: #111827;">{avg_dom or 'N/A'}</div>
          </td>
        </tr>
        """
    
    # Build the complete HTML email
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{report_type_display} Report</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f9fafb;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td align="center" style="padding: 40px 0;">
                    <!-- Main Container -->
                    <table role="presentation" style="width: 600px; max-width: 100%; background-color: #ffffff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">
                        
                        <!-- Header (Phase 30: White-label branding) -->
                        <tr>
                            <td style="padding: 40px 40px 30px; text-align: center; background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 100%); border-radius: 8px 8px 0 0;">
                                {f'<img src="{logo_url}" alt="{brand_name}" style="height: 40px; margin-bottom: 20px; object-fit: contain;" />' if logo_url else ''}
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">📊 Your {report_type_display} Report</h1>
                                <p style="margin: 10px 0 0; color: #e0e7ff; font-size: 16px;">{area_display} • Last {lookback_days} days</p>
                                {f'<p style="margin: 15px 0 0; color: #ffffff; font-size: 14px; font-weight: 500;">{brand_name}</p>' if brand else ''}
                            </td>
                        </tr>
                        
                        <!-- Greeting -->
                        <tr>
                            <td style="padding: 30px 40px 20px;">
                                <p style="margin: 0; font-size: 16px; color: #374151; line-height: 1.6;">
                                    Hi{f' {account_name}' if account_name else ''},
                                </p>
                                <p style="margin: 15px 0 0; font-size: 16px; color: #374151; line-height: 1.6;">
                                    Your scheduled <strong>{report_type_display}</strong> report for {area_display} is ready!
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Key Metrics -->
                        <tr>
                            <td style="padding: 0 40px 30px;">
                                <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f9fafb; border-radius: 8px; overflow: hidden;">
                                    {metrics_html}
                                </table>
                            </td>
                        </tr>
                        
                        <!-- CTA Button (Phase 30: Uses brand accent color) -->
                        <tr>
                            <td style="padding: 0 40px 40px; text-align: center;">
                                <a href="{pdf_url}" style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                                    📄 View Full Report (PDF)
                                </a>
                                <p style="margin: 15px 0 0; font-size: 14px; color: #6b7280;">
                                    This link will expire in 7 days
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer (Phase 30: White-label contact info + Pass B5: Headshot) -->
                        <tr>
                            <td style="padding: 30px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb;">
                                {f'''
                                <table role="presentation" style="width: 100%; margin-bottom: 20px;">
                                    <tr>
                                        <td style="text-align: center;">
                                            <img src="{rep_photo_url}" alt="Representative" style="width: 64px; height: 64px; border-radius: 50%; object-fit: cover; border: 3px solid {primary_color};" />
                                        </td>
                                    </tr>
                                </table>
                                ''' if rep_photo_url else ''}
                                {f'<p style="margin: 0; font-size: 14px; color: #374151; text-align: center; font-weight: 500;">{contact_line1}</p>' if contact_line1 else ''}
                                {f'<p style="margin: 5px 0 0; font-size: 14px; color: #6b7280; text-align: center;">{contact_line2}</p>' if contact_line2 else ''}
                                {f'<p style="margin: 10px 0 0; font-size: 14px; color: #6b7280; text-align: center;"><a href="{website_url}" style="color: {primary_color}; text-decoration: none;">{website_url.replace("https://", "").replace("http://", "")}</a></p>' if website_url else ''}
                                <p style="margin: {'20px' if (contact_line1 or contact_line2 or website_url) else '0'} 0 0; font-size: 14px; color: #6b7280; text-align: center;">
                                    You're receiving this because you have an active schedule for {area_display}.
                                </p>
                                <p style="margin: 10px 0 0; font-size: 14px; color: #6b7280; text-align: center;">
                                    <a href="{unsubscribe_url}" style="color: #6b7280; text-decoration: underline;">Unsubscribe</a> from these automated reports
                                </p>
                                <p style="margin: 15px 0 0; font-size: 12px; color: #9ca3af; text-align: center;">
                                    © {brand_name}. All rights reserved.
                                </p>
                                {'' if brand else '<p style="margin: 5px 0 0; font-size: 10px; color: #d1d5db; text-align: center;">Powered by TrendyReports</p>'}
                            </td>
                        </tr>
                        
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return html


def schedule_email_subject(report_type: str, city: Optional[str], zip_codes: Optional[list]) -> str:
    """Generate email subject line for a scheduled report."""
    # Format report type
    report_type_display = {
        "market_snapshot": "Market Snapshot",
        "new_listings": "New Listings",
        "inventory": "Inventory Report",
        "closed": "Closed Sales",
        "price_bands": "Price Bands Analysis",
        "open_houses": "Open Houses",
        "new_listings_gallery": "New Listings Gallery",
        "featured_listings": "Featured Listings",
    }.get(report_type, report_type.replace("_", " ").title())
    
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
    
    return f"📊 Your {report_type_display} Report for {area} is Ready!"

