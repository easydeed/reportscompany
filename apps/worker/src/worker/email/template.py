"""HTML email template for scheduled report notifications."""
from typing import Dict, Optional


def schedule_email_html(
    account_name: str,
    report_type: str,
    city: Optional[str],
    zip_codes: Optional[list],
    lookback_days: int,
    metrics: Dict,
    pdf_url: str,
    unsubscribe_url: str,
) -> str:
    """
    Generate HTML email for a scheduled report notification.
    
    Args:
        account_name: Name of the account (for personalization)
        report_type: Type of report (market_snapshot, new_listings, etc.)
        city: City name (if city-based report)
        zip_codes: List of ZIP codes (if ZIP-based report)
        lookback_days: Number of days covered by the report
        metrics: Dictionary of key metrics to display
        pdf_url: Direct link to the PDF report
        unsubscribe_url: Link to unsubscribe from future emails
    
    Returns:
        HTML string for the email body
    """
    # Format report type for display
    report_type_display = {
        "market_snapshot": "Market Snapshot",
        "new_listings": "New Listings",
        "inventory": "Inventory Report",
        "closed": "Closed Sales",
        "price_bands": "Price Bands Analysis",
        "open_houses": "Open Houses",
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
                        
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 30px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px 8px 0 0;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">📊 Your {report_type_display} Report</h1>
                                <p style="margin: 10px 0 0; color: #e0e7ff; font-size: 16px;">{area_display} • Last {lookback_days} days</p>
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
                        
                        <!-- CTA Button -->
                        <tr>
                            <td style="padding: 0 40px 40px; text-align: center;">
                                <a href="{pdf_url}" style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                                    📄 View Full Report (PDF)
                                </a>
                                <p style="margin: 15px 0 0; font-size: 14px; color: #6b7280;">
                                    This link will expire in 7 days
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0; font-size: 14px; color: #6b7280; text-align: center;">
                                    You're receiving this because you have an active schedule for {area_display}.
                                </p>
                                <p style="margin: 10px 0 0; font-size: 14px; color: #6b7280; text-align: center;">
                                    <a href="{unsubscribe_url}" style="color: #6b7280; text-decoration: underline;">Unsubscribe</a> from these automated reports
                                </p>
                                <p style="margin: 15px 0 0; font-size: 12px; color: #9ca3af; text-align: center;">
                                    © {account_name or 'Market Reports'}. All rights reserved.
                                </p>
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

