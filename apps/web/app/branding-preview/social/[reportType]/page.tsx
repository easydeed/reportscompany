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
 * Renders report-specific social media story images with branding.
 * Each report type gets a unique, visually distinct layout.
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
      featured_listings: "Featured Listings",
      inventory: "Active Inventory",
      closed: "Just Sold",
      price_bands: "Market by Price",
      open_houses: "Open Houses",
    };
    return titles[type] || "Market Report";
  };

  const metrics = (data as any).metrics || {};
  const counts = (data as any).counts || {};
  const city = (data as any).city || "Beverly Hills";
  const listings = (data as any).listings || (data as any).listings_sample || [];
  const priceBands = (data as any).price_bands || [];

  // Render different content based on report type
  const renderReportContent = () => {
    switch (reportType) {
      case "new_listings_gallery":
      case "featured_listings":
        return renderGalleryContent();
      case "price_bands":
        return renderPriceBandsContent();
      case "new_listings":
        return renderNewListingsContent();
      case "inventory":
        return renderInventoryContent();
      case "closed":
        return renderClosedContent();
      case "open_houses":
        return renderOpenHousesContent();
      default:
        return renderMarketSnapshotContent();
    }
  };

  // Market Snapshot - Classic metrics layout
  const renderMarketSnapshotContent = () => (
    <div className="content-section metrics-layout">
      <div className="hero-metric">
        <div className="value">{formatCurrency(metrics.median_close_price || 4150000)}</div>
        <div className="label">Median Sale Price</div>
      </div>
      <div className="metric-grid">
        <div className="metric-card">
          <div className="value">{formatNumber(counts.Closed || 89)}</div>
          <div className="label">Homes Sold</div>
        </div>
        <div className="metric-card">
          <div className="value">{formatNumber(metrics.avg_dom || 42)}</div>
          <div className="label">Avg Days</div>
        </div>
        <div className="metric-card">
          <div className="value">{(metrics.months_of_inventory || 4.3).toFixed(1)}</div>
          <div className="label">Mo. Supply</div>
        </div>
        <div className="metric-card">
          <div className="value">{((metrics.list_to_close_ratio || 0.976) * 100).toFixed(0)}%</div>
          <div className="label">Sale-to-List</div>
        </div>
      </div>
    </div>
  );

  // Gallery/Featured - Property photo grid
  const renderGalleryContent = () => {
    const displayListings = listings.slice(0, 4);
    const totalCount = reportType === "featured_listings" 
      ? (data as any).total_listings || 4 
      : listings.length;
    
    return (
      <div className="content-section gallery-layout">
        <div className="gallery-header">
          <div className="gallery-count">{totalCount}</div>
          <div className="gallery-label">
            {reportType === "featured_listings" ? "Featured Properties" : "New on Market"}
          </div>
        </div>
        <div className="property-grid">
          {displayListings.map((listing: any, i: number) => (
            <div key={i} className="property-card">
              <div 
                className="property-image" 
                style={{ backgroundImage: `url(${listing.hero_photo_url})` }}
              >
                <div className="property-price">{formatCurrency(listing.list_price)}</div>
              </div>
              <div className="property-details">
                <div className="property-address">{listing.street_address}</div>
                <div className="property-specs">
                  {listing.bedrooms} bd • {listing.bathrooms} ba • {formatNumber(listing.sqft)} sf
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Price Bands - Visual bar chart
  const renderPriceBandsContent = () => {
    const maxCount = Math.max(...priceBands.map((b: any) => b.count));
    
    return (
      <div className="content-section pricebands-layout">
        <div className="bands-header">
          <div className="bands-title">Price Distribution</div>
          <div className="bands-subtitle">{formatNumber(priceBands.reduce((s: number, b: any) => s + b.count, 0))} Active Listings</div>
        </div>
        <div className="bands-chart">
          {priceBands.map((band: any, i: number) => (
            <div key={i} className="band-row">
              <div className="band-label">{band.label}</div>
              <div className="band-bar-container">
                <div 
                  className="band-bar" 
                  style={{ width: `${(band.count / maxCount) * 100}%` }}
                >
                  <span className="band-count">{band.count}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="bands-footer">
          <div className="band-stat">
            <span className="stat-value">{formatCurrency(metrics.median_list_price || 4250000)}</span>
            <span className="stat-label">Median Price</span>
          </div>
          <div className="band-stat">
            <span className="stat-value">{metrics.avg_dom || 42}</span>
            <span className="stat-label">Avg Days</span>
          </div>
        </div>
      </div>
    );
  };

  // New Listings - Compact property cards
  const renderNewListingsContent = () => {
    const sampleListings = (data as any).listings_sample || [];
    const displayListings = sampleListings.slice(0, 3);
    
    return (
      <div className="content-section newlistings-layout">
        <div className="nl-hero">
          <div className="nl-count">{counts.Active || 42}</div>
          <div className="nl-label">New Listings</div>
          <div className="nl-period">Last 14 Days</div>
        </div>
        <div className="nl-stats">
          <div className="nl-stat">
            <span className="stat-value">{formatCurrency(metrics.median_list_price || 4350000)}</span>
            <span className="stat-label">Median Price</span>
          </div>
          <div className="nl-stat">
            <span className="stat-value">{metrics.avg_dom || 7}</span>
            <span className="stat-label">Avg Days</span>
          </div>
        </div>
        {displayListings.length > 0 && (
          <div className="nl-listings">
            {displayListings.map((listing: any, i: number) => (
              <div key={i} className="nl-listing-row">
                <div className="nl-listing-info">
                  <div className="nl-address">{listing.address}</div>
                  <div className="nl-specs">{listing.beds}bd/{listing.baths}ba • {formatNumber(listing.sqft)}sf</div>
                </div>
                <div className="nl-price">{formatCurrency(listing.list_price)}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Inventory - Visual breakdown
  const renderInventoryContent = () => (
    <div className="content-section inventory-layout">
      <div className="inv-hero">
        <div className="inv-count">{counts.Active || 127}</div>
        <div className="inv-label">Active Listings</div>
      </div>
      <div className="inv-breakdown">
        <div className="inv-segment active-segment">
          <div className="segment-bar" style={{ height: '100%' }}></div>
          <div className="segment-info">
            <span className="segment-count">{counts.Active || 127}</span>
            <span className="segment-label">Active</span>
          </div>
        </div>
        <div className="inv-segment pending-segment">
          <div className="segment-bar" style={{ height: `${((counts.Pending || 34) / (counts.Active || 127)) * 100}%` }}></div>
          <div className="segment-info">
            <span className="segment-count">{counts.Pending || 34}</span>
            <span className="segment-label">Pending</span>
          </div>
        </div>
      </div>
      <div className="inv-stats">
        <div className="inv-stat">
          <span className="stat-value">{metrics.avg_dom || 45}</span>
          <span className="stat-label">Avg Days on Market</span>
        </div>
      </div>
    </div>
  );

  // Closed Sales - Performance focused
  const renderClosedContent = () => (
    <div className="content-section closed-layout">
      <div className="closed-hero">
        <div className="closed-count">{counts.Closed || 89}</div>
        <div className="closed-label">Homes Sold</div>
        <div className="closed-period">Last 30 Days</div>
      </div>
      <div className="closed-metrics">
        <div className="closed-metric primary">
          <div className="metric-value">{formatCurrency(metrics.median_close_price || 4150000)}</div>
          <div className="metric-label">Median Sale Price</div>
        </div>
        <div className="closed-row">
          <div className="closed-metric">
            <div className="metric-value">{metrics.avg_dom || 42}</div>
            <div className="metric-label">Avg Days</div>
          </div>
          <div className="closed-metric">
            <div className="metric-value">{formatCurrency(metrics.median_list_price || 4250000)}</div>
            <div className="metric-label">Median List</div>
          </div>
        </div>
      </div>
    </div>
  );

  // Open Houses - Event style
  const renderOpenHousesContent = () => (
    <div className="content-section openhouses-layout">
      <div className="oh-hero">
        <div className="oh-icon">🏠</div>
        <div className="oh-count">{counts.Active || 15}</div>
        <div className="oh-label">Open Houses</div>
        <div className="oh-period">This Weekend</div>
      </div>
      <div className="oh-cta">
        <div className="oh-cta-text">Schedule Your Tour</div>
        <div className="oh-cta-sub">Contact for exclusive access</div>
      </div>
    </div>
  );

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
              
              /* ===== HEADER ===== */
              .header {
                background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
                padding: 60px 60px 50px;
                text-align: center;
              }
              
              .header-logo {
                height: 70px;
                width: auto;
                max-width: 260px;
                object-fit: contain;
                margin-bottom: 20px;
                filter: brightness(0) invert(1);
              }
              
              .header-logo-placeholder {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 70px;
                height: 70px;
                background: rgba(255,255,255,0.2);
                border-radius: 16px;
                margin-bottom: 20px;
                font-size: 32px;
                font-weight: 800;
                color: white;
              }
              
              .header-badge {
                display: inline-block;
                background: rgba(255,255,255,0.2);
                color: #fff;
                font-size: 22px;
                font-weight: 600;
                padding: 10px 28px;
                border-radius: 999px;
                margin-bottom: 16px;
                letter-spacing: 1px;
                text-transform: uppercase;
              }
              
              .header-title {
                font-size: 44px;
                font-weight: 800;
                color: #fff;
                margin-bottom: 8px;
              }
              
              .header-market {
                font-size: 32px;
                font-weight: 600;
                color: rgba(255,255,255,0.9);
              }
              
              /* ===== CONTENT SECTIONS ===== */
              .content-section {
                flex: 1;
                padding: 50px;
                display: flex;
                flex-direction: column;
                justify-content: center;
              }
              
              /* --- Market Snapshot Layout --- */
              .metrics-layout .hero-metric {
                text-align: center;
                padding: 40px 30px;
                background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
                border-radius: 28px;
                margin-bottom: 30px;
              }
              
              .metrics-layout .hero-metric .value {
                font-size: 100px;
                font-weight: 900;
                color: #fff;
                line-height: 1;
              }
              
              .metrics-layout .hero-metric .label {
                font-size: 28px;
                font-weight: 600;
                color: rgba(255,255,255,0.9);
                margin-top: 12px;
                text-transform: uppercase;
                letter-spacing: 2px;
              }
              
              .metrics-layout .metric-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
              }
              
              .metrics-layout .metric-card {
                background: var(--light-gray);
                border-radius: 20px;
                padding: 32px 24px;
                text-align: center;
                border: 2px solid var(--border);
              }
              
              .metrics-layout .metric-card .value {
                font-size: 56px;
                font-weight: 800;
                color: var(--ink);
                line-height: 1;
              }
              
              .metrics-layout .metric-card .label {
                font-size: 20px;
                font-weight: 600;
                color: var(--muted);
                margin-top: 8px;
                text-transform: uppercase;
              }
              
              /* --- Gallery Layout --- */
              .gallery-layout {
                padding: 40px;
              }
              
              .gallery-header {
                text-align: center;
                margin-bottom: 30px;
              }
              
              .gallery-count {
                font-size: 80px;
                font-weight: 900;
                color: var(--primary);
                line-height: 1;
              }
              
              .gallery-label {
                font-size: 28px;
                font-weight: 700;
                color: var(--ink);
                text-transform: uppercase;
                letter-spacing: 2px;
              }
              
              .property-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                flex: 1;
              }
              
              .property-card {
                background: #fff;
                border-radius: 20px;
                overflow: hidden;
                border: 2px solid var(--border);
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
              }
              
              .property-image {
                height: 240px;
                background-size: cover;
                background-position: center;
                position: relative;
              }
              
              .property-price {
                position: absolute;
                bottom: 12px;
                left: 12px;
                background: var(--primary);
                color: #fff;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 24px;
                font-weight: 700;
              }
              
              .property-details {
                padding: 16px;
              }
              
              .property-address {
                font-size: 22px;
                font-weight: 700;
                color: var(--ink);
                margin-bottom: 4px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
              }
              
              .property-specs {
                font-size: 18px;
                color: var(--muted);
              }
              
              /* --- Price Bands Layout --- */
              .pricebands-layout {
                padding: 50px;
              }
              
              .bands-header {
                text-align: center;
                margin-bottom: 40px;
              }
              
              .bands-title {
                font-size: 40px;
                font-weight: 800;
                color: var(--ink);
              }
              
              .bands-subtitle {
                font-size: 24px;
                color: var(--muted);
                margin-top: 8px;
              }
              
              .bands-chart {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 16px;
              }
              
              .band-row {
                display: flex;
                align-items: center;
                gap: 16px;
              }
              
              .band-label {
                width: 180px;
                font-size: 22px;
                font-weight: 600;
                color: var(--ink);
                text-align: right;
              }
              
              .band-bar-container {
                flex: 1;
                height: 50px;
                background: var(--light-gray);
                border-radius: 25px;
                overflow: hidden;
              }
              
              .band-bar {
                height: 100%;
                background: linear-gradient(90deg, var(--primary), var(--accent));
                border-radius: 25px;
                display: flex;
                align-items: center;
                justify-content: flex-end;
                padding-right: 16px;
                min-width: 60px;
              }
              
              .band-count {
                font-size: 22px;
                font-weight: 700;
                color: #fff;
              }
              
              .bands-footer {
                display: flex;
                justify-content: center;
                gap: 60px;
                margin-top: 40px;
                padding-top: 30px;
                border-top: 2px solid var(--border);
              }
              
              .band-stat {
                text-align: center;
              }
              
              .band-stat .stat-value {
                display: block;
                font-size: 40px;
                font-weight: 800;
                color: var(--primary);
              }
              
              .band-stat .stat-label {
                font-size: 18px;
                color: var(--muted);
                text-transform: uppercase;
              }
              
              /* --- New Listings Layout --- */
              .newlistings-layout {
                padding: 50px;
              }
              
              .nl-hero {
                text-align: center;
                padding: 40px;
                background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
                border-radius: 28px;
                margin-bottom: 30px;
              }
              
              .nl-count {
                font-size: 120px;
                font-weight: 900;
                color: #fff;
                line-height: 1;
              }
              
              .nl-label {
                font-size: 32px;
                font-weight: 700;
                color: rgba(255,255,255,0.95);
                text-transform: uppercase;
                letter-spacing: 2px;
              }
              
              .nl-period {
                font-size: 22px;
                color: rgba(255,255,255,0.8);
                margin-top: 8px;
              }
              
              .nl-stats {
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
              }
              
              .nl-stat {
                flex: 1;
                background: var(--light-gray);
                border-radius: 20px;
                padding: 28px;
                text-align: center;
                border: 2px solid var(--border);
              }
              
              .nl-stat .stat-value {
                display: block;
                font-size: 40px;
                font-weight: 800;
                color: var(--ink);
              }
              
              .nl-stat .stat-label {
                font-size: 18px;
                color: var(--muted);
                text-transform: uppercase;
              }
              
              .nl-listings {
                background: var(--light-gray);
                border-radius: 20px;
                padding: 20px;
                border: 2px solid var(--border);
              }
              
              .nl-listing-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 0;
                border-bottom: 1px solid var(--border);
              }
              
              .nl-listing-row:last-child {
                border-bottom: none;
              }
              
              .nl-address {
                font-size: 24px;
                font-weight: 600;
                color: var(--ink);
              }
              
              .nl-specs {
                font-size: 18px;
                color: var(--muted);
              }
              
              .nl-price {
                font-size: 28px;
                font-weight: 700;
                color: var(--primary);
              }
              
              /* --- Inventory Layout --- */
              .inventory-layout {
                padding: 50px;
                align-items: center;
              }
              
              .inv-hero {
                text-align: center;
                margin-bottom: 40px;
              }
              
              .inv-count {
                font-size: 140px;
                font-weight: 900;
                color: var(--primary);
                line-height: 1;
              }
              
              .inv-label {
                font-size: 36px;
                font-weight: 700;
                color: var(--ink);
                text-transform: uppercase;
                letter-spacing: 2px;
              }
              
              .inv-breakdown {
                display: flex;
                gap: 30px;
                height: 300px;
                width: 100%;
                max-width: 600px;
                margin-bottom: 40px;
              }
              
              .inv-segment {
                flex: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
              }
              
              .segment-bar {
                width: 100%;
                border-radius: 20px;
              }
              
              .active-segment .segment-bar {
                background: linear-gradient(135deg, var(--primary), var(--accent));
              }
              
              .pending-segment .segment-bar {
                background: var(--border);
              }
              
              .segment-info {
                margin-top: 16px;
                text-align: center;
              }
              
              .segment-count {
                display: block;
                font-size: 40px;
                font-weight: 800;
                color: var(--ink);
              }
              
              .segment-label {
                font-size: 20px;
                color: var(--muted);
                text-transform: uppercase;
              }
              
              .inv-stats {
                text-align: center;
              }
              
              .inv-stat .stat-value {
                display: block;
                font-size: 60px;
                font-weight: 800;
                color: var(--ink);
              }
              
              .inv-stat .stat-label {
                font-size: 22px;
                color: var(--muted);
              }
              
              /* --- Closed Sales Layout --- */
              .closed-layout {
                padding: 50px;
              }
              
              .closed-hero {
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
                border-radius: 28px;
                margin-bottom: 30px;
              }
              
              .closed-count {
                font-size: 140px;
                font-weight: 900;
                color: #fff;
                line-height: 1;
              }
              
              .closed-label {
                font-size: 36px;
                font-weight: 700;
                color: rgba(255,255,255,0.95);
                text-transform: uppercase;
                letter-spacing: 2px;
              }
              
              .closed-period {
                font-size: 22px;
                color: rgba(255,255,255,0.8);
                margin-top: 8px;
              }
              
              .closed-metrics {
                display: flex;
                flex-direction: column;
                gap: 20px;
              }
              
              .closed-metric.primary {
                background: var(--light-gray);
                border-radius: 24px;
                padding: 40px;
                text-align: center;
                border: 2px solid var(--border);
              }
              
              .closed-metric.primary .metric-value {
                font-size: 56px;
                font-weight: 800;
                color: var(--primary);
              }
              
              .closed-metric.primary .metric-label {
                font-size: 22px;
                color: var(--muted);
                text-transform: uppercase;
                margin-top: 8px;
              }
              
              .closed-row {
                display: flex;
                gap: 20px;
              }
              
              .closed-row .closed-metric {
                flex: 1;
                background: var(--light-gray);
                border-radius: 20px;
                padding: 30px;
                text-align: center;
                border: 2px solid var(--border);
              }
              
              .closed-row .metric-value {
                font-size: 40px;
                font-weight: 800;
                color: var(--ink);
              }
              
              .closed-row .metric-label {
                font-size: 18px;
                color: var(--muted);
                text-transform: uppercase;
                margin-top: 4px;
              }
              
              /* --- Open Houses Layout --- */
              .openhouses-layout {
                padding: 50px;
                align-items: center;
                text-align: center;
              }
              
              .oh-hero {
                margin-bottom: 60px;
              }
              
              .oh-icon {
                font-size: 100px;
                margin-bottom: 20px;
              }
              
              .oh-count {
                font-size: 160px;
                font-weight: 900;
                color: var(--primary);
                line-height: 1;
              }
              
              .oh-label {
                font-size: 44px;
                font-weight: 700;
                color: var(--ink);
                text-transform: uppercase;
                letter-spacing: 2px;
              }
              
              .oh-period {
                font-size: 28px;
                color: var(--muted);
                margin-top: 12px;
              }
              
              .oh-cta {
                background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
                border-radius: 24px;
                padding: 40px 60px;
              }
              
              .oh-cta-text {
                font-size: 32px;
                font-weight: 700;
                color: #fff;
              }
              
              .oh-cta-sub {
                font-size: 22px;
                color: rgba(255,255,255,0.8);
                margin-top: 8px;
              }
              
              /* ===== FOOTER ===== */
              .footer {
                background: var(--light-gray);
                padding: 40px 50px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-top: 2px solid var(--border);
              }
              
              .footer-contact {
                display: flex;
                align-items: center;
                gap: 20px;
              }
              
              .footer-photo {
                width: 90px;
                height: 90px;
                border-radius: 50%;
                object-fit: cover;
                border: 3px solid var(--primary);
              }
              
              .footer-photo-placeholder {
                width: 90px;
                height: 90px;
                border-radius: 50%;
                background: var(--border);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                color: var(--muted);
              }
              
              .footer-info {
                display: flex;
                flex-direction: column;
                gap: 4px;
              }
              
              .footer-name {
                font-size: 28px;
                font-weight: 700;
                color: var(--ink);
              }
              
              .footer-details {
                font-size: 20px;
                color: var(--muted);
              }
              
              .footer-website {
                font-size: 20px;
                color: var(--primary);
                font-weight: 600;
              }
              
              .footer-logo {
                height: 70px;
                width: auto;
                max-width: 180px;
                object-fit: contain;
              }
              
              .footer-brand-text {
                font-size: 26px;
                font-weight: 700;
                color: var(--primary);
              }
              
              /* Sample watermark */
              .sample-watermark {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 120px;
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

          {/* Report-specific Content */}
          {renderReportContent()}

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
