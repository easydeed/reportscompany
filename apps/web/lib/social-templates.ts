/**
 * Social Media Template Builders for TrendyReports
 *
 * These functions build 1080x1920 HTML templates for social media sharing
 * (Instagram Stories, TikTok, etc.)
 *
 * Each template incorporates:
 * - User's branding (colors, logos)
 * - Agent headshot and contact info
 * - Key metrics from the report
 */

// Default TrendyReports brand colors
const DEFAULT_PRIMARY_COLOR = "#4F46E5";
const DEFAULT_ACCENT_COLOR = "#F26B2B";

/**
 * Escape HTML special characters to prevent XSS attacks.
 * All user-provided strings must be passed through this function.
 */
function escapeHtml(unsafe: string | null | undefined): string {
  if (unsafe == null) return "";
  return String(unsafe)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Sanitize a URL - only allow http, https, and data URLs
 */
function sanitizeUrl(url: string | null | undefined): string {
  if (!url) return "";
  const trimmed = String(url).trim();
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://") || trimmed.startsWith("data:")) {
    return trimmed;
  }
  return "";
}

/**
 * Inject brand colors into social template
 * All brand values are sanitized to prevent XSS
 */
function injectBrand(html: string, brand: any): string {
  if (!brand) return html;

  // Sanitize color values - only allow valid hex colors
  const colorRegex = /^#[0-9A-Fa-f]{6}$/;
  const primaryColor = colorRegex.test(brand.primary_color) ? brand.primary_color : DEFAULT_PRIMARY_COLOR;
  const accentColor = colorRegex.test(brand.accent_color) ? brand.accent_color : DEFAULT_ACCENT_COLOR;
  
  // Sanitize text values
  const brandName = escapeHtml(brand.display_name) || "TrendyReports";
  const contactLine1 = escapeHtml(brand.contact_line1) || "";
  const contactLine2 = escapeHtml(brand.contact_line2) || "";
  const websiteUrl = escapeHtml(brand.website_url) || "";
  
  // Sanitize URLs
  const logoUrl = sanitizeUrl(brand.logo_url);
  const footerLogoUrl = sanitizeUrl(brand.footer_logo_url) || logoUrl;
  const repPhotoUrl = sanitizeUrl(brand.rep_photo_url);

  // Inject CSS color overrides
  const colorOverride = `
    <style>
      :root {
        --pct-blue: ${primaryColor};
        --pct-accent: ${accentColor};
      }
    </style>
  `;

  let result = html.replace("</head>", `${colorOverride}</head>`);

  // Replace brand placeholders
  result = result.replaceAll("{{brand_name}}", brandName);
  result = result.replaceAll("{{logo_url}}", logoUrl);
  result = result.replaceAll("{{footer_logo_url}}", footerLogoUrl);
  result = result.replaceAll("{{rep_photo_url}}", repPhotoUrl);
  result = result.replaceAll("{{contact_line1}}", contactLine1);
  result = result.replaceAll("{{contact_line2}}", contactLine2);
  result = result.replaceAll("{{website_url}}", websiteUrl);

  // Handle conditionals
  if (repPhotoUrl) {
    result = result.replace(/\{\{#if rep_photo_url\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
  } else {
    result = result.replace(/\{\{#if rep_photo_url\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  }

  if (contactLine1) {
    result = result.replace(/\{\{#if contact_line1\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
  } else {
    result = result.replace(/\{\{#if contact_line1\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  }

  if (contactLine2) {
    result = result.replace(/\{\{#if contact_line2\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
  } else {
    result = result.replace(/\{\{#if contact_line2\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  }

  if (websiteUrl) {
    result = result.replace(/\{\{#if website_url\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
  } else {
    result = result.replace(/\{\{#if website_url\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  }

  if (logoUrl) {
    result = result.replace(/\{\{#if logo_url\}\}([\s\S]*?)\{\{else\}\}[\s\S]*?\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if logo_url\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
  } else {
    result = result.replace(/\{\{#if logo_url\}\}[\s\S]*?\{\{else\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if logo_url\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  }

  if (footerLogoUrl) {
    result = result.replace(/\{\{#if footer_logo_url\}\}([\s\S]*?)\{\{else\}\}[\s\S]*?\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if footer_logo_url\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
  } else {
    result = result.replace(/\{\{#if footer_logo_url\}\}[\s\S]*?\{\{else\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if footer_logo_url\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  }

  return result;
}

// Format helpers
function formatCurrency(val: number | null | undefined): string {
  if (val == null || isNaN(val)) return "—";
  if (val >= 1000000) {
    return "$" + (val / 1000000).toFixed(1) + "M";
  }
  if (val >= 1000) {
    return "$" + Math.round(val / 1000) + "K";
  }
  return "$" + Math.round(val).toLocaleString();
}

function formatNumber(val: number | null | undefined): string {
  if (val == null || isNaN(val)) return "—";
  return Math.round(val).toLocaleString();
}

function formatDecimal(val: number | null | undefined, decimals: number = 1): string {
  if (val == null || isNaN(val)) return "—";
  return val.toFixed(decimals);
}

function formatPercent(val: number | null | undefined): string {
  if (val == null || isNaN(val)) return "—";
  return val.toFixed(0);
}

/**
 * Build Social Market Snapshot HTML
 */
export function buildSocialMarketSnapshotHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const counts = r.counts || {};
  const lookback = r.lookback_days || 30;

  const closedCount = counts.Closed ?? 0;
  const activeCount = counts.Active ?? 0;
  const moi = metrics.months_of_inventory ?? (closedCount > 0 ? activeCount / closedCount : 0);

  const closeToListRatio = metrics.close_to_list_ratio ?? (
    (metrics.median_close_price && metrics.median_list_price)
      ? (metrics.median_close_price / metrics.median_list_price) * 100
      : 0
  );

  // All user-provided text is escaped to prevent XSS
  const replacements: Record<string, string> = {
    "{{market_name}}": escapeHtml(r.city) || "Market",
    "{{period_label}}": escapeHtml(r.period_label) || `Last ${lookback} days`,
    "{{report_date}}": r.report_date || new Date().toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }),
    "{{median_price}}": formatCurrency(metrics.median_close_price || metrics.median_list_price),
    "{{closed_sales}}": formatNumber(closedCount),
    "{{avg_dom}}": formatNumber(Math.round(metrics.avg_dom || 0)),
    "{{moi}}": formatDecimal(moi),
    "{{close_to_list_ratio}}": formatPercent(closeToListRatio),
  };

  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }

  return injectBrand(html, data.brand);
}

/**
 * Build Social New Listings HTML
 */
export function buildSocialNewListingsHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const counts = r.counts || {};
  const lookback = r.lookback_days || 30;

  const newListingsCount = counts.NewListings ?? counts.Active ?? metrics.new_listings_count ?? 0;

  // All user-provided text is escaped to prevent XSS
  const replacements: Record<string, string> = {
    "{{market_name}}": escapeHtml(r.city) || "Market",
    "{{period_label}}": escapeHtml(r.period_label) || `Last ${lookback} days`,
    "{{report_date}}": r.report_date || new Date().toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }),
    "{{new_listings}}": formatNumber(newListingsCount),
    "{{median_price}}": formatCurrency(metrics.median_list_price),
    "{{avg_dom}}": formatNumber(Math.round(metrics.avg_dom || 0)),
  };

  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }

  return injectBrand(html, data.brand);
}

/**
 * Build Social Closed Sales HTML
 */
export function buildSocialClosedHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const counts = r.counts || {};
  const lookback = r.lookback_days || 30;

  const closedCount = counts.Closed ?? 0;
  const closeToListRatio = metrics.close_to_list_ratio ?? (
    (metrics.median_close_price && metrics.median_list_price)
      ? (metrics.median_close_price / metrics.median_list_price) * 100
      : 0
  );

  // All user-provided text is escaped to prevent XSS
  const replacements: Record<string, string> = {
    "{{market_name}}": escapeHtml(r.city) || "Market",
    "{{period_label}}": escapeHtml(r.period_label) || `Last ${lookback} days`,
    "{{report_date}}": r.report_date || new Date().toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }),
    "{{closed_sales}}": formatNumber(closedCount),
    "{{median_price}}": formatCurrency(metrics.median_close_price),
    "{{avg_dom}}": formatNumber(Math.round(metrics.avg_dom || 0)),
    "{{close_to_list_ratio}}": formatPercent(closeToListRatio),
  };

  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }

  return injectBrand(html, data.brand);
}

/**
 * Build Social Inventory HTML
 */
export function buildSocialInventoryHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const counts = r.counts || {};
  const lookback = r.lookback_days || 30;

  const activeCount = counts.Active ?? 0;
  const closedCount = counts.Closed ?? 0;
  const moi = metrics.months_of_inventory ?? (closedCount > 0 ? (activeCount / closedCount) * (lookback / 30) : 0);

  // All user-provided text is escaped to prevent XSS
  const replacements: Record<string, string> = {
    "{{market_name}}": escapeHtml(r.city) || "Market",
    "{{period_label}}": escapeHtml(r.period_label) || `Last ${lookback} days`,
    "{{report_date}}": r.report_date || new Date().toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }),
    "{{active_listings}}": formatNumber(activeCount),
    "{{median_price}}": formatCurrency(metrics.median_list_price),
    "{{avg_dom}}": formatNumber(Math.round(metrics.avg_dom || 0)),
    "{{moi}}": formatDecimal(moi),
  };

  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }

  return injectBrand(html, data.brand);
}

/**
 * Build Social Gallery HTML (for new_listings_gallery and featured_listings)
 * Uses the first listing as the featured property
 */
export function buildSocialGalleryHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const listings = r.listings || r.listings_sample || [];

  // Get the first listing as the featured property, with safe defaults
  const featured = listings[0] || {};
  
  // Check if we have a valid featured listing
  const hasValidListing = featured && (featured.street_address || featured.list_price);

  // All user-provided text is escaped to prevent XSS
  // URLs are sanitized to prevent javascript: injection
  const replacements: Record<string, string> = {
    "{{market_name}}": escapeHtml(r.city) || "Market",
    "{{hero_photo_url}}": sanitizeUrl(featured.hero_photo_url),
    "{{list_price}}": hasValidListing ? formatCurrency(featured.list_price) : "—",
    "{{street_address}}": escapeHtml(featured.street_address) || "Property Details Coming Soon",
    "{{city}}": escapeHtml(featured.city || r.city) || "",
    "{{zip_code}}": escapeHtml(featured.zip_code) || "",
    "{{bedrooms}}": hasValidListing ? formatNumber(featured.bedrooms) : "—",
    "{{bathrooms}}": hasValidListing ? formatDecimal(featured.bathrooms, 1) : "—",
    "{{sqft}}": hasValidListing ? formatNumber(featured.sqft) : "—",
    "{{days_on_market}}": hasValidListing ? formatNumber(featured.days_on_market || 0) : "—",
  };

  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }

  return injectBrand(html, data.brand);
}

/**
 * Build Social Price Bands HTML
 */
export function buildSocialPriceBandsHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const lookback = r.lookback_days || 30;
  const bands = r.price_bands || [];

  const totalListings = bands.reduce((sum: number, b: any) => sum + (b.count || 0), 0);

  // All user-provided text is escaped to prevent XSS
  const replacements: Record<string, string> = {
    "{{market_name}}": escapeHtml(r.city) || "Market",
    "{{period_label}}": escapeHtml(r.period_label) || `Last ${lookback} days`,
    "{{report_date}}": r.report_date || new Date().toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }),
    "{{total_listings}}": formatNumber(totalListings),
    "{{median_price}}": formatCurrency(metrics.median_list_price),
  };

  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }

  // Build price bands visualization (top 3)
  // All band labels are escaped to prevent XSS
  const topBands = bands.slice(0, 3);
  const bandsHtml = topBands.map((band: any) => {
    const percentage = totalListings > 0 ? ((band.count || 0) / totalListings) * 100 : 0;
    const safeLabel = escapeHtml(band.label) || "—";
    return `
      <div class="price-band">
        <div class="band-header">
          <div class="band-label">${safeLabel}</div>
          <div class="band-count">${formatNumber(band.count)} listings</div>
        </div>
        <div class="band-bar-container">
          <div class="band-bar" style="width: ${Math.max(15, percentage)}%;">
            <span class="band-bar-text">${percentage.toFixed(0)}%</span>
          </div>
        </div>
        <div class="band-stats">
          <div class="band-stat">
            <div class="band-stat-value">${formatCurrency(band.median_price)}</div>
            <div class="band-stat-label">Median</div>
          </div>
          <div class="band-stat">
            <div class="band-stat-value">${formatNumber(band.avg_dom || 0)}</div>
            <div class="band-stat-label">Avg DOM</div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  html = html.replace('<!-- PRICE_BANDS_SOCIAL -->', bandsHtml);

  return injectBrand(html, data.brand);
}
