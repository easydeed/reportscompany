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
const DEFAULT_PRIMARY_COLOR = "#7C3AED";
const DEFAULT_ACCENT_COLOR = "#F26B2B";

/**
 * Inject brand colors into social template
 */
function injectBrand(html: string, brand: any): string {
  if (!brand) return html;

  const primaryColor = brand.primary_color || DEFAULT_PRIMARY_COLOR;
  const accentColor = brand.accent_color || DEFAULT_ACCENT_COLOR;
  const brandName = brand.display_name || "TrendyReports";
  const logoUrl = brand.logo_url || "";
  const footerLogoUrl = brand.footer_logo_url || logoUrl;
  const repPhotoUrl = brand.rep_photo_url || "";
  const contactLine1 = brand.contact_line1 || "";
  const contactLine2 = brand.contact_line2 || "";
  const websiteUrl = brand.website_url || "";

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

  const replacements: Record<string, string> = {
    "{{market_name}}": r.city || "Market",
    "{{period_label}}": r.period_label || `Last ${lookback} days`,
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

  const replacements: Record<string, string> = {
    "{{market_name}}": r.city || "Market",
    "{{period_label}}": r.period_label || `Last ${lookback} days`,
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

  const replacements: Record<string, string> = {
    "{{market_name}}": r.city || "Market",
    "{{period_label}}": r.period_label || `Last ${lookback} days`,
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

  const replacements: Record<string, string> = {
    "{{market_name}}": r.city || "Market",
    "{{period_label}}": r.period_label || `Last ${lookback} days`,
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

  // Get the first listing as the featured property
  const featured = listings[0] || {};

  const replacements: Record<string, string> = {
    "{{market_name}}": r.city || "Market",
    "{{hero_photo_url}}": featured.hero_photo_url || "",
    "{{list_price}}": formatCurrency(featured.list_price),
    "{{street_address}}": featured.street_address || "Address not available",
    "{{city}}": featured.city || r.city || "",
    "{{zip_code}}": featured.zip_code || "",
    "{{bedrooms}}": formatNumber(featured.bedrooms),
    "{{bathrooms}}": formatDecimal(featured.bathrooms, 1),
    "{{sqft}}": formatNumber(featured.sqft),
    "{{days_on_market}}": formatNumber(featured.days_on_market || 0),
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

  const replacements: Record<string, string> = {
    "{{market_name}}": r.city || "Market",
    "{{period_label}}": r.period_label || `Last ${lookback} days`,
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
  const topBands = bands.slice(0, 3);
  const bandsHtml = topBands.map((band: any) => {
    const percentage = totalListings > 0 ? ((band.count || 0) / totalListings) * 100 : 0;
    return `
      <div class="price-band">
        <div class="band-header">
          <div class="band-label">${band.label || "—"}</div>
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
