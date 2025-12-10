/**
 * Template utilities for TrendyReports PDF generation
 * 
 * Phase 26: Convert PCT templates to TrendyReports branded PDFs
 * Phase 30: Support white-label branding for affiliate accounts
 * 
 * These functions map report data (result_json) to HTML template placeholders
 * following the pattern: {{placeholder_name}} → actual value
 */

// Default TrendyReports brand colors (Phase 26)
const DEFAULT_PRIMARY_COLOR = "#7C3AED"; // Trendy violet
const DEFAULT_ACCENT_COLOR = "#F26B2B";  // Trendy coral

/**
 * Phase 30: Inject brand colors and metadata into template
 */
function injectBrand(html: string, brand: any): string {
  if (!brand) return html;
  
  const primaryColor = brand.primary_color || DEFAULT_PRIMARY_COLOR;
  const accentColor = brand.accent_color || DEFAULT_ACCENT_COLOR;
  const brandName = brand.display_name || "TrendyReports";
  const logoUrl = brand.logo_url || "";
  const repPhotoUrl = brand.rep_photo_url || "";
  const contactLine1 = brand.contact_line1 || "";
  const contactLine2 = brand.contact_line2 || "";
  const websiteUrl = brand.website_url || "";
  
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
  
  // Replace brand placeholders
  result = result.replaceAll("{{brand_name}}", brandName);
  result = result.replaceAll("{{brand_logo_url}}", logoUrl);
  result = result.replaceAll("{{brand_badge}}", `${brandName} Insights`);
  
  // Replace contact/branding placeholders
  result = result.replaceAll("{{logo_url}}", logoUrl);
  result = result.replaceAll("{{rep_photo_url}}", repPhotoUrl);
  result = result.replaceAll("{{contact_line1}}", contactLine1);
  result = result.replaceAll("{{contact_line2}}", contactLine2);
  result = result.replaceAll("{{website_url}}", websiteUrl);
  
  // Handle Handlebars-style conditionals for branded footer
  // {{#if rep_photo_url}}...{{/if}}
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
  
  // Tagline for footer
  const tagline = brand.display_name 
    ? `${brandName} • Market Intelligence`
    : "TrendyReports • Market Intelligence Powered by Live MLS Data";
  result = result.replaceAll("{{brand_tagline}}", tagline);
  
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
    "{{new_listings}}": formatNumber(newListingsCount),  // New listings in period
    "{{new_listings_delta}}": "0", // TODO: Calculate from historical
    "{{new_listings_delta_class}}": "up",
    "{{new_listings_fill}}": String(Math.min(100, (newListingsCount / 100) * 100)),
    
    "{{pendings}}": formatNumber(pendingCount),
    "{{pendings_delta}}": "0",
    "{{pendings_delta_class}}": "up",
    "{{pendings_fill}}": String(Math.min(100, (pendingCount / 50) * 100)),
    
    "{{close_to_list_ratio}}": formatPercent(closeToListRatio),
    "{{ctl_delta}}": "0",
    "{{ctl_delta_class}}": closeToListRatio >= 100 ? "up" : "down",
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

  // Footer HTML (reused on each page)
  const footerHtml = `
    <section class="branded-footer avoid-break">
      <div class="branded-footer-contact">
        ${data.brand?.rep_photo_url ? `<img src="${data.brand.rep_photo_url}" alt="${data.brand?.contact_line1 || ''}" class="branded-footer-photo" />` : ''}
        <div class="branded-footer-info">
          ${data.brand?.contact_line1 ? `<div class="branded-footer-name">${data.brand.contact_line1}</div>` : ''}
          ${data.brand?.contact_line2 ? `<div class="branded-footer-details">${data.brand.contact_line2}</div>` : ''}
          ${data.brand?.website_url ? `<div class="branded-footer-website">${data.brand.website_url}</div>` : ''}
        </div>
      </div>
      <div class="branded-footer-logo">
        ${data.brand?.logo_url
          ? `<img src="${data.brand.logo_url}" alt="${brandName}" class="logo-img" />`
          : `<div style="font-size: 14px; font-weight: 600; color: var(--pct-blue);">${brandName}</div>`
        }
      </div>
    </section>
    <footer class="footer">
      Report generated by ${brandName} • Data source: MLS • ${reportDate}
    </footer>
  `;

  // Build row HTML helper
  // Note: Field mapping from PropertyDataExtractor:
  // - street_address (not address)
  // - bedrooms (not beds)
  // - bathrooms (not baths)
  // - price_per_sqft for $/sqft
  const buildRow = (listing: any) => `
    <tr>
      <td>${listing.city || r.city || "—"}</td>
      <td>${listing.street_address || "—"}</td>
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
      // Full header for first page
      headerHtml = `
        <header class="header avoid-break">
          <div class="brand">
            <div class="title-block">
              <h1>New Listings — ${marketName}</h1>
              <div class="sub">Period: ${periodLabel} • Source: Live MLS Data • Report Date: ${reportDate}</div>
            </div>
          </div>
          <div class="badge">${brandBadge}</div>
        </header>
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
      headerHtml = `
        <div class="header-continuation">
          <div class="title">New Listings — ${marketName} (continued)</div>
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
              ${pageNum === 1 ? '<h3>New Listings — Sorted by List Date</h3>' : ''}
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

  // Footer HTML (reused on each page)
  const footerHtml = `
    <section class="branded-footer avoid-break">
      <div class="branded-footer-contact">
        ${data.brand?.rep_photo_url ? `<img src="${data.brand.rep_photo_url}" alt="${data.brand?.contact_line1 || ''}" class="branded-footer-photo" />` : ''}
        <div class="branded-footer-info">
          ${data.brand?.contact_line1 ? `<div class="branded-footer-name">${data.brand.contact_line1}</div>` : ''}
          ${data.brand?.contact_line2 ? `<div class="branded-footer-details">${data.brand.contact_line2}</div>` : ''}
          ${data.brand?.website_url ? `<div class="branded-footer-website">${data.brand.website_url}</div>` : ''}
        </div>
      </div>
      <div class="branded-footer-logo">
        ${data.brand?.logo_url
          ? `<img src="${data.brand.logo_url}" alt="${brandName}" class="logo-img" />`
          : `<div style="font-size: 14px; font-weight: 600; color: var(--pct-blue);">${brandName}</div>`
        }
      </div>
    </section>
    <footer class="footer">
      Report generated by ${brandName} • Data source: MLS • ${reportDate}
    </footer>
  `;

  // Build row HTML helper (Inventory)
  // Note: Field mapping from PropertyDataExtractor:
  // - street_address (not address)
  // - bedrooms (not beds)
  // - bathrooms (not baths)
  const buildRow = (listing: any) => `
    <tr>
      <td>${listing.city || r.city || "—"}</td>
      <td>${listing.street_address || "—"}</td>
      <td class="t-right">${formatCurrency(listing.list_price)}</td>
      <td class="t-right">${formatNumber(listing.bedrooms)}</td>
      <td class="t-right">${formatDecimal(listing.bathrooms, 1)}</td>
      <td class="t-right">${formatNumber(listing.sqft)}</td>
      <td class="t-right">${formatNumber(listing.days_on_market)}</td>
      <td class="t-right">${listing.status || "Active"}</td>
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
      // Full header for first page
      headerHtml = `
        <header class="header avoid-break">
          <div class="brand">
            <div class="title-block">
              <h1>Listing Inventory — ${marketName}</h1>
              <div class="sub">Period: ${periodLabel} • Source: Live MLS Data • Report Date: ${reportDate}</div>
            </div>
          </div>
          <div class="badge">${brandBadge}</div>
        </header>
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
      headerHtml = `
        <div class="header-continuation">
          <div class="title">Listing Inventory — ${marketName} (continued)</div>
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
              ${pageNum === 1 ? '<h3>Active Listings — Sorted by Days on Market</h3>' : ''}
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

  // Footer HTML (reused on each page)
  const footerHtml = `
    <section class="branded-footer avoid-break">
      <div class="branded-footer-contact">
        ${data.brand?.rep_photo_url ? `<img src="${data.brand.rep_photo_url}" alt="${data.brand?.contact_line1 || ''}" class="branded-footer-photo" />` : ''}
        <div class="branded-footer-info">
          ${data.brand?.contact_line1 ? `<div class="branded-footer-name">${data.brand.contact_line1}</div>` : ''}
          ${data.brand?.contact_line2 ? `<div class="branded-footer-details">${data.brand.contact_line2}</div>` : ''}
          ${data.brand?.website_url ? `<div class="branded-footer-website">${data.brand.website_url}</div>` : ''}
        </div>
      </div>
      <div class="branded-footer-logo">
        ${data.brand?.logo_url
          ? `<img src="${data.brand.logo_url}" alt="${brandName}" class="logo-img" />`
          : `<div style="font-size: 14px; font-weight: 600; color: var(--pct-blue);">${brandName}</div>`
        }
      </div>
    </section>
    <footer class="footer">
      Report generated by ${brandName} • Data source: MLS • ${reportDate}
    </footer>
  `;

  // Build row HTML helper (Closed)
  // Note: Field mapping from PropertyDataExtractor:
  // - street_address (not address)
  // - bedrooms (not beds)
  // - bathrooms (not baths)
  const buildRow = (listing: any) => `
    <tr>
      <td>${listing.city || r.city || "—"}</td>
      <td>${listing.street_address || "—"}</td>
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
      // Full header for first page
      headerHtml = `
        <header class="header avoid-break">
          <div class="brand">
            <div class="title-block">
              <h1>Closed Listings — ${marketName}</h1>
              <div class="sub">Period: ${periodLabel} • Source: Live MLS Data • Report Date: ${reportDate}</div>
            </div>
          </div>
          <div class="badge">${brandBadge}</div>
        </header>
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
          <div class="title">Closed Listings — ${marketName} (continued)</div>
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
              ${pageNum === 1 ? '<h3>Closed Listings — Sorted by Close Date</h3>' : ''}
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

  // Footer HTML (reused on each page)
  const footerHtml = `
    <section class="branded-footer avoid-break">
      <div class="branded-footer-contact">
        ${data.brand?.rep_photo_url ? `<img src="${data.brand.rep_photo_url}" alt="${data.brand?.contact_line1 || ''}" class="branded-footer-photo" />` : ''}
        <div class="branded-footer-info">
          ${data.brand?.contact_line1 ? `<div class="branded-footer-name">${data.brand.contact_line1}</div>` : ''}
          ${data.brand?.contact_line2 ? `<div class="branded-footer-details">${data.brand.contact_line2}</div>` : ''}
          ${data.brand?.website_url ? `<div class="branded-footer-website">${data.brand.website_url}</div>` : ''}
        </div>
      </div>
      <div class="branded-footer-logo">
        ${data.brand?.logo_url
          ? `<img src="${data.brand.logo_url}" alt="${brandName}" class="logo-img" />`
          : `<div style="font-size: 14px; font-weight: 600; color: var(--pct-blue);">${brandName}</div>`
        }
      </div>
    </section>
    <footer class="footer">
      Report generated by ${brandName} • Data source: MLS • ${reportDate}
    </footer>
  `;

  // Build card HTML helper
  // Note: onerror handler provides fallback if MLS photo URL fails to load (common in PDF rendering)
  const fallbackImg = "https://via.placeholder.com/400x300/e5e7eb/9ca3af?text=No+Image";
  const buildCard = (listing: any) => {
    const photoUrl = listing.hero_photo_url || fallbackImg;
    return `
      <div class="property-card avoid-break">
        <img src="${photoUrl}" alt="${listing.street_address || 'Property'}" class="photo" onerror="this.onerror=null; this.src='${fallbackImg}';" />
        <div class="info">
          <div class="address">${listing.street_address || "Address not available"}</div>
          <div class="city">${listing.city || r.city || ""}, ${listing.zip_code || ""}</div>
          <div class="price">${formatCurrency(listing.list_price)}</div>
          <div class="details">
            <div class="detail">🛏 ${formatNumber(listing.bedrooms)} bd</div>
            <div class="detail">🛁 ${formatDecimal(listing.bathrooms, 1)} ba</div>
            <div class="detail">📐 ${formatNumber(listing.sqft)} sqft</div>
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
    const cardsHtml = pageListings.map(buildCard).join('');

    let headerHtml: string;
    if (pageNum === 1) {
      // Full header for first page
      headerHtml = `
        <header class="header avoid-break">
          <div class="brand">
            <div class="title-block">
              <h1>New Listings Gallery — ${marketName}</h1>
              <div class="sub">Period: ${periodLabel} • Source: Live MLS Data • Report Date: ${reportDate}</div>
            </div>
          </div>
          <div class="badge">${brandBadge}</div>
        </header>
        <section class="ribbon avoid-break">
          <div class="count">${formatNumber(r.total_listings || listings.length)}</div>
          <div class="label">NEW LISTINGS — LAST ${lookback} DAYS</div>
        </section>
      `;
    } else {
      // Condensed header for continuation pages
      headerHtml = `
        <div class="header-continuation">
          <div class="title">New Listings Gallery — ${marketName} (continued)</div>
          <div class="page-info">Page ${pageNum} of ${totalPages}</div>
        </div>
      `;
    }

    const pageHtml = `
      <div class="page">
        <div class="page-content">
          ${headerHtml}
          <section class="gallery-grid">
            ${cardsHtml}
          </section>
        </div>
        ${footerHtml}
      </div>
    `;

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

