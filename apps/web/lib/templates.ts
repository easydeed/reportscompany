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
  // TODO: Implement in Phase 26B.1
  return templateHtml;
}

/**
 * Build Inventory HTML from template + data
 */
export function buildInventoryHtml(
  templateHtml: string,
  data: any
): string {
  // TODO: Implement in Phase 26B.2
  return templateHtml;
}

/**
 * Build Closed Listings HTML from template + data
 */
export function buildClosedHtml(
  templateHtml: string,
  data: any
): string {
  // TODO: Implement in Phase 26B.3
  return templateHtml;
}

/**
 * Build Price Bands HTML from template + data
 */
export function buildPriceBandsHtml(
  templateHtml: string,
  data: any
): string {
  // TODO: Implement in Phase 26B.4
  return templateHtml;
}

