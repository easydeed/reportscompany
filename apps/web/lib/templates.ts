/**
 * Template utilities for TrendyReports PDF generation
 * 
 * Phase 26: Convert PCT templates to TrendyReports branded PDFs
 * Phase 30: Support white-label branding for affiliate accounts
 * 
 * These functions map report data (result_json) to HTML template placeholders
 * following the pattern: {{placeholder_name}} → actual value
 * 
 * SECURITY: All user-provided content is escaped to prevent XSS attacks.
 */

// Default TrendyReports brand colors (Phase 26)
const DEFAULT_PRIMARY_COLOR = "#7C3AED"; // Trendy violet
const DEFAULT_ACCENT_COLOR = "#F26B2B";  // Trendy coral

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
 * Validate hex color - only allow valid 6-digit hex colors
 */
function sanitizeColor(color: string | null | undefined, fallback: string): string {
  if (!color) return fallback;
  const colorRegex = /^#[0-9A-Fa-f]{6}$/;
  return colorRegex.test(color) ? color : fallback;
}

/**
 * Phase 30: Inject brand colors and metadata into template
 * SECURITY: All brand values are sanitized to prevent XSS
 * 
 * IMPORTANT: This function MUST process ALL Handlebars-style conditionals,
 * even when brand data is missing. Otherwise raw {{#if}} tags appear in output.
 */
function injectBrand(html: string, brand: any): string {
  // Provide default brand if none supplied to ensure conditionals are processed
  const safeBrand = brand || {
    display_name: "TrendyReports",
    primary_color: DEFAULT_PRIMARY_COLOR,
    accent_color: DEFAULT_ACCENT_COLOR,
  };
  
  // Sanitize colors - only allow valid hex
  const primaryColor = sanitizeColor(safeBrand.primary_color, DEFAULT_PRIMARY_COLOR);
  const accentColor = sanitizeColor(safeBrand.accent_color, DEFAULT_ACCENT_COLOR);
  
  // Sanitize text values to prevent XSS
  const brandName = escapeHtml(safeBrand.display_name) || "TrendyReports";
  
  // Sanitize URLs
  const logoUrl = sanitizeUrl(safeBrand.logo_url);
  const footerLogoUrl = sanitizeUrl(safeBrand.footer_logo_url) || logoUrl;
  const repPhotoUrl = sanitizeUrl(safeBrand.rep_photo_url);
  const contactLine1 = escapeHtml(safeBrand.contact_line1) || "";
  const contactLine2 = escapeHtml(safeBrand.contact_line2) || "";
  const websiteUrl = escapeHtml(safeBrand.website_url) || "";
  
  // Inject CSS color overrides right before </head>
  const colorOverride = `
    <style>
      :root {
        --pct-blue: ${primaryColor};
        --pct-accent: ${accentColor};
      }
    </style>
  `;
  
  let result = html.replace("</head>", `${colorOverride}</head>`);
  
  // Replace brand placeholders FIRST (before conditionals)
  result = result.replaceAll("{{brand_name}}", brandName);
  result = result.replaceAll("{{brand_logo_url}}", logoUrl);
  result = result.replaceAll("{{brand_badge}}", `${brandName} Insights`);
  
  // Replace contact/branding placeholders
  result = result.replaceAll("{{logo_url}}", logoUrl);
  result = result.replaceAll("{{footer_logo_url}}", footerLogoUrl);
  result = result.replaceAll("{{rep_photo_url}}", repPhotoUrl);
  result = result.replaceAll("{{contact_line1}}", contactLine1);
  result = result.replaceAll("{{contact_line2}}", contactLine2);
  result = result.replaceAll("{{website_url}}", websiteUrl);
  
  // Process Handlebars-style conditionals
  // CRITICAL: Process {{#if...}}{{else}}{{/if}} BEFORE simple {{#if...}}{{/if}}
  // to avoid partial matches
  
  // rep_photo_url conditionals
  if (repPhotoUrl) {
    result = result.replace(/\{\{#if\s+rep_photo_url\s*\}\}([\s\S]*?)\{\{else\}\}[\s\S]*?\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if\s+rep_photo_url\s*\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
  } else {
    result = result.replace(/\{\{#if\s+rep_photo_url\s*\}\}[\s\S]*?\{\{else\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if\s+rep_photo_url\s*\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  }
  
  // contact_line1 conditionals
  if (contactLine1) {
    result = result.replace(/\{\{#if\s+contact_line1\s*\}\}([\s\S]*?)\{\{else\}\}[\s\S]*?\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if\s+contact_line1\s*\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
  } else {
    result = result.replace(/\{\{#if\s+contact_line1\s*\}\}[\s\S]*?\{\{else\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if\s+contact_line1\s*\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  }
  
  // contact_line2 conditionals
  if (contactLine2) {
    result = result.replace(/\{\{#if\s+contact_line2\s*\}\}([\s\S]*?)\{\{else\}\}[\s\S]*?\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if\s+contact_line2\s*\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
  } else {
    result = result.replace(/\{\{#if\s+contact_line2\s*\}\}[\s\S]*?\{\{else\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if\s+contact_line2\s*\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  }
  
  // website_url conditionals
  if (websiteUrl) {
    result = result.replace(/\{\{#if\s+website_url\s*\}\}([\s\S]*?)\{\{else\}\}[\s\S]*?\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if\s+website_url\s*\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
  } else {
    result = result.replace(/\{\{#if\s+website_url\s*\}\}[\s\S]*?\{\{else\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if\s+website_url\s*\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  }
  
  // logo_url conditionals
  if (logoUrl) {
    result = result.replace(/\{\{#if\s+logo_url\s*\}\}([\s\S]*?)\{\{else\}\}[\s\S]*?\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if\s+logo_url\s*\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
  } else {
    result = result.replace(/\{\{#if\s+logo_url\s*\}\}[\s\S]*?\{\{else\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if\s+logo_url\s*\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  }
  
  // footer_logo_url conditionals (separate from header logo)
  if (footerLogoUrl) {
    result = result.replace(/\{\{#if\s+footer_logo_url\s*\}\}([\s\S]*?)\{\{else\}\}[\s\S]*?\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if\s+footer_logo_url\s*\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
  } else {
    result = result.replace(/\{\{#if\s+footer_logo_url\s*\}\}[\s\S]*?\{\{else\}\}([\s\S]*?)\{\{\/if\}\}/g, '$1');
    result = result.replace(/\{\{#if\s+footer_logo_url\s*\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  }
  
  // Tagline for footer
  const tagline = safeBrand.display_name 
    ? `${brandName} • Market Intelligence`
    : "TrendyReports • Market Intelligence Powered by Live MLS Data";
  result = result.replaceAll("{{brand_tagline}}", tagline);
  
  // CLEANUP: Remove any remaining Handlebars tags that weren't matched
  // This prevents raw {{...}} from appearing in the final output
  result = result.replace(/\{\{#if\s+\w+\s*\}\}[\s\S]*?\{\{\/if\}\}/g, '');
  result = result.replace(/\{\{[^}]+\}\}/g, '');
  
  return result;
}

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
 * Build branded footer HTML with proper XSS protection
 * SECURITY: All brand values are escaped/sanitized
 */
function buildBrandedFooterHtml(brand: any, brandName: string, reportDate: string): string {
  // Sanitize all brand values
  const safeRepPhotoUrl = sanitizeUrl(brand?.rep_photo_url);
  const safeContactLine1 = escapeHtml(brand?.contact_line1) || "";
  const safeContactLine2 = escapeHtml(brand?.contact_line2) || "";
  const safeWebsiteUrl = escapeHtml(brand?.website_url) || "";
  const safeFooterLogoUrl = sanitizeUrl(brand?.footer_logo_url) || sanitizeUrl(brand?.logo_url);
  const safeBrandName = escapeHtml(brandName);
  const safeReportDate = escapeHtml(reportDate);
  
  return `
    <div class="page-footer">
      <section class="branded-footer avoid-break">
        <div class="branded-footer-contact">
          ${safeRepPhotoUrl ? `<img src="${safeRepPhotoUrl}" alt="${safeContactLine1}" class="branded-footer-photo" />` : ''}
          <div class="branded-footer-info">
            ${safeContactLine1 ? `<div class="branded-footer-name">${safeContactLine1}</div>` : ''}
            ${safeContactLine2 ? `<div class="branded-footer-details">${safeContactLine2}</div>` : ''}
            ${safeWebsiteUrl ? `<div class="branded-footer-website">${safeWebsiteUrl}</div>` : ''}
          </div>
        </div>
        <div class="branded-footer-logo">
          ${safeFooterLogoUrl
            ? `<img src="${safeFooterLogoUrl}" alt="${safeBrandName}" class="logo-img" />`
            : `<div style="font-size: 14px; font-weight: 600; color: var(--pct-blue);">${safeBrandName}</div>`
          }
        </div>
      </section>
      <footer class="footer">
        Report generated by ${safeBrandName} • Data source: MLS • ${safeReportDate}
      </footer>
    </div>
  `;
}

/**
 * Build hero header HTML (V2 - Full-bleed gradient)
 * Used across all report types for consistent branding
 * SECURITY: All values are pre-sanitized by injectBrand, but we double-check here
 * 
 * @param reportType - Base report type (e.g., "new_listings_gallery")
 * @param brandName - Brand display name
 * @param brandBadge - Badge text (e.g., "TrendyReports Insights")
 * @param logoUrl - Optional logo URL
 * @param presetDisplayName - Optional preset name to override default (e.g., "Condo Watch")
 */
function buildHeroHeader(
  reportType: string,
  brandName: string,
  brandBadge: string,
  logoUrl?: string,
  presetDisplayName?: string
): string {
  const reportLabels: Record<string, string> = {
    new_listings: "New Listings",
    inventory: "Inventory Report",
    closed: "Closed Sales",
    price_bands: "Price Analysis",
    new_listings_gallery: "New Listings Gallery",
    featured_listings: "Featured Listings",
  };
  // Use preset display name if available, otherwise fall back to default label
  const reportLabel = presetDisplayName || reportLabels[reportType] || "Market Report";
  
  // Sanitize inputs (defensive - should already be sanitized by caller)
  const safeBrandName = escapeHtml(brandName);
  const safeBrandBadge = escapeHtml(brandBadge);
  const safeLogoUrl = sanitizeUrl(logoUrl);
  
  return `
    <div class="hero-header">
      <div class="hero-left">
        ${safeLogoUrl 
          ? `<img src="${safeLogoUrl}" alt="${safeBrandName}" class="hero-logo" />`
          : ''
        }
        <div class="hero-text">
          <div class="hero-brand-name">${safeBrandName}</div>
          <div class="hero-report-type">${reportLabel}</div>
        </div>
      </div>
      <div class="hero-right">
        <span class="pdf-badge">PDF</span>
        <span class="affiliate-pill">${safeBrandBadge}</span>
      </div>
    </div>
  `;
}

/**
 * Build title bar HTML (below hero header)
 * SECURITY: User-provided values are escaped
 */
function buildTitleBar(
  title: string,
  marketName: string,
  periodLabel: string,
  reportDate: string
): string {
  // Sanitize all user-provided values
  const safeTitle = escapeHtml(title);
  const safeMarketName = escapeHtml(marketName);
  const safePeriodLabel = escapeHtml(periodLabel);
  const safeReportDate = escapeHtml(reportDate);
  
  return `
    <div class="title-bar">
      <h1>${safeTitle} — ${safeMarketName}</h1>
      <p class="sub">Period: ${safePeriodLabel} • Source: Live MLS Data • Report Date: ${safeReportDate}</p>
    </div>
  `;
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
  
  // Get counts from result_json (these are now date-filtered by the worker)
  const activeCount = counts.Active ?? 0;
  const pendingCount = counts.Pending ?? 0;
  const closedCount = counts.Closed ?? 0;  // Now accurately filtered by close_date
  const newListingsCount = counts.NewListings ?? metrics.new_listings_count ?? 0;
  
  // Use metrics from worker (already calculated correctly)
  const lookback = r.lookback_days || 30;
  const moi = metrics.months_of_inventory ?? (closedCount > 0 ? activeCount / closedCount : 0);
  
  // Sale-to-List ratio - use from metrics if available
  const closeToListRatio = metrics.close_to_list_ratio ?? (
    (metrics.median_close_price && metrics.median_list_price)
      ? (metrics.median_close_price / metrics.median_list_price) * 100
      : 0
  );
  
  // Property type data from worker
  const byType = r.by_property_type || {};
  
  // Price tier data from worker
  const tiers = r.price_tiers || {};
  
  // Build replacements map
  // SECURITY: All user-provided text values are escaped
  const replacements: Record<string, string> = {
    // Header - escape user-provided text
    "{{market_name}}": escapeHtml(r.city) || "Market",
    "{{period_label}}": escapeHtml(r.period_label) || `Last ${lookback} days`,
    "{{report_date}}": escapeHtml(r.report_date) || new Date().toLocaleDateString('en-US', {
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
    "{{new_listings}}": formatNumber(newListingsCount),  // New listings in period
    "{{new_listings_delta}}": "",  // Historical comparison not yet implemented
    "{{new_listings_delta_class}}": "neutral",
    "{{new_listings_fill}}": String(Math.min(100, (newListingsCount / 100) * 100)),
    
    "{{pendings}}": formatNumber(pendingCount),
    "{{pendings_delta}}": "",  // Historical comparison not yet implemented
    "{{pendings_delta_class}}": "neutral",
    "{{pendings_fill}}": String(Math.min(100, (pendingCount / 50) * 100)),
    
    "{{close_to_list_ratio}}": formatPercent(closeToListRatio),
    "{{ctl_delta}}": "",  // Historical comparison not yet implemented
    "{{ctl_delta_class}}": closeToListRatio >= 100 ? "up" : "neutral",
    "{{ctl_fill}}": String(Math.min(100, closeToListRatio)),
    
    // By Property Type - use actual data from result_json
    // byType is a dict like { "SFR": { label, count, median_price, avg_dom }, ... }
    "{{sfr_median}}": formatCurrency(byType.SFR?.median_price ?? 0),
    "{{sfr_closed}}": formatNumber(byType.SFR?.count ?? 0),
    "{{sfr_dom}}": formatDecimal(byType.SFR?.avg_dom ?? 0),
    
    "{{condo_median}}": formatCurrency(byType.Condo?.median_price ?? 0),
    "{{condo_closed}}": formatNumber(byType.Condo?.count ?? 0),
    "{{condo_dom}}": formatDecimal(byType.Condo?.avg_dom ?? 0),
    
    "{{th_median}}": formatCurrency(byType.Townhome?.median_price ?? 0),
    "{{th_closed}}": formatNumber(byType.Townhome?.count ?? 0),
    "{{th_dom}}": formatDecimal(byType.Townhome?.avg_dom ?? 0),
    
    // By Price Tier - use actual data from result_json
    // tiers is a dict like { "Entry": { label, count, median_price, moi }, ... }
    "{{tier1_median}}": formatCurrency(tiers.Entry?.median_price ?? 0),
    "{{tier1_closed}}": formatNumber(tiers.Entry?.count ?? 0),
    "{{tier1_moi}}": formatDecimal(tiers.Entry?.moi ?? 0),
    
    "{{tier2_median}}": formatCurrency(tiers["Move-Up"]?.median_price ?? 0),
    "{{tier2_closed}}": formatNumber(tiers["Move-Up"]?.count ?? 0),
    "{{tier2_moi}}": formatDecimal(tiers["Move-Up"]?.moi ?? 0),
    
    "{{tier3_median}}": formatCurrency(tiers.Luxury?.median_price ?? 0),
    "{{tier3_closed}}": formatNumber(tiers.Luxury?.count ?? 0),
    "{{tier3_moi}}": formatDecimal(tiers.Luxury?.moi ?? 0),
  };
  
  // Apply all replacements
  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }
  
  // Phase 30: Inject brand colors and metadata
  return injectBrand(html, data.brand);
}

/**
 * Build New Listings HTML from template + data (paginated)
 */
export function buildNewListingsHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const counts = r.counts || {};
  const lookback = r.lookback_days || 30;

  // Pagination: ~15 rows per page
  const ROWS_PER_PAGE = 15;

  // Get and sort listings
  const listings = r.listings_sample || [];
  const sortedListings = listings.slice().sort((a: any, b: any) =>
    (b.list_date || "").localeCompare(a.list_date || "")
  );

  const totalPages = Math.max(1, Math.ceil(sortedListings.length / ROWS_PER_PAGE));

  // Common data
  const marketName = r.city || "Market";
  const periodLabel = r.period_label || `Last ${lookback} days`;
  const reportDate = r.report_date || new Date().toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric'
  });
  const brandName = data.brand?.display_name || "TrendyReports";
  const brandBadge = `${brandName} Insights`;
  // Smart Preset display name (e.g., "Condo Watch" instead of "New Listings Gallery")
  const presetDisplayName = r.preset_display_name || null;

  // Footer HTML (reused on each page) - uses XSS-protected helper
  const footerHtml = buildBrandedFooterHtml(data.brand, brandName, reportDate);

  // Build row HTML helper
  // Note: Field mapping from PropertyDataExtractor:
  // - street_address (not address)
  // - bedrooms (not beds)
  // - bathrooms (not baths)
  // - price_per_sqft for $/sqft
  // SECURITY: All user-provided text is escaped
  const buildRow = (listing: any) => `
    <tr>
      <td>${escapeHtml(listing.city || r.city) || "—"}</td>
      <td>${escapeHtml(listing.street_address) || "—"}</td>
      <td class="t-right">${formatCurrency(listing.list_price)}</td>
      <td class="t-right">${formatNumber(listing.bedrooms)}</td>
      <td class="t-right">${formatDecimal(listing.bathrooms, 1)}</td>
      <td class="t-right">${formatNumber(listing.sqft)}</td>
      <td class="t-right">${formatNumber(listing.days_on_market)}</td>
      <td class="t-right">${listing.list_date ? new Date(listing.list_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : "—"}</td>
    </tr>
  `;

  // Table header (reused on each page)
  const tableHeader = `
    <thead>
      <tr>
        <th>City</th>
        <th>Address</th>
        <th class="t-right">List Price</th>
        <th class="t-right">Beds</th>
        <th class="t-right">Baths</th>
        <th class="t-right">SqFt</th>
        <th class="t-right">DOM</th>
        <th class="t-right">List Date</th>
      </tr>
    </thead>
  `;

  // Generate pages
  const pages: string[] = [];

  for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
    const startIdx = (pageNum - 1) * ROWS_PER_PAGE;
    const pageListings = sortedListings.slice(startIdx, startIdx + ROWS_PER_PAGE);
    const rowsHtml = pageListings.map(buildRow).join('');

    let headerHtml: string;
    if (pageNum === 1) {
      // V2: Hero header for first page
      const logoUrl = data.brand?.logo_url || "";
      const titleBarName = presetDisplayName || "New Listings";
      headerHtml = `
        ${buildHeroHeader("new_listings", brandName, brandBadge, logoUrl, presetDisplayName)}
        ${buildTitleBar(titleBarName, marketName, periodLabel, reportDate)}
        <section class="ribbon avoid-break">
          <div class="kpi">
            <div class="item"><div class="lbl">Total New Listings</div><div class="val">${formatNumber(counts.Active || 0)}</div></div>
            <div class="item"><div class="lbl">Median List Price</div><div class="val">${formatCurrency(metrics.median_list_price)}</div></div>
            <div class="item"><div class="lbl">Avg DOM</div><div class="val">${formatDecimal(metrics.avg_dom)}</div></div>
            <div class="item"><div class="lbl">Avg Price/SqFt</div><div class="val">${formatCurrency(metrics.avg_ppsf || 0)}</div></div>
          </div>
          <div class="chip">Last ${lookback} days</div>
        </section>
      `;
    } else {
      // Condensed header for continuation pages
      const titleBarName = presetDisplayName || "New Listings";
      headerHtml = `
        <div class="header-continuation">
          <div class="title">${titleBarName} — ${marketName} (continued)</div>
          <div class="page-info">Page ${pageNum} of ${totalPages}</div>
        </div>
      `;
    }

    const pageHtml = `
      <div class="page">
        <div class="page-content">
          ${headerHtml}
          <section class="stack data-section">
            <div class="card">
              ${pageNum === 1 ? `<h3>${presetDisplayName || "New Listings"} — Sorted by List Date</h3>` : ''}
              <table>
                ${tableHeader}
                <tbody>${rowsHtml}</tbody>
              </table>
            </div>
          </section>
        </div>
        ${footerHtml}
      </div>
    `;

    pages.push(pageHtml);
  }

  // Replace placeholder with all pages
  let html = templateHtml.replace('<!-- TABLE_PAGES -->', pages.join('\n'));

  // Phase 30: Inject brand colors and metadata
  return injectBrand(html, data.brand);
}

/**
 * Build Inventory HTML from template + data (paginated)
 */
export function buildInventoryHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const counts = r.counts || {};
  const lookback = r.lookback_days || 30;

  // Pagination: ~15 rows per page
  const ROWS_PER_PAGE = 15;

  // Calculate MOI
  const activeCount = counts.Active ?? 0;
  const closedCount = counts.Closed ?? 0;
  const moi = closedCount > 0 ? (activeCount / closedCount) * (lookback / 30) : 0;

  // Get and sort listings
  const listings = r.listings_sample || [];
  const sortedListings = listings
    .filter((l: any) => l.status === "Active")
    .sort((a: any, b: any) => (b.days_on_market || 0) - (a.days_on_market || 0));

  const totalPages = Math.max(1, Math.ceil(sortedListings.length / ROWS_PER_PAGE));

  // Common data
  const marketName = r.city || "Market";
  const periodLabel = r.period_label || `Last ${lookback} days`;
  const reportDate = r.report_date || new Date().toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric'
  });
  const brandName = data.brand?.display_name || "TrendyReports";
  const brandBadge = `${brandName} Insights`;
  // Smart Preset display name (e.g., "Condo Watch" instead of "Inventory Report")
  const presetDisplayName = r.preset_display_name || null;

  // Footer HTML (reused on each page) - uses XSS-protected helper
  const footerHtml = buildBrandedFooterHtml(data.brand, brandName, reportDate);

  // Build row HTML helper (Inventory)
  // Note: Field mapping from PropertyDataExtractor:
  // - street_address (not address)
  // - bedrooms (not beds)
  // - bathrooms (not baths)
  // SECURITY: All user-provided text is escaped
  const buildRow = (listing: any) => `
    <tr>
      <td>${escapeHtml(listing.city || r.city) || "—"}</td>
      <td>${escapeHtml(listing.street_address) || "—"}</td>
      <td class="t-right">${formatCurrency(listing.list_price)}</td>
      <td class="t-right">${formatNumber(listing.bedrooms)}</td>
      <td class="t-right">${formatDecimal(listing.bathrooms, 1)}</td>
      <td class="t-right">${formatNumber(listing.sqft)}</td>
      <td class="t-right">${formatNumber(listing.days_on_market)}</td>
      <td class="t-right">${escapeHtml(listing.status) || "Active"}</td>
    </tr>
  `;

  // Table header (reused on each page)
  const tableHeader = `
    <thead>
      <tr>
        <th>City</th>
        <th>Address</th>
        <th class="t-right">List Price</th>
        <th class="t-right">Beds</th>
        <th class="t-right">Baths</th>
        <th class="t-right">SqFt</th>
        <th class="t-right">DOM</th>
        <th class="t-right">Status</th>
      </tr>
    </thead>
  `;

  // Generate pages
  const pages: string[] = [];

  for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
    const startIdx = (pageNum - 1) * ROWS_PER_PAGE;
    const pageListings = sortedListings.slice(startIdx, startIdx + ROWS_PER_PAGE);
    const rowsHtml = pageListings.map(buildRow).join('');

    let headerHtml: string;
    if (pageNum === 1) {
      // V2: Hero header for first page
      const logoUrl = data.brand?.logo_url || "";
      const titleBarName = presetDisplayName || "Listing Inventory";
      headerHtml = `
        ${buildHeroHeader("inventory", brandName, brandBadge, logoUrl, presetDisplayName)}
        ${buildTitleBar(titleBarName, marketName, periodLabel, reportDate)}
        <section class="ribbon avoid-break">
          <div class="kpi">
            <div class="item"><div class="lbl">Total Active Listings</div><div class="val">${formatNumber(activeCount)}</div></div>
            <div class="item"><div class="lbl">New This Month</div><div class="val">${formatNumber(activeCount)}</div></div>
            <div class="item"><div class="lbl">Median DOM</div><div class="val">${formatDecimal(metrics.avg_dom)}</div></div>
            <div class="item"><div class="lbl">Months of Inventory</div><div class="val">${formatDecimal(moi)}</div></div>
          </div>
          <div class="chip">Current Snapshot</div>
        </section>
      `;
    } else {
      // Condensed header for continuation pages
      const titleBarName = presetDisplayName || "Listing Inventory";
      headerHtml = `
        <div class="header-continuation">
          <div class="title">${titleBarName} — ${marketName} (continued)</div>
          <div class="page-info">Page ${pageNum} of ${totalPages}</div>
        </div>
      `;
    }

    // V6: Hero header must be OUTSIDE page-content for proper negative margin bleed
    // This matches the Market Snapshot template structure
    const pageHtml = pageNum === 1
      ? `
      <div class="page">
        ${headerHtml}
        <div class="page-content">
          <section class="stack data-section">
            <div class="card">
              <h3>Active Listings — Sorted by Days on Market</h3>
              <table>
                ${tableHeader}
                <tbody>${rowsHtml}</tbody>
              </table>
            </div>
          </section>
        </div>
        ${footerHtml}
      </div>
      `
      : `
      <div class="page">
        <div class="page-content">
          ${headerHtml}
          <section class="stack data-section">
            <div class="card">
              <table>
                ${tableHeader}
                <tbody>${rowsHtml}</tbody>
              </table>
            </div>
          </section>
        </div>
        ${footerHtml}
      </div>
      `;

    pages.push(pageHtml);
  }

  // Replace placeholder with all pages
  let html = templateHtml.replace('<!-- TABLE_PAGES -->', pages.join('\n'));

  // Phase 30: Inject brand colors and metadata
  return injectBrand(html, data.brand);
}

/**
 * Build Closed Listings HTML from template + data (paginated)
 */
export function buildClosedHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const counts = r.counts || {};
  const lookback = r.lookback_days || 30;

  // Pagination: ~15 rows per page
  const ROWS_PER_PAGE = 15;

  // Calculate close-to-list ratio
  const closeToListRatio = (metrics.median_close_price && metrics.median_list_price)
    ? (metrics.median_close_price / metrics.median_list_price) * 100
    : 0;

  // Get and sort listings
  const listings = r.listings_sample || [];
  const sortedListings = listings
    .filter((l: any) => l.status === "Closed")
    .sort((a: any, b: any) => (b.close_date || "").localeCompare(a.close_date || ""));

  const totalPages = Math.max(1, Math.ceil(sortedListings.length / ROWS_PER_PAGE));

  // Common data
  const marketName = r.city || "Market";
  const periodLabel = r.period_label || `Last ${lookback} days`;
  const reportDate = r.report_date || new Date().toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric'
  });
  const brandName = data.brand?.display_name || "TrendyReports";
  const brandBadge = `${brandName} Insights`;
  // Smart Preset display name
  const presetDisplayName = r.preset_display_name || null;

  // Footer HTML (reused on each page) - uses XSS-protected helper
  const footerHtml = buildBrandedFooterHtml(data.brand, brandName, reportDate);

  // Build row HTML helper (Closed)
  // Note: Field mapping from PropertyDataExtractor:
  // - street_address (not address)
  // - bedrooms (not beds)
  // - bathrooms (not baths)
  // SECURITY: All user-provided text is escaped
  const buildRow = (listing: any) => `
    <tr>
      <td>${escapeHtml(listing.city || r.city) || "—"}</td>
      <td>${escapeHtml(listing.street_address) || "—"}</td>
      <td class="t-right">${formatCurrency(listing.close_price || listing.list_price)}</td>
      <td class="t-right">${formatNumber(listing.bedrooms)}</td>
      <td class="t-right">${formatDecimal(listing.bathrooms, 1)}</td>
      <td class="t-right">${formatNumber(listing.sqft)}</td>
      <td class="t-right">${formatNumber(listing.days_on_market)}</td>
      <td class="t-right">${listing.close_date ? new Date(listing.close_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : "—"}</td>
    </tr>
  `;

  // Table header (reused on each page)
  const tableHeader = `
    <thead>
      <tr>
        <th>City</th>
        <th>Address</th>
        <th class="t-right">Close Price</th>
        <th class="t-right">Beds</th>
        <th class="t-right">Baths</th>
        <th class="t-right">SqFt</th>
        <th class="t-right">DOM</th>
        <th class="t-right">Close Date</th>
      </tr>
    </thead>
  `;

  // Generate pages
  const pages: string[] = [];

  for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
    const startIdx = (pageNum - 1) * ROWS_PER_PAGE;
    const pageListings = sortedListings.slice(startIdx, startIdx + ROWS_PER_PAGE);
    const rowsHtml = pageListings.map(buildRow).join('');

    let headerHtml: string;
    if (pageNum === 1) {
      // V2: Hero header for first page
      const logoUrl = data.brand?.logo_url || "";
      const titleBarName = presetDisplayName || "Closed Sales";
      headerHtml = `
        ${buildHeroHeader("closed", brandName, brandBadge, logoUrl, presetDisplayName)}
        ${buildTitleBar(titleBarName, marketName, periodLabel, reportDate)}
        <section class="ribbon avoid-break">
          <div class="kpi">
            <div class="item"><div class="lbl">Total Closed</div><div class="val">${formatNumber(counts.Closed || 0)}</div></div>
            <div class="item"><div class="lbl">Median Close Price</div><div class="val">${formatCurrency(metrics.median_close_price)}</div></div>
            <div class="item"><div class="lbl">Avg DOM</div><div class="val">${formatDecimal(metrics.avg_dom)}</div></div>
            <div class="item"><div class="lbl">Close-to-List Ratio</div><div class="val">${formatDecimal(closeToListRatio, 1)}%</div></div>
          </div>
          <div class="chip">Last ${lookback} days</div>
        </section>
      `;
    } else {
      // Condensed header for continuation pages
      headerHtml = `
        <div class="header-continuation">
          <div class="title">Closed Sales — ${marketName} (continued)</div>
          <div class="page-info">Page ${pageNum} of ${totalPages}</div>
        </div>
      `;
    }

    // V6: Hero header must be OUTSIDE page-content for proper negative margin bleed
    // This matches the Market Snapshot template structure
    const pageHtml = pageNum === 1
      ? `
      <div class="page">
        ${headerHtml}
        <div class="page-content">
          <section class="stack data-section">
            <div class="card">
              <h3>Closed Listings — Sorted by Close Date</h3>
              <table>
                ${tableHeader}
                <tbody>${rowsHtml}</tbody>
              </table>
            </div>
          </section>
        </div>
        ${footerHtml}
      </div>
      `
      : `
      <div class="page">
        <div class="page-content">
          ${headerHtml}
          <section class="stack data-section">
            <div class="card">
              <table>
                ${tableHeader}
                <tbody>${rowsHtml}</tbody>
              </table>
            </div>
          </section>
        </div>
        ${footerHtml}
      </div>
      `;

    pages.push(pageHtml);
  }

  // Replace placeholder with all pages
  let html = templateHtml.replace('<!-- TABLE_PAGES -->', pages.join('\n'));

  // Phase 30: Inject brand colors and metadata
  return injectBrand(html, data.brand);
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
  
  // Phase 30: Inject brand colors and metadata
  return injectBrand(html, data.brand);
}

/**
 * Phase P2: Build New Listings Gallery HTML (3×2 photo grid per page, paginated)
 */
export function buildNewListingsGalleryHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const lookback = r.lookback_days || 30;
  const listings = r.listings || [];

  // Pagination: 6 cards per page (3 columns × 2 rows)
  const CARDS_PER_PAGE = 6;
  const totalPages = Math.max(1, Math.ceil(listings.length / CARDS_PER_PAGE));

  // Common data
  const marketName = r.city || "Market";
  const periodLabel = r.period_label || `Last ${lookback} days`;
  const reportDate = r.report_date || new Date().toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric'
  });
  const brandName = data.brand?.display_name || "TrendyReports";
  const brandBadge = `${brandName} Insights`;
  // Smart Preset display name (e.g., "Condo Watch" instead of "New Listings Gallery")
  const presetDisplayName = r.preset_display_name || null;

  // Footer HTML (reused on each page) - uses XSS-protected helper
  const footerHtml = buildBrandedFooterHtml(data.brand, brandName, reportDate);

  // Build card HTML helper
  // Photos use CSS background-image with MLS URLs (or R2 URLs when photo proxy is enabled)
  // V2.5: Added icons for beds/baths/sqft, increased text sizes
  // SECURITY: All user-provided text is escaped
  const bedIcon = `<svg class="detail-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7v11m0-4h18m0 4v-8a2 2 0 0 0-2-2H5m14 0V5a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v4"/></svg>`;
  const bathIcon = `<svg class="detail-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12h16a1 1 0 0 1 1 1v3a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4v-3a1 1 0 0 1 1-1zM6 12V5a2 2 0 0 1 2-2h1"/><circle cx="9" cy="5" r="1"/></svg>`;
  const sqftIcon = `<svg class="detail-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 3v18"/></svg>`;
  
  const buildCard = (listing: any) => {
    // Sanitize photo URL - only allow valid URLs
    const photoUrl = sanitizeUrl(listing.hero_photo_url);
    // Handle both base64 data URIs and regular URLs (sanitizeUrl allows data: URIs)
    const bgStyle = photoUrl ? `background-image:url('${photoUrl.replaceAll("'", "%27")}');` : "";
    return `
      <div class="property-card avoid-break">
        <div class="photo-container" style="${bgStyle}"></div>
        <div class="info">
          <div class="address">${escapeHtml(listing.street_address) || "Address not available"}</div>
          <div class="city">${escapeHtml(listing.city || r.city) || ""}, ${escapeHtml(listing.zip_code) || ""}</div>
          <div class="price">${formatCurrency(listing.list_price)}</div>
          <div class="details">
            <div class="detail">${bedIcon} ${formatNumber(listing.bedrooms)} bd</div>
            <div class="detail">${bathIcon} ${formatDecimal(listing.bathrooms, 1)} ba</div>
            <div class="detail">${sqftIcon} ${formatNumber(listing.sqft)} sf</div>
          </div>
        </div>
      </div>
    `;
  };

  // Generate pages
  const pages: string[] = [];

  for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
    const startIdx = (pageNum - 1) * CARDS_PER_PAGE;
    const pageListings = listings.slice(startIdx, startIdx + CARDS_PER_PAGE);
    const cardsHtml = pageListings.map((listing: any) => buildCard(listing)).join('');

    let pageHtml: string;
    if (pageNum === 1) {
      // V2.3: Hero header OUTSIDE page-content for full-bleed
      const logoUrl = data.brand?.logo_url || "";
      const titleBarName = presetDisplayName || "New Listings Gallery";
      const ribbonLabel = presetDisplayName ? presetDisplayName.toUpperCase() : "NEW LISTINGS";
      pageHtml = `
      <div class="page">
        ${buildHeroHeader("new_listings_gallery", brandName, brandBadge, logoUrl, presetDisplayName)}
        <div class="page-content">
          ${buildTitleBar(titleBarName, marketName, periodLabel, reportDate)}
          <section class="ribbon avoid-break">
            <div class="count">${formatNumber(r.total_listings || listings.length)}</div>
            <div class="label">${ribbonLabel} — LAST ${lookback} DAYS</div>
          </section>
          <section class="gallery-grid">
            ${cardsHtml}
          </section>
        </div>
        ${footerHtml}
      </div>
      `;
    } else {
      // Condensed header for continuation pages
      const titleBarName = presetDisplayName || "New Listings Gallery";
      pageHtml = `
      <div class="page">
        <div class="page-content" style="padding-top: 0.4in;">
          <div class="header-continuation">
            <div class="title">${titleBarName} — ${marketName} (continued)</div>
            <div class="page-info">Page ${pageNum} of ${totalPages}</div>
          </div>
          <section class="gallery-grid">
            ${cardsHtml}
          </section>
        </div>
        ${footerHtml}
      </div>
      `;
    }

    pages.push(pageHtml);
  }

  // Replace placeholder with all pages
  let html = templateHtml.replace('<!-- GALLERY_PAGES -->', pages.join('\n'));

  // Phase 30: Inject brand colors and metadata
  return injectBrand(html, data.brand);
}

/**
 * Phase P2: Build Featured Listings HTML (2×2 large photo grid)
 */
export function buildFeaturedListingsHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const lookback = r.lookback_days || 30;
  
  // Smart Preset display name (e.g., "Luxury Showcase" instead of "Featured Listings")
  const presetDisplayName = r.preset_display_name || null;
  const reportTitle = presetDisplayName || "Featured Listings";
  const ribbonLabel = presetDisplayName ? presetDisplayName.toUpperCase() : "FEATURED PROPERTIES";
  
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
    "{{total_listings}}": formatNumber(r.total_listings || 0),
    "{{report_title}}": escapeHtml(reportTitle),
    "{{ribbon_label}}": escapeHtml(ribbonLabel),
  };
  
  let html = templateHtml;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }
  
  // Build featured cards
  // Note: onerror handler provides fallback if MLS photo URL fails to load (common in PDF rendering)
  const fallbackImgFeatured = "https://via.placeholder.com/600x400/e5e7eb/9ca3af?text=No+Image";
  const listings = r.listings || [];
  const cards = listings.map((listing: any) => {
    const photoUrl = listing.hero_photo_url || fallbackImgFeatured;
    
    return `
      <div class="featured-card avoid-break">
        <img src="${photoUrl}" alt="${listing.street_address || 'Property'}" class="photo" onerror="this.onerror=null; this.src='${fallbackImgFeatured}';" />
        <div class="info">
          <div class="address">${listing.street_address || "Address not available"}</div>
          <div class="city">${listing.city || r.city || ""}, ${listing.zip_code || ""}</div>
          <div class="price">${formatCurrency(listing.list_price)}</div>
          <div class="details">
            <div class="detail">
              <div class="label">Bedrooms</div>
              <div class="value">${formatNumber(listing.bedrooms)} bd</div>
            </div>
            <div class="detail">
              <div class="label">Bathrooms</div>
              <div class="value">${formatDecimal(listing.bathrooms, 1)} ba</div>
            </div>
            <div class="detail">
              <div class="label">Square Feet</div>
              <div class="value">${formatNumber(listing.sqft)} sqft</div>
            </div>
            <div class="detail">
              <div class="label">Price/SqFt</div>
              <div class="value">${formatCurrency(listing.price_per_sqft || 0)}</div>
            </div>
            <div class="detail">
              <div class="label">Days on Market</div>
              <div class="value">${formatNumber(listing.days_on_market)}</div>
            </div>
            <div class="detail">
              <div class="label">Listed</div>
              <div class="value">${listing.list_date || "—"}</div>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
  
  html = html.replace('<!-- FEATURED_CARDS -->', cards);
  
  // Phase 30: Inject brand colors and metadata
  return injectBrand(html, data.brand);
}

