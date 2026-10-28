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

import { deriveBrandTokens } from "./brand-tokens";

// Default TrendyReports brand colour. The accent is no longer read: Design's
// stories (5th package) dropped it with the gradient it was the far end of.
const DEFAULT_PRIMARY_COLOR = "#4F46E5";

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
  // No brand still gets the tokens: the templates read every one of them.
  brand = brand || {};

  // Sanitize color values - only allow valid hex colors
  const colorRegex = /^#[0-9A-Fa-f]{6}$/;
  const primaryColor = colorRegex.test(brand.primary_color) ? brand.primary_color : DEFAULT_PRIMARY_COLOR;
  // The brand is a FILL and never moves; every text use is a derived ink, the
  // same derivation as the reports (lib/brand-tokens.ts ports themes.py).
  const t = deriveBrandTokens(primaryColor);
  
  // Sanitize text values
  const brandName = escapeHtml(brand.display_name) || "TrendyReports";
  const contactLine1 = escapeHtml(brand.contact_line1) || "";
  const contactLine2 = escapeHtml(brand.contact_line2) || "";
  const websiteUrl = escapeHtml(brand.website_url) || "";
  
  // Sanitize URLs
  const logoUrl = sanitizeUrl(brand.logo_url);
  const footerLogoUrl = sanitizeUrl(brand.footer_logo_url) || logoUrl;
  const repPhotoUrl = sanitizeUrl(brand.rep_photo_url);
  const initials = escapeHtml(
    initialsFrom(String(brand.contact_line1 || brand.display_name || ""))
  );

  // Inject CSS color overrides
  const colorOverride = `
    <style>
      :root {
        --pct-blue: ${t.primary};
        --pct-on: ${t.onPrimary};
        --pct-ink: ${t.primaryInk};
        --pct-tint: ${t.tint};
        --pct-on-dark: ${t.primaryOnDark};
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
  result = result.replaceAll("{{initials}}", initials);

  // Each conditional stops at the next mustache-hash, so a missing logo
  // cannot swallow the rest of the story on its way to a later {{else}}.
  result = applyIf(result, "rep_photo_url", Boolean(repPhotoUrl));
  result = applyIf(result, "contact_line1", Boolean(contactLine1));
  result = applyIf(result, "contact_line2", Boolean(contactLine2));
  result = applyIf(result, "website_url", Boolean(websiteUrl));
  result = applyIf(result, "logo_url", Boolean(logoUrl));
  result = applyIf(result, "footer_logo_url", Boolean(footerLogoUrl));

  return result;
}

function initialsFrom(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function applyIf(html: string, key: string, present: boolean): string {
  const ifElse = new RegExp(
    `\\{\\{#if ${key}\\}\\}((?:(?!\\{\\{#)[\\s\\S])*?)\\{\\{else\\}\\}((?:(?!\\{\\{#)[\\s\\S])*?)\\{\\{\\/if\\}\\}`,
    "g"
  );
  const only = new RegExp(
    `\\{\\{#if ${key}\\}\\}((?:(?!\\{\\{#)[\\s\\S])*?)\\{\\{\\/if\\}\\}`,
    "g"
  );
  html = html.replace(ifElse, present ? "$1" : "$2");
  return html.replace(only, present ? "$1" : "");
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

function present(val: number | null | undefined): val is number {
  return val != null && !isNaN(val);
}

function heroPx(value: string): string {
  return value.length > 6 ? "170" : "210";
}

function heroSub(text: string): string {
  if (!text) return "";
  return `<div style="margin-top:8px;font-size:28px;color:#64748B">${escapeHtml(text)}</div>`;
}

function saleToList(metrics: any): string {
  const raw = metrics.close_to_list_ratio ?? metrics.list_to_sale_ratio ?? metrics.sale_to_list_ratio;
  if (!present(raw)) {
    const close = metrics.median_close_price;
    const list = metrics.median_list_price;
    if (!present(close) || !present(list) || list === 0) return "—";
    return ((close / list) * 100).toFixed(1) + "%";
  }
  const pct = raw < 3 ? raw * 100 : raw;
  return pct.toFixed(1) + "%";
}

function pricePerSqft(metrics: any): string {
  const raw = metrics.avg_ppsf ?? metrics.price_per_sqft ?? metrics.avg_price_per_sqft;
  if (!present(raw) || raw === 0) return "—";
  return formatCurrency(raw);
}

function reportContext(data: any) {
  const r = data.result_json || data;
  const lookback = r.lookback_days || 30;
  return {
    r,
    metrics: r.metrics || {},
    counts: r.counts || {},
    market: escapeHtml(r.city) || "Market",
    city: r.city || "this market",
    period: escapeHtml(r.period_label) || `Last ${lookback} days`,
    date: escapeHtml(r.report_date) || new Date().toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }),
  };
}

function fill(templateHtml: string, pairs: Record<string, string>, brand: any): string {
  let html = templateHtml;
  for (const [key, value] of Object.entries(pairs)) {
    html = html.replaceAll(key, value);
  }
  return injectBrand(html, brand);
}

function statsPairs(
  ctx: ReturnType<typeof reportContext>,
  headline: string,
  heroValue: string,
  heroLabel: string,
  sub: string,
  cells: Array<[string, string]>
): Record<string, string> {
  return {
    "{{market_name}}": ctx.market,
    "{{period_label}}": ctx.period,
    "{{report_date}}": ctx.date,
    "{{headline}}": escapeHtml(headline),
    "{{hero_value}}": heroValue,
    "{{hero_size}}": heroPx(heroValue),
    "{{hero_label}}": escapeHtml(heroLabel),
    "{{hero_sub_html}}": heroSub(sub),
    "<!-- STAT_CELLS -->": statCells(cells),
  };
}

/**
 * The cells under the hero: four as a 2×2, three or fewer in one row.
 *
 * EVERY CELL IS A METRIC THE REPORT COMPUTES. A dash means "missing this
 * time" — the feed had nothing for it on this run — never "this report does
 * not calculate it". The first version shipped five cells that read a dash on
 * every story (under $1M, detached, over 30 days, price cuts, and closed
 * sales' price per square foot): none has a producer in report_builders.py,
 * so the cell could only ever be empty, and a permanent dash reads as broken.
 */
function statCells(cells: Array<[string, string]>): string {
  if (cells.length === 0) return "";
  const cols = cells.length === 4 ? 2 : cells.length;
  const size = cols === 2 ? 88 : 72;
  const items = cells.map(([value, label]) =>
    `<div style="background:#F8FAFC;border:2px solid #ECEAE3;padding:40px 36px"><div style="font-size:${size}px;font-weight:800;letter-spacing:-.03em;line-height:1">${value}</div><div style="margin-top:14px;font-size:25px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:#64748B">${escapeHtml(label)}</div></div>`
  ).join("");
  return `<div style="margin-top:40px;display:grid;grid-template-columns:repeat(${cols},1fr);gap:24px">${items}</div>`;
}

/**
 * Build Social Market Snapshot HTML
 */
export function buildSocialMarketSnapshotHtml(templateHtml: string, data: any): string {
  const ctx = reportContext(data);
  const { metrics, counts } = ctx;
  const closed = counts.Closed ?? 0;
  const active = counts.Active ?? 0;
  const moi = present(metrics.months_of_inventory)
    ? metrics.months_of_inventory
    : closed > 0 ? active / closed : null;
  const price = formatCurrency(metrics.median_close_price || metrics.median_list_price);
  return fill(templateHtml, statsPairs(
    ctx,
    price === "—" ? `Market snapshot for ${ctx.city}.` : `${ctx.city} median sale price is ${price}.`,
    price,
    "Median sale price",
    "",
    [
      [formatNumber(counts.Closed), "Homes sold"],
      [formatNumber(present(metrics.avg_dom) ? Math.round(metrics.avg_dom) : null), "Days to sell"],
      [saleToList(metrics), "Sale to list"],
      [present(moi) ? formatDecimal(moi) : "—", "Months supply"],
    ]
  ), data.brand);
}

/**
 * Build Social New Listings HTML
 */
export function buildSocialNewListingsHtml(templateHtml: string, data: any): string {
  const ctx = reportContext(data);
  const { metrics, counts } = ctx;
  // `counts.Active` IS the new-listings count: build_new_listings_result emits
  // the listings that came to market in the window as Active. The first version
  // read `counts.NewListings`, which only the Snapshot builder emits, so this
  // story's hero number was a dash on every run.
  const n = counts.Active ?? null;
  const count = formatNumber(n);
  return fill(templateHtml, statsPairs(
    ctx,
    count === "—" ? `New listings in ${ctx.city}.` : `${count} new listings in ${ctx.city}.`,
    count,
    "New listings",
    "",
    [
      [formatCurrency(metrics.median_list_price), "Median asking"],
      [pricePerSqft(metrics), "Per sq ft"],
      [formatNumber(present(metrics.avg_dom) ? Math.round(metrics.avg_dom) : null), "Days on market"],
    ]
  ), data.brand);
}

/**
 * Build Social Closed Sales HTML
 */
export function buildSocialClosedHtml(templateHtml: string, data: any): string {
  const ctx = reportContext(data);
  const { metrics, counts } = ctx;
  const count = formatNumber(counts.Closed);
  return fill(templateHtml, statsPairs(
    ctx,
    count === "—" ? `Homes sold in ${ctx.city}.` : `${count} homes sold in ${ctx.city}.`,
    count,
    "Homes sold",
    "",
    [
      [formatCurrency(metrics.median_close_price), "Median sale"],
      [formatNumber(present(metrics.avg_dom) ? Math.round(metrics.avg_dom) : null), "Days to sell"],
      [saleToList(metrics), "Sale to list"],
    ]
  ), data.brand);
}

/**
 * Build Social Inventory HTML
 */
export function buildSocialInventoryHtml(templateHtml: string, data: any): string {
  const ctx = reportContext(data);
  const { metrics, counts, r } = ctx;
  // `metrics.total_active` — everything for sale, the months-of-supply
  // numerator and the Inventory email's hero. NOT `counts.Active`, which is the
  // listings TABLE's population (only those listed inside the window), so
  // "N homes are for sale" over it was a false sentence.
  const active = present(metrics.total_active) ? metrics.total_active : null;
  const closed = counts.Closed ?? 0;
  const lookback = r.lookback_days || 30;
  const moi = present(metrics.months_of_inventory)
    ? metrics.months_of_inventory
    : closed > 0 ? (active ?? 0) / closed * (lookback / 30) : null;
  const count = formatNumber(active);
  const days = present(metrics.median_dom) ? metrics.median_dom : metrics.avg_dom;
  return fill(templateHtml, statsPairs(
    ctx,
    count === "—" ? `Homes for sale in ${ctx.city}.` : `${count} homes are for sale in ${ctx.city}.`,
    count,
    "Active listings",
    "",
    [
      // Not the median asking price: build_inventory_result computes it over
      // the windowed listings, a different set from the hero's.
      [formatNumber(metrics.new_this_month), "New this month"],
      [formatNumber(present(days) ? Math.round(days) : null), "Days on market"],
      [present(moi) ? formatDecimal(moi) : "—", "Months supply"],
    ]
  ), data.brand);
}

/**
 * Build Social Open Houses HTML
 */
export function buildSocialOpenHousesHtml(templateHtml: string, data: any): string {
  const ctx = reportContext(data);
  const listings = ctx.r.listings || ctx.r.listings_sample || [];
  const total = ctx.counts.OpenHouses ?? listings.length;
  const featured = listings[0] || {};
  const when = formatOpenHouse(featured.next_open_house);
  const countLine = listings.length === 0
    ? `Open houses in ${ctx.city}`
    : when
      ? `${when} · 1 of ${formatNumber(total)}`
      : `1 of ${formatNumber(total)}`;
  return fill(templateHtml, photoPairs(ctx, featured, countLine, false), data.brand);
}

/**
 * Build Social New Listings Gallery HTML
 */
export function buildSocialGalleryHtml(templateHtml: string, data: any): string {
  const ctx = reportContext(data);
  const listings = ctx.r.listings || ctx.r.listings_sample || [];
  const total = ctx.r.total_listings ?? listings.length;
  return fill(
    templateHtml,
    photoPairs(ctx, listings[0] || {}, listings.length ? `1 of ${formatNumber(total)} new in ${ctx.city}` : `New listings in ${ctx.city}`, true),
    data.brand
  );
}

/**
 * Build Social Featured Listings HTML
 */
export function buildSocialFeaturedHtml(templateHtml: string, data: any): string {
  const ctx = reportContext(data);
  const listings = ctx.r.listings || ctx.r.listings_sample || [];
  const total = ctx.r.total_listings ?? listings.length;
  return fill(
    templateHtml,
    photoPairs(ctx, listings[0] || {}, listings.length ? `1 of ${formatNumber(total)} in ${ctx.city}` : `Featured in ${ctx.city}`, true),
    data.brand
  );
}

/**
 * Build Social Price Bands HTML
 */
export function buildSocialPriceBandsHtml(templateHtml: string, data: any): string {
  const ctx = reportContext(data);
  const bands = ctx.r.price_bands || [];
  const total = bands.reduce((sum: number, band: any) => sum + (band.count || 0), 0);
  const top = bands.reduce((best: any, band: any) => (
    !best || (band.count || 0) > (best.count || 0) ? band : best
  ), null);
  const share = top && total > 0 ? Math.round(((top.count || 0) / total) * 100) : null;
  const hero = share == null ? "—" : `${share}%`;
  const label = top ? String(top.label || "") : "";
  const pairs = statsPairs(
    ctx,
    share == null ? `Price bands for ${ctx.city}.` : `${share}% of ${ctx.city} listings are ${label}.`,
    hero,
    label ? `of listings are ${label}` : "of listings",
    top && share != null ? `${formatNumber(top.count)} of ${formatNumber(total)} homes` : "",
    []
  );
  let html = templateHtml;
  for (const [key, value] of Object.entries(pairs)) {
    html = html.replaceAll(key, value);
  }
  html = html.replace("<!-- PRICE_BANDS -->", bandRows(bands, total));
  return injectBrand(html, data.brand);
}

function bandRows(bands: any[], total: number): string {
  return bands.slice(0, 3).map((band) => {
    const pct = total > 0 ? ((band.count || 0) / total) * 100 : 0;
    const width = Math.max(2, pct);
    const label = escapeHtml(band.label) || "—";
    const detail = `${formatNumber(band.count)} homes · median ${formatCurrency(band.median_price)}`;
    return `<div><div style="display:flex;justify-content:space-between;align-items:baseline"><span style="font-size:34px;font-weight:700">${label}</span><span style="font-size:28px;color:#64748B">${detail}</span></div><div style="margin-top:12px;height:22px;background:#ECEAE3"><div style="width:${width.toFixed(0)}%;height:22px;background:var(--pct-blue)"></div></div></div>`;
  }).join("");
}

function photoPairs(
  ctx: ReturnType<typeof reportContext>,
  featured: any,
  countLine: string,
  includeDays: boolean
): Record<string, string> {
  const hasListing = Boolean(featured && (featured.street_address || featured.list_price));
  const street = escapeHtml(featured.street_address) || "";
  const city = escapeHtml(featured.city || "") || "";
  const address = [street, city].filter(Boolean).join(", ") || "—";
  const parts: string[] = [];
  if (hasListing && featured.bedrooms != null) parts.push(`${formatNumber(featured.bedrooms)} bd`);
  if (hasListing && featured.bathrooms != null) {
    const baths = Number(featured.bathrooms);
    const bathsLabel = Number.isInteger(baths) ? String(baths) : formatDecimal(baths, 1);
    parts.push(`${bathsLabel} ba`);
  }
  if (hasListing && featured.sqft != null) parts.push(`${formatNumber(featured.sqft)} sq ft`);
  if (includeDays && hasListing && featured.days_on_market != null) {
    parts.push(`${formatNumber(featured.days_on_market)} days`);
  }
  return {
    "{{market_name}}": ctx.market,
    "{{period_label}}": ctx.period,
    "{{report_date}}": ctx.date,
    "{{count_line}}": escapeHtml(countLine),
    "{{list_price}}": hasListing ? formatCurrency(featured.list_price) : "—",
    "{{street_address}}": address,
    "{{specs}}": parts.join(" · ") || "—",
    "{{photo_block}}": photoBlock(sanitizeUrl(featured.hero_photo_url)),
  };
}

function photoBlock(url: string): string {
  if (!url) {
    return `<div style="height:900px;background:#E4E2DA;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#64748B">Listing photo</div>`;
  }
  const safe = url.replace(/['"\\()]/g, "");
  return `<div style="height:900px;background:#E4E2DA center/cover no-repeat;background-image:url('${safe}')"></div>`;
}

function formatOpenHouse(raw: string | null | undefined): string {
  if (!raw) return "";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(raw));
  if (!match) return "";
  const parsed = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}

export const SOCIAL_TEMPLATE_MAP: Record<string, { filename: string; builder: (t: string, d: any) => string }> = {
  market_snapshot: { filename: "social-market-snapshot.html", builder: buildSocialMarketSnapshotHtml },
  new_listings: { filename: "social-new-listings.html", builder: buildSocialNewListingsHtml },
  closed: { filename: "social-closed.html", builder: buildSocialClosedHtml },
  inventory: { filename: "social-inventory.html", builder: buildSocialInventoryHtml },
  open_houses: { filename: "social-open-houses.html", builder: buildSocialOpenHousesHtml },
  price_bands: { filename: "social-price-bands.html", builder: buildSocialPriceBandsHtml },
  new_listings_gallery: { filename: "social-new-listings-gallery.html", builder: buildSocialGalleryHtml },
  featured_listings: { filename: "social-featured-listings.html", builder: buildSocialFeaturedHtml },
};
