/**
 * Template utilities for TrendyReports PDF generation
 * 
 * These functions map report data (result_json) to HTML template placeholders
 * following the pattern: {{placeholder_name}} → actual value
 */

// Format currency
function formatCurrency(val: number | null | undefined): string {
  if (val == null || isNaN(val)) return "—";
  return "$" + Math.round(val).toLocaleString();
}

// Format number with commas
function formatNumber(val: number | null | undefined): string {
  if (val == null || isNaN(val)) return "—";
  return Math.round(val).toLocaleString();
}

// Format decimal
function formatDecimal(val: number | null | undefined, decimals: number = 1): string {
  if (val == null || isNaN(val)) return "—";
  return val.toFixed(decimals);
}

// Format percentage
function formatPercent(val: number | null | undefined): string {
  if (val == null || isNaN(val)) return "—";
  return val.toFixed(1);
}

/**
 * Build Market Snapshot HTML from template + data
 */
export function buildMarketSnapshotHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const counts = r.counts || {};
  
  // Calculate derived values
  const activeCount = counts.Active ?? 0;
  const pendingCount = counts.Pending ?? 0;
  const closedCount = counts.Closed ?? 0;
  
  // MOI calculation: (active listings / closed sales) * (lookback days / 30)
  const lookback = r.lookback_days || 30;
  const moi = closedCount > 0 ? (activeCount / closedCount) * (lookback / 30) : 0;
  
  // Sale-to-List ratio
  const closeToListRatio = (metrics.median_close_price && metrics.median_list_price)
    ? (metrics.median_close_price / metrics.median_list_price) * 100
    : 0;
  
  // Property type data (placeholder - needs worker enhancement)
  const byType = r.by_property_type || {};
  
  // Price tier data (placeholder - needs worker enhancement)
  const tiers = r.price_tiers || {};
  
  // Build replacements map
  const replacements: Record<string, string> = {
    // Header
    "{{market_name}}": r.city || "Market",
    "{{period_label}}": r.period_label || `Last ${lookback} days`,
    "{{report_date}}": r.report_date || new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    }),
    "{{lookback_days}}": String(lookback),
    
    // Hero ribbon KPIs
    "{{median_price}}": formatCurrency(metrics.median_close_price || metrics.median_list_price),
    "{{closed_sales}}": formatNumber(closedCount),
    "{{avg_dom}}": formatDecimal(metrics.avg_dom),
    "{{moi}}": formatDecimal(moi),
    
    // Core indicators
    "{{new_listings}}": formatNumber(activeCount), // Approximation
    "{{new_listings_delta}}": "0", // TODO: Calculate from historical
    "{{new_listings_delta_class}}": "up",
    "{{new_listings_fill}}": String(Math.min(100, (activeCount / 100) * 100)),
    
    "{{pendings}}": formatNumber(pendingCount),
    "{{pendings_delta}}": "0",
    "{{pendings_delta_class}}": "up",
    "{{pendings_fill}}": String(Math.min(100, (pendingCount / 50) * 100)),
    
    "{{close_to_list_ratio}}": formatPercent(closeToListRatio),
    "{{ctl_delta}}": "0",
    "{{ctl_delta_class}}": closeToListRatio >= 100 ? "up" : "down",
    "{{ctl_fill}}": String(Math.min(100, closeToListRatio)),
    
    // By Property Type
    "{{sfr_median}}": formatCurrency(byType.SFR?.median || metrics.median_close_price),
    "{{sfr_closed}}": formatNumber(byType.SFR?.count || Math.round(closedCount * 0.7)),
    "{{sfr_dom}}": formatDecimal(byType.SFR?.dom || metrics.avg_dom),
    
    "{{condo_median}}": formatCurrency(byType.Condo?.median || metrics.median_close_price * 0.7),
    "{{condo_closed}}": formatNumber(byType.Condo?.count || Math.round(closedCount * 0.2)),
    "{{condo_dom}}": formatDecimal(byType.Condo?.dom || metrics.avg_dom),
    
    "{{th_median}}": formatCurrency(byType.Townhome?.median || metrics.median_close_price * 0.85),
    "{{th_closed}}": formatNumber(byType.Townhome?.count || Math.round(closedCount * 0.1)),
    "{{th_dom}}": formatDecimal(byType.Townhome?.dom || metrics.avg_dom),
    
    // By Price Tier
    "{{tier1_median}}": formatCurrency(tiers.entry?.median || metrics.median_close_price * 0.6),
    "{{tier1_closed}}": formatNumber(tiers.entry?.count || Math.round(closedCount * 0.3)),
    "{{tier1_moi}}": formatDecimal(tiers.entry?.moi || moi * 0.8),
    
    "{{tier2_median}}": formatCurrency(tiers.move_up?.median || metrics.median_close_price),
    "{{tier2_closed}}": formatNumber(tiers.move_up?.count || Math.round(closedCount * 0.5)),
    "{{tier2_moi}}": formatDecimal(tiers.move_up?.moi || moi),
    
    "{{tier3_median}}": formatCurrency(tiers.luxury?.median || metrics.median_close_price * 2),
    "{{tier3_closed}}": formatNumber(tiers.luxury?.count || Math.round(closedCount * 0.2)),
    "{{tier3_moi}}": formatDecimal(tiers.luxury?.moi || moi * 1.5),
  };
  
  // Apply all replacements
  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }
  
  return html;
}

/**
 * Build New Listings HTML from template + data
 */
export function buildNewListingsHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const counts = r.counts || {};
  const lookback = r.lookback_days || 30;
  
  // Build header and ribbon replacements
  const replacements: Record<string, string> = {
    "{{market_name}}": r.city || "Market",
    "{{period_label}}": r.period_label || `Last ${lookback} days`,
    "{{report_date}}": r.report_date || new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    }),
    "{{lookback_days}}": String(lookback),
    "{{total_new}}": formatNumber(counts.Active || 0),
    "{{median_price}}": formatCurrency(metrics.median_list_price),
    "{{avg_dom}}": formatDecimal(metrics.avg_dom),
    "{{avg_ppsf}}": formatDecimal(metrics.avg_ppsf || 0),
  };
  
  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }
  
  // Build table rows
  const listings = r.listings_sample || [];
  const sortedListings = listings.slice().sort((a: any, b: any) => 
    (b.list_date || "").localeCompare(a.list_date || "")
  );
  
  const rows = sortedListings.map((listing: any) => `
    <tr>
      <td>${listing.city || r.city || "—"}</td>
      <td>${listing.address || "—"}</td>
      <td class="t-right">${formatCurrency(listing.list_price)}</td>
      <td class="t-right">${formatNumber(listing.beds)}</td>
      <td class="t-right">${formatDecimal(listing.baths, 1)}</td>
      <td class="t-right">${formatNumber(listing.sqft)}</td>
      <td class="t-right">${formatNumber(listing.days_on_market)}</td>
      <td class="t-right">${listing.list_date ? new Date(listing.list_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : "—"}</td>
    </tr>
  `).join('');
  
  html = html.replace('<!-- LISTINGS_TABLE_ROWS -->', rows);
  
  return html;
}

/**
 * Build Inventory HTML from template + data
 */
export function buildInventoryHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const counts = r.counts || {};
  const lookback = r.lookback_days || 30;
  
  const activeCount = counts.Active ?? 0;
  const closedCount = counts.Closed ?? 0;
  const moi = closedCount > 0 ? (activeCount / closedCount) * (lookback / 30) : 0;
  
  const replacements: Record<string, string> = {
    "{{market_name}}": r.city || "Market",
    "{{period_label}}": r.period_label || `Last ${lookback} days`,
    "{{report_date}}": r.report_date || new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    }),
    "{{lookback_days}}": String(lookback),
    "{{total_active}}": formatNumber(activeCount),
    "{{new_this_month}}": formatNumber(activeCount), // Approximation
    "{{median_dom}}": formatDecimal(metrics.avg_dom),
    "{{moi}}": formatDecimal(moi),
  };
  
  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }
  
  // Build table rows
  const listings = r.listings_sample || [];
  const sortedListings = listings
    .filter((l: any) => l.status === "Active")
    .sort((a: any, b: any) => (b.days_on_market || 0) - (a.days_on_market || 0));
  
  const rows = sortedListings.map((listing: any) => `
    <tr>
      <td>${listing.city || r.city || "—"}</td>
      <td>${listing.address || "—"}</td>
      <td class="t-right">${formatCurrency(listing.list_price)}</td>
      <td class="t-right">${formatNumber(listing.beds)}</td>
      <td class="t-right">${formatDecimal(listing.baths, 1)}</td>
      <td class="t-right">${formatNumber(listing.sqft)}</td>
      <td class="t-right">${formatNumber(listing.days_on_market)}</td>
      <td class="t-right">${listing.status || "Active"}</td>
    </tr>
  `).join('');
  
  html = html.replace('<!-- LISTINGS_TABLE_ROWS -->', rows);
  
  return html;
}

/**
 * Build Closed Listings HTML from template + data
 */
export function buildClosedHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const counts = r.counts || {};
  const lookback = r.lookback_days || 30;
  
  const closeToListRatio = (metrics.median_close_price && metrics.median_list_price)
    ? (metrics.median_close_price / metrics.median_list_price) * 100
    : 0;
  
  const replacements: Record<string, string> = {
    "{{market_name}}": r.city || "Market",
    "{{period_label}}": r.period_label || `Last ${lookback} days`,
    "{{report_date}}": r.report_date || new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    }),
    "{{lookback_days}}": String(lookback),
    "{{total_closed}}": formatNumber(counts.Closed || 0),
    "{{median_price}}": formatCurrency(metrics.median_close_price),
    "{{avg_dom}}": formatDecimal(metrics.avg_dom),
    "{{ctl}}": formatDecimal(closeToListRatio, 1),
  };
  
  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }
  
  // Build table rows
  const listings = r.listings_sample || [];
  const sortedListings = listings
    .filter((l: any) => l.status === "Closed")
    .sort((a: any, b: any) => (b.close_date || "").localeCompare(a.close_date || ""));
  
  const rows = sortedListings.map((listing: any) => `
    <tr>
      <td>${listing.city || r.city || "—"}</td>
      <td>${listing.address || "—"}</td>
      <td class="t-right">${formatCurrency(listing.close_price || listing.list_price)}</td>
      <td class="t-right">${formatNumber(listing.beds)}</td>
      <td class="t-right">${formatDecimal(listing.baths, 1)}</td>
      <td class="t-right">${formatNumber(listing.sqft)}</td>
      <td class="t-right">${formatNumber(listing.days_on_market)}</td>
      <td class="t-right">${listing.close_date ? new Date(listing.close_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : "—"}</td>
    </tr>
  `).join('');
  
  html = html.replace('<!-- LISTINGS_TABLE_ROWS -->', rows);
  
  return html;
}

/**
 * Build Price Bands HTML from template + data
 */
export function buildPriceBandsHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const lookback = r.lookback_days || 30;
  const bands = r.price_bands || [];
  
  // Calculate totals
  const totalListings = bands.reduce((sum: number, b: any) => sum + (b.count || 0), 0);
  const prices = bands.flatMap((b: any) => b.listings || []).map((l: any) => l.list_price || 0).filter((p: number) => p > 0);
  const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
  const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;
  
  // Find hottest and slowest bands
  const sortedByDom = bands.slice().sort((a: any, b: any) => (a.avg_dom || 999) - (b.avg_dom || 999));
  const hottest = sortedByDom[0] || {};
  const slowest = sortedByDom[sortedByDom.length - 1] || {};
  
  const replacements: Record<string, string> = {
    "{{market_name}}": r.city || "Market",
    "{{period_label}}": r.period_label || `Last ${lookback} days`,
    "{{report_date}}": r.report_date || new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    }),
    "{{lookback_days}}": String(lookback),
    "{{total_listings}}": formatNumber(totalListings),
    "{{median_price}}": formatCurrency(metrics.median_list_price),
    "{{avg_dom}}": formatDecimal(metrics.avg_dom),
    "{{price_range}}": `${formatCurrency(minPrice)} - ${formatCurrency(maxPrice)}`,
    "{{hottest_band}}": hottest.label || "—",
    "{{hottest_count}}": formatNumber(hottest.count || 0),
    "{{hottest_dom}}": formatNumber(hottest.avg_dom || 0),
    "{{slowest_band}}": slowest.label || "—",
    "{{slowest_count}}": formatNumber(slowest.count || 0),
    "{{slowest_dom}}": formatNumber(slowest.avg_dom || 0),
  };
  
  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }
  
  // Build price bands
  const bandsHtml = bands.map((band: any) => {
    const percentage = totalListings > 0 ? ((band.count || 0) / totalListings) * 100 : 0;
    
    return `
      <div class="price-band">
        <div class="band-title">${band.label || "—"}</div>
        <div class="band-count">${formatNumber(band.count || 0)} listings (${percentage.toFixed(1)}% of market)</div>
        <div class="bar-container">
          <div class="bar-fill" style="width: ${percentage}%;">
            ${percentage.toFixed(1)}%
          </div>
        </div>
        <div class="band-metrics">
          <div class="metric">
            <div class="metric-label">Median Price</div>
            <div class="metric-value">${formatCurrency(band.median_price || 0)}</div>
          </div>
          <div class="metric">
            <div class="metric-label">Avg DOM</div>
            <div class="metric-value">${formatNumber(band.avg_dom || 0)}</div>
          </div>
          <div class="metric">
            <div class="metric-label">Price/SqFt</div>
            <div class="metric-value">${formatCurrency(band.avg_ppsf || 0)}</div>
          </div>
        </div>
      </div>
    `;
  }).join('');
  
  html = html.replace('<!-- PRICE_BANDS_CONTENT -->', bandsHtml);
  
  return html;
}

