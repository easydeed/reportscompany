import { SAMPLE_REPORT_DATA, ReportType } from "@/lib/sample-report-data";

type Props = {
  params: Promise<{ reportType: string }>;
  searchParams: Promise<{
    brand_name?: string;
    logo_url?: string;
    footer_logo_url?: string;
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
 * V2: Updated to match PDF template hero header design
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
  // Footer logo - use separate footer_logo_url if provided, otherwise fall back to logo_url
  const footerLogoUrl = query.footer_logo_url ? decodeURIComponent(query.footer_logo_url) : logoUrl;
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
                max-height: 11in;
                padding: 0;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                overflow: hidden;
                page-break-after: avoid;
                page-break-inside: avoid;
              }
              
              /* V2 Hero Header - Full bleed gradient */
              .hero-header {
                background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
                color: white;
                padding: 24px 32px;
                min-height: 90px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
              }
              
              .hero-left {
                display: flex;
                align-items: center;
                gap: 16px;
              }
              
              .hero-logo {
                height: 52px;
                width: auto;
                max-width: 140px;
                object-fit: contain;
                filter: brightness(0) invert(1);
              }
              
              .hero-logo-placeholder {
                width: 52px;
                height: 52px;
                background: rgba(255,255,255,0.2);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                font-weight: bold;
              }
              
              .hero-text {
                display: flex;
                flex-direction: column;
                gap: 2px;
              }
              
              .hero-brand-name {
                font-size: 16px;
                font-weight: 600;
                opacity: 0.95;
              }
              
              .hero-report-type {
                font-size: 12px;
                opacity: 0.8;
                text-transform: uppercase;
                letter-spacing: 0.5px;
              }
              
              .hero-right {
                display: flex;
                align-items: center;
                gap: 12px;
              }
              
              .pdf-badge {
                background: rgba(255,255,255,0.2);
                color: white;
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
              }
              
              .affiliate-pill {
                background: rgba(255,255,255,0.15);
                color: white;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
              }
              
              /* Title Bar - Below hero */
              .title-bar {
                padding: 20px 32px;
                border-bottom: 1px solid #e5e7eb;
                background: white;
              }
              
              .title-bar h1 {
                font-size: 22px;
                font-weight: 700;
                color: #0f172a;
                margin: 0 0 4px 0;
              }
              
              .title-bar .subline {
                font-size: 13px;
                color: #64748b;
                margin: 0;
              }
              
              .content {
                padding: 24px 32px;
                flex: 1;
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
                text-align: center;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
              }
              
              .metric-label {
                font-size: 11px;
                opacity: 0.9;
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                text-align: center;
              }
              
              .metric-value {
                font-size: 24px;
                font-weight: 700;
                text-align: center;
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
                margin: auto 32px 0;
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

              /* Page Footer */
              .page-footer {
                margin-top: auto;
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
              
              @media print {
                html, body {
                  margin: 0 !important;
                  padding: 0 !important;
                  background: white !important;
                }
                .page {
                  box-shadow: none !important;
                  margin: 0 !important;
                  overflow: hidden !important;
                  page-break-after: avoid !important;
                }
                .hero-header {
                  margin: 0 !important;
                  -webkit-print-color-adjust: exact !important;
                  print-color-adjust: exact !important;
                }
                .metric-card {
                  -webkit-print-color-adjust: exact !important;
                  print-color-adjust: exact !important;
                }
                .sample-watermark {
                  display: none !important;
                }
              }
            `,
          }}
        />
      </head>
      <body>
        <div className="sample-watermark">SAMPLE</div>
        
        <div className="page">
          {/* V2 Hero Header */}
          <div className="hero-header">
            <div className="hero-left">
              {logoUrl ? (
                <img src={logoUrl} alt={brandName} className="hero-logo" />
              ) : (
                <div className="hero-logo-placeholder">{brandName[0]}</div>
              )}
              <div className="hero-text">
                <div className="hero-brand-name">{brandName}</div>
                <div className="hero-report-type">{getReportTitle(reportType)}</div>
              </div>
            </div>
            <div className="hero-right">
              <span className="pdf-badge">PDF</span>
              <span className="affiliate-pill">{brandName}</span>
            </div>
          </div>

          {/* Title Bar */}
          <div className="title-bar">
            <h1>{getReportTitle(reportType)} — {city}</h1>
            <p className="subline">{periodLabel} • {reportDate} • Source: Live MLS Data</p>
          </div>

          <div className="content">
            {/* Report-type specific intro */}
            <p className="intro">
              {reportType === "market_snapshot" && (
                <>This market snapshot provides key indicators for <strong>{city}</strong> based on the most recent <strong>{(data as any).lookback_days || 30} days</strong> of MLS activity, including pricing trends, inventory levels, and days on market.</>
              )}
              {reportType === "new_listings" && (
                <>Discover <strong>{formatNumber(counts.Active)}</strong> new properties listed in <strong>{city}</strong> over the past <strong>{(data as any).lookback_days || 14} days</strong>. Fresh opportunities for buyers and investors.</>
              )}
              {reportType === "inventory" && (
                <>Current inventory analysis for <strong>{city}</strong> showing <strong>{formatNumber(counts.Active)}</strong> active listings with an average of <strong>{metrics.avg_dom || 0} days</strong> on market.</>
              )}
              {reportType === "closed" && (
                <><strong>{formatNumber(counts.Closed)}</strong> properties closed in <strong>{city}</strong> over the past <strong>{(data as any).lookback_days || 30} days</strong> with a median sale price of <strong>{formatCurrency(metrics.median_close_price)}</strong>.</>
              )}
              {reportType === "price_bands" && (
                <>Market breakdown by price range for <strong>{city}</strong> showing activity across different market segments over the past <strong>{(data as any).lookback_days || 30} days</strong>.</>
              )}
              {reportType === "new_listings_gallery" && (
                <>Photo gallery showcasing <strong>{(data as any).total_listings || (data as any).listings?.length || 0}</strong> newly listed properties in <strong>{city}</strong> from the past <strong>{(data as any).lookback_days || 14} days</strong>.</>
              )}
              {reportType === "featured_listings" && (
                <>Curated selection of <strong>{(data as any).total_listings || (data as any).listings?.length || 0}</strong> premium properties featured in <strong>{city}</strong>. Each property has been selected for its exceptional value or features.</>
              )}
              {reportType === "open_houses" && (
                <>Upcoming open houses in <strong>{city}</strong> this weekend. <strong>{formatNumber(counts.Active)}</strong> properties available for viewing.</>
              )}
            </p>

            {/* Report-type specific metrics */}
            {reportType === "market_snapshot" && (
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Median Sale Price</div>
                  <div className="metric-value">{formatCurrency(metrics.median_close_price)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Closed Sales</div>
                  <div className="metric-value">{formatNumber(counts.Closed)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Avg. Days on Market</div>
                  <div className="metric-value">{metrics.avg_dom || 0}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Months of Inventory</div>
                  <div className="metric-value">{metrics.months_of_inventory?.toFixed(1) || "—"}</div>
                </div>
              </div>
            )}

            {reportType === "new_listings" && (
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">New Listings</div>
                  <div className="metric-value">{formatNumber(counts.Active)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Median List Price</div>
                  <div className="metric-value">{formatCurrency(metrics.median_list_price)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Avg. Price/SqFt</div>
                  <div className="metric-value">${formatNumber(metrics.avg_ppsf || 0)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Pending</div>
                  <div className="metric-value">{formatNumber(counts.Pending)}</div>
                </div>
              </div>
            )}

            {reportType === "inventory" && (
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Active Listings</div>
                  <div className="metric-value">{formatNumber(counts.Active)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Pending Sales</div>
                  <div className="metric-value">{formatNumber(counts.Pending)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Avg. DOM</div>
                  <div className="metric-value">{metrics.avg_dom || 0}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Median DOM</div>
                  <div className="metric-value">{metrics.median_dom || 0}</div>
                </div>
              </div>
            )}

            {reportType === "closed" && (
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Closed Sales</div>
                  <div className="metric-value">{formatNumber(counts.Closed)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Median Close Price</div>
                  <div className="metric-value">{formatCurrency(metrics.median_close_price)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Median List Price</div>
                  <div className="metric-value">{formatCurrency(metrics.median_list_price)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Avg. DOM</div>
                  <div className="metric-value">{metrics.avg_dom || 0}</div>
                </div>
              </div>
            )}

            {reportType === "price_bands" && (
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Total Listings</div>
                  <div className="metric-value">{formatNumber((data as any).price_bands?.reduce((s: number, b: any) => s + b.count, 0) || 0)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Median Price</div>
                  <div className="metric-value">{formatCurrency(metrics.median_list_price)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Price Bands</div>
                  <div className="metric-value">{(data as any).price_bands?.length || 0}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Avg. DOM</div>
                  <div className="metric-value">{metrics.avg_dom || 0}</div>
                </div>
              </div>
            )}

            {(reportType === "new_listings_gallery" || reportType === "featured_listings") && (
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Properties</div>
                  <div className="metric-value">{(data as any).total_listings || (data as any).listings?.length || 0}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Avg. Price</div>
                  <div className="metric-value">
                    {formatCurrency(
                      (data as any).listings?.length > 0
                        ? Math.round((data as any).listings.reduce((s: number, l: any) => s + l.list_price, 0) / (data as any).listings.length)
                        : 0
                    )}
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Avg. Beds</div>
                  <div className="metric-value">
                    {(data as any).listings?.length > 0
                      ? Math.round((data as any).listings.reduce((s: number, l: any) => s + l.bedrooms, 0) / (data as any).listings.length)
                      : "—"}
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Avg. SqFt</div>
                  <div className="metric-value">
                    {formatNumber(
                      (data as any).listings?.length > 0
                        ? Math.round((data as any).listings.reduce((s: number, l: any) => s + l.sqft, 0) / (data as any).listings.length)
                        : 0
                    )}
                  </div>
                </div>
              </div>
            )}

            {reportType === "open_houses" && (
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Open Houses</div>
                  <div className="metric-value">{formatNumber(counts.Active)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">This Weekend</div>
                  <div className="metric-value">{formatNumber(counts.Active)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Avg. DOM</div>
                  <div className="metric-value">{metrics.avg_dom || 0}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">View Period</div>
                  <div className="metric-value">{(data as any).lookback_days || 7} days</div>
                </div>
              </div>
            )}

            {/* Price Bands Table for price_bands report */}
            {reportType === "price_bands" && (data as any).price_bands && (
              <div className="section">
                <h3>Price Band Analysis</h3>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Price Range</th>
                      <th className="text-right">Count</th>
                      <th className="text-right">Median Price</th>
                      <th className="text-right">Avg DOM</th>
                      <th className="text-right">Avg $/SqFt</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data as any).price_bands.map((band: any, i: number) => (
                      <tr key={i}>
                        <td>{band.label}</td>
                        <td className="text-right">{band.count}</td>
                        <td className="text-right">{formatCurrency(band.median_price)}</td>
                        <td className="text-right">{band.avg_dom}</td>
                        <td className="text-right">${formatNumber(band.avg_ppsf)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Listings Table for reports with sample listings */}
            {(reportType === "market_snapshot" || reportType === "new_listings" || reportType === "closed") &&
              (data as any).listings_sample && (data as any).listings_sample.length > 0 && (
              <div className="section">
                <h3>{reportType === "closed" ? "Recent Closings" : reportType === "new_listings" ? "New Listings" : "Recent Activity"}</h3>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Address</th>
                      <th className="text-right">{reportType === "closed" ? "Close Price" : "List Price"}</th>
                      <th className="text-right">Beds</th>
                      <th className="text-right">Baths</th>
                      <th className="text-right">SqFt</th>
                      <th className="text-right">DOM</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data as any).listings_sample.slice(0, 5).map((l: any, i: number) => (
                      <tr key={i}>
                        <td>{l.address}</td>
                        <td className="text-right">{formatCurrency(reportType === "closed" ? (l.close_price || l.list_price) : l.list_price)}</td>
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
            {(reportType === "new_listings_gallery" || reportType === "featured_listings") && 
              (data as any).listings && (data as any).listings.length > 0 && (
              <div className="section">
                <h3>{reportType === "featured_listings" ? "Featured Properties" : "New Properties"}</h3>
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

          {/* Page Footer */}
          <div className="page-footer">
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
                {footerLogoUrl ? (
                  <img src={footerLogoUrl} alt={brandName} />
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
        </div>
      </body>
    </html>
  );
}

// Disable layout for this page (it's a standalone HTML page for PDF)
export const metadata = {
  title: "Branding Preview",
};
