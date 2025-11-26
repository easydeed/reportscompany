import { SAMPLE_REPORT_DATA, ReportType } from "@/lib/sample-report-data";

type Props = {
  params: Promise<{ reportType: string }>;
  searchParams: Promise<{
    brand_name?: string;
    logo_url?: string;
    primary_color?: string;
    accent_color?: string;
    rep_photo_url?: string;
    contact_line1?: string;
    contact_line2?: string;
    website_url?: string;
  }>;
};

/**
 * Branding Preview Page
 * 
 * Renders a sample report with branding for PDF generation.
 * Used by the backend to generate sample PDFs.
 * 
 * Pass B4.4: Branding Preview Page
 */
export default async function BrandingPreviewPage({ params, searchParams }: Props) {
  const { reportType: rawType } = await params;
  const query = await searchParams;

  // Validate report type
  const validTypes = Object.keys(SAMPLE_REPORT_DATA);
  const reportType = validTypes.includes(rawType) ? (rawType as ReportType) : "market_snapshot";

  // Get sample data
  const data = SAMPLE_REPORT_DATA[reportType];

  // Get branding from query params
  const brandName = query.brand_name || "Your Brand";
  const logoUrl = query.logo_url ? decodeURIComponent(query.logo_url) : null;
  const primaryColor = query.primary_color ? `#${query.primary_color}` : "#7C3AED";
  const accentColor = query.accent_color ? `#${query.accent_color}` : "#F26B2B";
  // Footer branding
  const repPhotoUrl = query.rep_photo_url ? decodeURIComponent(query.rep_photo_url) : null;
  const contactLine1 = query.contact_line1 ? decodeURIComponent(query.contact_line1) : null;
  const contactLine2 = query.contact_line2 ? decodeURIComponent(query.contact_line2) : null;
  const websiteUrl = query.website_url ? decodeURIComponent(query.website_url) : null;

  // Format helpers
  const formatCurrency = (val: number) => {
    if (!val) return "$0";
    return "$" + val.toLocaleString();
  };

  const formatNumber = (val: number) => {
    if (!val) return "0";
    return val.toLocaleString();
  };

  const getReportTitle = (type: string): string => {
    const titles: Record<string, string> = {
      market_snapshot: "Market Snapshot",
      new_listings: "New Listings",
      new_listings_gallery: "New Listings Gallery",
      featured_listings: "Featured Listings",
      inventory: "Inventory Report",
      closed: "Closed Sales",
      price_bands: "Price Bands",
      open_houses: "Open Houses",
    };
    return titles[type] || "Market Report";
  };

  const metrics = (data as any).metrics || {};
  const counts = (data as any).counts || {};
  const city = (data as any).city || "Market";
  const periodLabel = (data as any).period_label || "Last 30 days";
  const reportDate = (data as any).report_date || new Date().toLocaleDateString();

  return (
    <html>
      <head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>{getReportTitle(reportType)} - {brandName}</title>
        <style
          dangerouslySetInnerHTML={{
            __html: `
              @page {
                size: Letter;
                margin: 0;
              }
              
              :root {
                --primary: ${primaryColor};
                --accent: ${accentColor};
              }
              
              * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
              }
              
              body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.5;
                color: #1f2937;
                background: white;
              }
              
              .page {
                width: 8.5in;
                min-height: 11in;
                padding: 0;
                page-break-after: always;
              }
              
              .header {
                background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
                color: white;
                padding: 24px 32px;
              }
              
              .header-content {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 16px;
              }
              
              .header-left {
                display: flex;
                align-items: center;
                gap: 16px;
              }
              
              .logo {
                height: 48px;
                width: auto;
                max-width: 160px;
                object-fit: contain;
                filter: brightness(0) invert(1);
              }
              
              .logo-placeholder {
                width: 48px;
                height: 48px;
                background: rgba(255,255,255,0.2);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                font-weight: bold;
              }
              
              .header-title {
                font-size: 24px;
                font-weight: 700;
              }
              
              .header-subtitle {
                font-size: 14px;
                opacity: 0.9;
              }
              
              .header-right {
                text-align: right;
                font-size: 13px;
              }
              
              .content {
                padding: 32px;
              }
              
              .intro {
                color: #6b7280;
                margin-bottom: 24px;
                font-size: 14px;
              }
              
              .metrics-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                margin-bottom: 32px;
              }
              
              .metric-card {
                background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
                color: white;
                padding: 20px;
                border-radius: 12px;
              }
              
              .metric-label {
                font-size: 11px;
                opacity: 0.9;
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
              }
              
              .metric-value {
                font-size: 24px;
                font-weight: 700;
              }
              
              .section {
                margin-bottom: 32px;
              }
              
              .section h3 {
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 16px;
                color: var(--primary);
              }
              
              .data-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
              }
              
              .data-table th,
              .data-table td {
                padding: 10px 8px;
                border-bottom: 1px solid #e5e7eb;
              }
              
              .data-table th {
                text-align: left;
                font-weight: 600;
                color: #6b7280;
                font-size: 10px;
                text-transform: uppercase;
              }
              
              .text-right {
                text-align: right;
              }
              
              .gallery-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
              }
              
              .property-card {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                overflow: hidden;
              }
              
              .property-image {
                width: 100%;
                height: 120px;
                object-fit: cover;
              }
              
              .property-info {
                padding: 12px;
              }
              
              .property-address {
                font-weight: 600;
                font-size: 12px;
              }
              
              .property-location {
                font-size: 10px;
                color: #6b7280;
              }
              
              .property-price {
                font-size: 16px;
                font-weight: 700;
                color: var(--primary);
                margin: 6px 0;
              }
              
              .property-details {
                display: flex;
                gap: 10px;
                font-size: 10px;
                color: #6b7280;
              }
              
              /* Branded Footer (above gray footer) */
              .branded-footer {
                margin: 24px 32px 0;
                padding: 16px 20px;
                background: #f8fafc;
                border-radius: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 16px;
              }
              
              .branded-footer-contact {
                display: flex;
                align-items: center;
                gap: 12px;
              }
              
              .branded-footer-photo {
                width: 52px;
                height: 52px;
                border-radius: 50%;
                object-fit: cover;
                border: 2px solid var(--primary);
                flex-shrink: 0;
              }
              
              .branded-footer-info {
                display: flex;
                flex-direction: column;
                gap: 2px;
              }
              
              .branded-footer-name {
                font-size: 13px;
                font-weight: 600;
                color: #0f172a;
              }
              
              .branded-footer-details {
                font-size: 11px;
                color: #6b7280;
              }
              
              .branded-footer-website {
                font-size: 10px;
                color: var(--primary);
              }
              
              .branded-footer-logo {
                display: flex;
                align-items: center;
              }
              
              .branded-footer-logo img {
                height: 48px;
                width: auto;
                max-width: 160px;
                object-fit: contain;
              }
              
              .branded-footer-logo-text {
                font-size: 14px;
                font-weight: 600;
                color: var(--primary);
              }

              /* Gray Footer (bottom) */
              .footer {
                margin-top: 16px;
                padding: 12px 32px;
                border-top: 1px solid #e5e7eb;
                text-align: center;
                font-size: 10px;
                color: #9ca3af;
              }
              
              .sample-watermark {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 72px;
                font-weight: bold;
                color: rgba(0,0,0,0.03);
                pointer-events: none;
                z-index: 1000;
              }
            `,
          }}
        />
      </head>
      <body>
        <div className="sample-watermark">SAMPLE</div>
        
        <div className="page" style={{ position: "relative" }}>
          <div className="header">
            <div className="header-content">
              <div className="header-left">
                {logoUrl ? (
                  <img src={logoUrl} alt={brandName} className="logo" />
                ) : (
                  <div className="logo-placeholder">{brandName[0]}</div>
                )}
                <div>
                  <div className="header-title">
                    {getReportTitle(reportType)} — {city}
                  </div>
                  <div className="header-subtitle">
                    {periodLabel} • {reportDate}
                  </div>
                </div>
              </div>
              <div className="header-right">
                <div>{brandName} Insights</div>
              </div>
            </div>
          </div>

          <div className="content">
            <p className="intro">
              This {getReportTitle(reportType).toLowerCase()} provides key market
              indicators for <strong>{city}</strong> based on the most recent{" "}
              <strong>{(data as any).lookback_days || 30} days</strong> of MLS activity.
            </p>

            {/* Metrics Grid */}
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-label">Median Price</div>
                <div className="metric-value">
                  {formatCurrency(metrics.median_close_price || metrics.median_list_price)}
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Active Listings</div>
                <div className="metric-value">{formatNumber(counts.Active)}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Closed Sales</div>
                <div className="metric-value">{formatNumber(counts.Closed)}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Avg. DOM</div>
                <div className="metric-value">{metrics.avg_dom || 0}</div>
              </div>
            </div>

            {/* Listings Table */}
            {(data as any).listings_sample && (data as any).listings_sample.length > 0 && (
              <div className="section">
                <h3>Recent Activity</h3>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Address</th>
                      <th className="text-right">Price</th>
                      <th className="text-right">Beds</th>
                      <th className="text-right">Baths</th>
                      <th className="text-right">SqFt</th>
                      <th className="text-right">DOM</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data as any).listings_sample.slice(0, 6).map((l: any, i: number) => (
                      <tr key={i}>
                        <td>{l.address}</td>
                        <td className="text-right">{formatCurrency(l.list_price)}</td>
                        <td className="text-right">{l.beds}</td>
                        <td className="text-right">{l.baths}</td>
                        <td className="text-right">{formatNumber(l.sqft)}</td>
                        <td className="text-right">{l.days_on_market}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Gallery for gallery reports */}
            {(data as any).listings && (data as any).listings.length > 0 && (
              <div className="section">
                <h3>Featured Properties</h3>
                <div className="gallery-grid">
                  {(data as any).listings.slice(0, 6).map((l: any, i: number) => (
                    <div key={i} className="property-card">
                      <img
                        src={l.hero_photo_url || "https://via.placeholder.com/400x300"}
                        alt={l.street_address}
                        className="property-image"
                      />
                      <div className="property-info">
                        <div className="property-address">{l.street_address}</div>
                        <div className="property-location">
                          {l.city}, {l.zip_code}
                        </div>
                        <div className="property-price">{formatCurrency(l.list_price)}</div>
                        <div className="property-details">
                          <span>{l.bedrooms} bd</span>
                          <span>{l.bathrooms} ba</span>
                          <span>{formatNumber(l.sqft)} sqft</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Branded Footer */}
          <div className="branded-footer">
            <div className="branded-footer-contact">
              {repPhotoUrl && (
                <img src={repPhotoUrl} alt="Representative" className="branded-footer-photo" />
              )}
              <div className="branded-footer-info">
                {contactLine1 && <div className="branded-footer-name">{contactLine1}</div>}
                {contactLine2 && <div className="branded-footer-details">{contactLine2}</div>}
                {websiteUrl && (
                  <div className="branded-footer-website">
                    {websiteUrl.replace("https://", "").replace("http://", "")}
                  </div>
                )}
              </div>
            </div>
            <div className="branded-footer-logo">
              {logoUrl ? (
                <img src={logoUrl} alt={brandName} />
              ) : (
                <div className="branded-footer-logo-text">{brandName}</div>
              )}
            </div>
          </div>

          {/* Gray Footer */}
          <div className="footer">
            Report generated by {brandName} • Data source: MLS • Sample Data
          </div>
        </div>
      </body>
    </html>
  );
}

// Disable layout for this page (it's a standalone HTML page for PDF)
export const metadata = {
  title: "Branding Preview",
};

