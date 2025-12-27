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
 * Social Branding Preview Page (1080x1920)
 * 
 * Renders a sample social media story image with branding.
 * Used by the backend to generate sample JPGs for Brand Studio.
 */
export default async function SocialBrandingPreviewPage({ params, searchParams }: Props) {
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
  const repPhotoUrl = query.rep_photo_url ? decodeURIComponent(query.rep_photo_url) : null;
  const contactLine1 = query.contact_line1 ? decodeURIComponent(query.contact_line1) : null;
  const contactLine2 = query.contact_line2 ? decodeURIComponent(query.contact_line2) : null;
  const websiteUrl = query.website_url ? decodeURIComponent(query.website_url) : null;

  // Format helpers
  const formatCurrency = (val: number) => {
    if (!val) return "$0";
    if (val >= 1000000) return "$" + (val / 1000000).toFixed(1) + "M";
    if (val >= 1000) return "$" + Math.round(val / 1000) + "K";
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
      new_listings_gallery: "New Listings",
      featured_listings: "Featured",
      inventory: "Inventory",
      closed: "Closed Sales",
      price_bands: "Price Bands",
      open_houses: "Open Houses",
    };
    return titles[type] || "Market Report";
  };

  const metrics = (data as any).metrics || {};
  const counts = (data as any).counts || {};
  const city = (data as any).city || "Beverly Hills";

  // Get report-specific metrics
  const getHeroMetric = () => {
    switch (reportType) {
      case "market_snapshot":
        return { value: formatCurrency(metrics.median_close_price || 4150000), label: "Median Sale Price" };
      case "new_listings":
      case "new_listings_gallery":
        return { value: formatNumber(counts.Active || 42), label: "New Listings" };
      case "inventory":
        return { value: formatNumber(counts.Active || 127), label: "Active Listings" };
      case "closed":
        return { value: formatNumber(counts.Closed || 89), label: "Homes Sold" };
      case "price_bands":
        return { value: formatCurrency(metrics.median_list_price || 4250000), label: "Median Price" };
      case "featured_listings":
        return { value: formatNumber((data as any).total_listings || 4), label: "Featured" };
      case "open_houses":
        return { value: formatNumber(counts.Active || 15), label: "Open Houses" };
      default:
        return { value: formatCurrency(metrics.median_close_price || 0), label: "Median Price" };
    }
  };

  const getSecondaryMetrics = () => {
    switch (reportType) {
      case "market_snapshot":
        return [
          { value: formatNumber(counts.Closed || 89), label: "Homes Sold" },
          { value: formatNumber(metrics.avg_dom || 42), label: "Avg Days" },
          { value: (metrics.months_of_inventory || 4.3).toFixed(1), label: "Mo. Inventory" },
          { value: ((metrics.list_to_close_ratio || 0.976) * 100).toFixed(0) + "%", label: "Sale-to-List" },
        ];
      case "new_listings":
      case "new_listings_gallery":
        return [
          { value: formatCurrency(metrics.median_list_price || 4350000), label: "Median Price" },
          { value: formatNumber(metrics.avg_dom || 7), label: "Avg Days" },
        ];
      case "inventory":
        return [
          { value: formatNumber(counts.Pending || 34), label: "Pending" },
          { value: formatNumber(metrics.avg_dom || 45), label: "Avg Days" },
        ];
      case "closed":
        return [
          { value: formatCurrency(metrics.median_close_price || 4150000), label: "Median Price" },
          { value: formatNumber(metrics.avg_dom || 42), label: "Avg Days" },
        ];
      case "price_bands":
        return [
          { value: formatNumber((data as any).price_bands?.reduce((s: number, b: any) => s + b.count, 0) || 127), label: "Total Listings" },
          { value: formatNumber(metrics.avg_dom || 42), label: "Avg Days" },
        ];
      default:
        return [];
    }
  };

  const heroMetric = getHeroMetric();
  const secondaryMetrics = getSecondaryMetrics();

  return (
    <html>
      <head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=1080" />
        <title>{getReportTitle(reportType)} - {brandName} | Social</title>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />
        <style
          dangerouslySetInnerHTML={{
            __html: `
              * { margin: 0; padding: 0; box-sizing: border-box; }
              
              html, body {
                width: 1080px;
                height: 1920px;
                font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
                background: #ffffff;
                overflow: hidden;
                -webkit-font-smoothing: antialiased;
              }
              
              :root {
                --primary: ${primaryColor};
                --accent: ${accentColor};
                --ink: #0f172a;
                --muted: #64748b;
                --light-gray: #f8fafc;
                --border: #e2e8f0;
              }
              
              .story {
                width: 1080px;
                height: 1920px;
                display: flex;
                flex-direction: column;
                background: #ffffff;
              }
              
              /* Header */
              .header {
                background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
                padding: 80px 60px 60px;
                text-align: center;
              }
              
              .header-logo {
                height: 80px;
                width: auto;
                max-width: 280px;
                object-fit: contain;
                margin-bottom: 24px;
                filter: brightness(0) invert(1);
              }
              
              .header-logo-placeholder {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 80px;
                height: 80px;
                background: rgba(255,255,255,0.2);
                border-radius: 20px;
                margin-bottom: 24px;
                font-size: 36px;
                font-weight: 800;
                color: white;
              }
              
              .header-badge {
                display: inline-block;
                background: rgba(255,255,255,0.2);
                color: #fff;
                font-size: 24px;
                font-weight: 600;
                padding: 12px 32px;
                border-radius: 999px;
                margin-bottom: 20px;
                letter-spacing: 1px;
                text-transform: uppercase;
              }
              
              .header-title {
                font-size: 48px;
                font-weight: 800;
                color: #fff;
                margin-bottom: 12px;
                letter-spacing: -0.5px;
              }
              
              .header-market {
                font-size: 36px;
                font-weight: 600;
                color: rgba(255,255,255,0.9);
              }
              
              /* Metrics */
              .metrics {
                flex: 1;
                padding: 60px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                gap: 40px;
              }
              
              .hero-metric {
                text-align: center;
                padding: 50px 40px;
                background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
                border-radius: 32px;
                margin-bottom: 20px;
              }
              
              .hero-metric .value {
                font-size: 120px;
                font-weight: 900;
                color: #fff;
                line-height: 1;
                letter-spacing: -2px;
              }
              
              .hero-metric .label {
                font-size: 32px;
                font-weight: 600;
                color: rgba(255,255,255,0.9);
                margin-top: 16px;
                text-transform: uppercase;
                letter-spacing: 2px;
              }
              
              .metric-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 24px;
              }
              
              .metric-card {
                background: var(--light-gray);
                border-radius: 24px;
                padding: 40px 32px;
                text-align: center;
                border: 2px solid var(--border);
              }
              
              .metric-card .value {
                font-size: 72px;
                font-weight: 800;
                color: var(--ink);
                line-height: 1;
              }
              
              .metric-card .label {
                font-size: 24px;
                font-weight: 600;
                color: var(--muted);
                margin-top: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
              }
              
              .period-badge {
                text-align: center;
                padding: 20px;
              }
              
              .period-badge span {
                display: inline-block;
                background: var(--light-gray);
                color: var(--muted);
                font-size: 28px;
                font-weight: 600;
                padding: 16px 40px;
                border-radius: 999px;
                border: 2px solid var(--border);
              }
              
              /* Footer */
              .footer {
                background: var(--light-gray);
                padding: 48px 60px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-top: 2px solid var(--border);
              }
              
              .footer-contact {
                display: flex;
                align-items: center;
                gap: 24px;
              }
              
              .footer-photo {
                width: 100px;
                height: 100px;
                border-radius: 50%;
                object-fit: cover;
                border: 4px solid var(--primary);
              }
              
              .footer-photo-placeholder {
                width: 100px;
                height: 100px;
                border-radius: 50%;
                background: var(--border);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 36px;
                color: var(--muted);
              }
              
              .footer-info {
                display: flex;
                flex-direction: column;
                gap: 6px;
              }
              
              .footer-name {
                font-size: 32px;
                font-weight: 700;
                color: var(--ink);
              }
              
              .footer-details {
                font-size: 24px;
                color: var(--muted);
              }
              
              .footer-website {
                font-size: 22px;
                color: var(--primary);
                font-weight: 600;
              }
              
              .footer-logo {
                height: 80px;
                width: auto;
                max-width: 200px;
                object-fit: contain;
              }
              
              .footer-brand-text {
                font-size: 28px;
                font-weight: 700;
                color: var(--primary);
              }
              
              /* Sample watermark */
              .sample-watermark {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 140px;
                font-weight: 900;
                color: rgba(0,0,0,0.03);
                pointer-events: none;
                z-index: 1000;
                letter-spacing: 20px;
              }
            `,
          }}
        />
      </head>
      <body>
        <div className="sample-watermark">SAMPLE</div>
        
        <div className="story">
          {/* Header */}
          <div className="header">
            {logoUrl ? (
              <img src={logoUrl} alt={brandName} className="header-logo" />
            ) : (
              <div className="header-logo-placeholder">{brandName[0]}</div>
            )}
            <div className="header-badge">{getReportTitle(reportType)}</div>
            <div className="header-title">{city}</div>
            <div className="header-market">Real Estate Update</div>
          </div>

          {/* Metrics */}
          <div className="metrics">
            {/* Hero Metric */}
            <div className="hero-metric">
              <div className="value">{heroMetric.value}</div>
              <div className="label">{heroMetric.label}</div>
            </div>

            {/* Secondary Metrics Grid */}
            {secondaryMetrics.length > 0 && (
              <div className="metric-grid">
                {secondaryMetrics.map((m, i) => (
                  <div key={i} className="metric-card">
                    <div className="value">{m.value}</div>
                    <div className="label">{m.label}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Period Badge */}
            <div className="period-badge">
              <span>Last 30 days • Sample Data</span>
            </div>
          </div>

          {/* Footer */}
          <div className="footer">
            <div className="footer-contact">
              {repPhotoUrl ? (
                <img src={repPhotoUrl} alt="Representative" className="footer-photo" />
              ) : (
                <div className="footer-photo-placeholder">👤</div>
              )}
              <div className="footer-info">
                {contactLine1 ? (
                  <div className="footer-name">{contactLine1}</div>
                ) : (
                  <div className="footer-name">{brandName}</div>
                )}
                {contactLine2 && <div className="footer-details">{contactLine2}</div>}
                {websiteUrl && (
                  <div className="footer-website">
                    {websiteUrl.replace("https://", "").replace("http://", "")}
                  </div>
                )}
              </div>
            </div>
            {logoUrl ? (
              <img src={logoUrl} alt={brandName} className="footer-logo" />
            ) : (
              <div className="footer-brand-text">{brandName}</div>
            )}
          </div>
        </div>
      </body>
    </html>
  );
}

export const metadata = {
  title: "Social Branding Preview",
};

