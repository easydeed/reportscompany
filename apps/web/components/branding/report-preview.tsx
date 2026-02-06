"use client";

import { useState, useMemo } from "react";
import { SAMPLE_REPORT_DATA, REPORT_TYPE_OPTIONS, ReportType } from "@/lib/sample-report-data";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Monitor, Smartphone, Tablet, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface BrandingData {
  brand_display_name: string;
  logo_url: string | null;
  primary_color: string | null;
  accent_color: string | null;
  contact_line1?: string | null;
  contact_line2?: string | null;
  website_url?: string | null;
  rep_photo_url?: string | null;
}

interface ReportPreviewProps {
  branding: BrandingData;
}

/**
 * ReportPreview Component
 * 
 * Shows a live preview of how branding appears on different report types.
 * Uses sample data and client-side HTML generation.
 * 
 * Pass B3.2: Report Preview Component
 */
export function ReportPreview({ branding }: ReportPreviewProps) {
  const [reportType, setReportType] = useState<ReportType>("market_snapshot");
  const [viewMode, setViewMode] = useState<"desktop" | "tablet" | "mobile">("desktop");
  const [key, setKey] = useState(0); // For forcing iframe refresh

  const viewWidths = {
    desktop: "100%",
    tablet: "768px",
    mobile: "375px",
  };

  // Generate preview HTML
  const previewHtml = useMemo(() => {
    const data = SAMPLE_REPORT_DATA[reportType];
    return generatePreviewHtml(reportType, data, branding);
  }, [reportType, branding, key]);

  const handleRefresh = () => {
    setKey((k) => k + 1);
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Select value={reportType} onValueChange={(v) => setReportType(v as ReportType)}>
            <SelectTrigger className="w-56">
              <SelectValue placeholder="Select report type" />
            </SelectTrigger>
            <SelectContent>
              {REPORT_TYPE_OPTIONS.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  <div className="flex flex-col">
                    <span>{type.label}</span>
                    <span className="text-xs text-muted-foreground">{type.description}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button variant="outline" size="icon" onClick={handleRefresh} title="Refresh preview">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>

        <div className="flex items-center gap-1 border rounded-lg p-1 bg-muted/50">
          <button
            onClick={() => setViewMode("desktop")}
            className={cn(
              "p-2 rounded transition-colors",
              viewMode === "desktop"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
            title="Desktop view"
          >
            <Monitor className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode("tablet")}
            className={cn(
              "p-2 rounded transition-colors",
              viewMode === "tablet"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
            title="Tablet view"
          >
            <Tablet className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode("mobile")}
            className={cn(
              "p-2 rounded transition-colors",
              viewMode === "mobile"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
            title="Mobile view"
          >
            <Smartphone className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Preview Frame */}
      <div
        className="border rounded-lg bg-muted/30 p-4 overflow-auto"
        style={{ height: "600px" }}
      >
        <div
          className={cn(
            "bg-white shadow-lg mx-auto transition-all duration-300 rounded-lg overflow-hidden",
            viewMode !== "desktop" && "border"
          )}
          style={{ width: viewWidths[viewMode], minHeight: "100%" }}
        >
          <iframe
            key={key}
            srcDoc={previewHtml}
            className="w-full border-0"
            style={{ minHeight: "800px", height: "100%" }}
            title="Report Preview"
          />
        </div>
      </div>

      {/* Info */}
      <p className="text-xs text-muted-foreground text-center">
        Preview uses sample Beverly Hills data. Actual reports will show your market data.
      </p>
    </div>
  );
}

/**
 * Generate preview HTML with branding applied
 */
function generatePreviewHtml(
  reportType: ReportType,
  data: any,
  branding: BrandingData
): string {
  const primaryColor = branding.primary_color || "#4F46E5";
  const accentColor = branding.accent_color || "#F26B2B";
  const brandName = branding.brand_display_name || "Your Brand";
  const logoUrl = branding.logo_url || "";

  // Format currency
  const formatCurrency = (val: number) => {
    if (!val) return "$0";
    return "$" + val.toLocaleString();
  };

  // Format number
  const formatNumber = (val: number) => {
    if (!val) return "0";
    return val.toLocaleString();
  };

  // Get metrics from data
  const metrics = data.metrics || {};
  const counts = data.counts || {};
  const city = data.city || "Market";
  const periodLabel = data.period_label || "Last 30 days";
  const reportDate = data.report_date || new Date().toLocaleDateString();

  // Generate content based on report type
  let contentHtml = "";

  if (reportType === "market_snapshot") {
    contentHtml = `
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-label">Median Sale Price</div>
          <div class="metric-value">${formatCurrency(metrics.median_close_price || metrics.median_list_price)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Closed Sales</div>
          <div class="metric-value">${formatNumber(counts.Closed)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Avg. Days on Market</div>
          <div class="metric-value">${metrics.avg_dom || 0}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Active Listings</div>
          <div class="metric-value">${formatNumber(counts.Active)}</div>
        </div>
      </div>
      
      <div class="section">
        <h3>Market Activity</h3>
        <div class="indicator-grid">
          <div class="indicator">
            <div class="indicator-label">New Listings</div>
            <div class="indicator-value">${formatNumber(counts.Active)}</div>
            <div class="indicator-bar" style="width: ${Math.min(100, (counts.Active / 150) * 100)}%"></div>
          </div>
          <div class="indicator">
            <div class="indicator-label">Pending Sales</div>
            <div class="indicator-value">${formatNumber(counts.Pending)}</div>
            <div class="indicator-bar" style="width: ${Math.min(100, (counts.Pending / 50) * 100)}%"></div>
          </div>
        </div>
      </div>
    `;
  } else if (reportType === "new_listings" || reportType === "inventory" || reportType === "closed") {
    const listings = data.listings_sample || [];
    const listingsHtml = listings.slice(0, 5).map((l: any) => `
      <tr>
        <td>${l.address || "—"}</td>
        <td class="text-right">${formatCurrency(l.list_price)}</td>
        <td class="text-right">${l.beds || 0}</td>
        <td class="text-right">${l.baths || 0}</td>
        <td class="text-right">${formatNumber(l.sqft)}</td>
        <td class="text-right">${l.days_on_market || 0}</td>
      </tr>
    `).join("");

    contentHtml = `
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-label">Total ${reportType === "closed" ? "Closed" : "Listings"}</div>
          <div class="metric-value">${formatNumber(counts.Active || counts.Closed)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Median Price</div>
          <div class="metric-value">${formatCurrency(metrics.median_list_price || metrics.median_close_price)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Avg. DOM</div>
          <div class="metric-value">${metrics.avg_dom || 0}</div>
        </div>
      </div>
      
      <div class="section">
        <h3>Property Details</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>Address</th>
              <th class="text-right">Price</th>
              <th class="text-right">Beds</th>
              <th class="text-right">Baths</th>
              <th class="text-right">SqFt</th>
              <th class="text-right">DOM</th>
            </tr>
          </thead>
          <tbody>
            ${listingsHtml || "<tr><td colspan='6' class='text-center'>Sample listings will appear here</td></tr>"}
          </tbody>
        </table>
      </div>
    `;
  } else if (reportType === "new_listings_gallery" || reportType === "featured_listings") {
    const listings = data.listings || [];
    const cardsHtml = listings.slice(0, 6).map((l: any) => `
      <div class="property-card">
        <img src="${l.hero_photo_url || "https://via.placeholder.com/400x300/e5e7eb/9ca3af?text=Property"}" alt="${l.street_address}" class="property-image" />
        <div class="property-info">
          <div class="property-address">${l.street_address || "Address"}</div>
          <div class="property-location">${l.city || city}, ${l.zip_code || ""}</div>
          <div class="property-price">${formatCurrency(l.list_price)}</div>
          <div class="property-details">
            <span>${l.bedrooms || 0} bd</span>
            <span>${l.bathrooms || 0} ba</span>
            <span>${formatNumber(l.sqft)} sqft</span>
          </div>
        </div>
      </div>
    `).join("");

    contentHtml = `
      <div class="gallery-grid">
        ${cardsHtml}
      </div>
    `;
  } else if (reportType === "price_bands") {
    const bands = data.price_bands || [];
    const totalListings = bands.reduce((sum: number, b: any) => sum + (b.count || 0), 0);
    
    const bandsHtml = bands.map((b: any) => {
      const percentage = totalListings > 0 ? ((b.count || 0) / totalListings) * 100 : 0;
      return `
        <div class="price-band">
          <div class="band-header">
            <span class="band-label">${b.label}</span>
            <span class="band-count">${b.count} listings (${percentage.toFixed(1)}%)</span>
          </div>
          <div class="band-bar-container">
            <div class="band-bar" style="width: ${percentage}%"></div>
          </div>
          <div class="band-metrics">
            <span>Median: ${formatCurrency(b.median_price)}</span>
            <span>Avg DOM: ${b.avg_dom}</span>
          </div>
        </div>
      `;
    }).join("");

    contentHtml = `
      <div class="section">
        <h3>Price Distribution</h3>
        <div class="price-bands">
          ${bandsHtml}
        </div>
      </div>
    `;
  } else {
    contentHtml = `
      <div class="section">
        <p class="text-center">Preview for ${reportType.replace(/_/g, " ")} report</p>
      </div>
    `;
  }

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
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
        
        .header {
          background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
          color: white;
          padding: 24px 32px;
        }
        
        .header-content {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
        }
        
        .header-left {
          display: flex;
          align-items: center;
          gap: 16px;
        }
        
        .logo {
          height: 48px;
          width: auto;
          max-width: 160px;
          object-fit: contain;
          filter: brightness(0) invert(1);
        }
        
        .logo-placeholder {
          width: 48px;
          height: 48px;
          background: rgba(255,255,255,0.2);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          font-weight: bold;
        }
        
        .header-title {
          font-size: 24px;
          font-weight: 700;
        }
        
        .header-subtitle {
          font-size: 14px;
          opacity: 0.9;
        }
        
        .header-right {
          text-align: right;
          font-size: 13px;
        }
        
        .header-badge {
          opacity: 0.9;
        }
        
        .content {
          padding: 32px;
        }
        
        .intro {
          color: #6b7280;
          margin-bottom: 24px;
          font-size: 14px;
        }
        
        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
          gap: 16px;
          margin-bottom: 32px;
        }
        
        .metric-card {
          background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
          color: white;
          padding: 20px;
          border-radius: 12px;
        }
        
        .metric-label {
          font-size: 12px;
          opacity: 0.9;
          margin-bottom: 4px;
        }
        
        .metric-value {
          font-size: 24px;
          font-weight: 700;
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
        
        .indicator-grid {
          display: grid;
          gap: 16px;
        }
        
        .indicator {
          background: #f9fafb;
          padding: 16px;
          border-radius: 8px;
          border: 1px solid #e5e7eb;
        }
        
        .indicator-label {
          font-size: 13px;
          color: #6b7280;
        }
        
        .indicator-value {
          font-size: 28px;
          font-weight: 700;
          color: #1f2937;
        }
        
        .indicator-bar {
          height: 6px;
          background: var(--accent);
          border-radius: 3px;
          margin-top: 8px;
        }
        
        .data-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
        }
        
        .data-table th,
        .data-table td {
          padding: 12px 8px;
          border-bottom: 1px solid #e5e7eb;
        }
        
        .data-table th {
          text-align: left;
          font-weight: 600;
          color: #6b7280;
          font-size: 11px;
          text-transform: uppercase;
        }
        
        .text-right {
          text-align: right;
        }
        
        .text-center {
          text-align: center;
        }
        
        .gallery-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
        }
        
        .property-card {
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          overflow: hidden;
        }
        
        .property-image {
          width: 100%;
          height: 150px;
          object-fit: cover;
        }
        
        .property-info {
          padding: 16px;
        }
        
        .property-address {
          font-weight: 600;
          font-size: 14px;
        }
        
        .property-location {
          font-size: 12px;
          color: #6b7280;
        }
        
        .property-price {
          font-size: 18px;
          font-weight: 700;
          color: var(--primary);
          margin: 8px 0;
        }
        
        .property-details {
          display: flex;
          gap: 12px;
          font-size: 12px;
          color: #6b7280;
        }
        
        .price-bands {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        
        .price-band {
          background: #f9fafb;
          padding: 16px;
          border-radius: 8px;
        }
        
        .band-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
        }
        
        .band-label {
          font-weight: 600;
        }
        
        .band-count {
          font-size: 13px;
          color: #6b7280;
        }
        
        .band-bar-container {
          height: 8px;
          background: #e5e7eb;
          border-radius: 4px;
          overflow: hidden;
        }
        
        .band-bar {
          height: 100%;
          background: var(--accent);
          border-radius: 4px;
        }
        
        .band-metrics {
          display: flex;
          gap: 16px;
          margin-top: 8px;
          font-size: 12px;
          color: #6b7280;
        }
        
        /* Branded Footer (above gray footer) */
        .branded-footer {
          margin: 24px 32px 0;
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
        
        /* Gray Footer (bottom) */
        .footer {
          margin-top: 16px;
          padding: 12px 32px;
          border-top: 1px solid #e5e7eb;
          text-align: center;
          font-size: 10px;
          color: #9ca3af;
        }
      </style>
    </head>
    <body>
      <div class="header">
        <div class="header-content">
          <div class="header-left">
            ${logoUrl 
              ? `<img src="${logoUrl}" alt="${brandName}" class="logo" />`
              : `<div class="logo-placeholder">${brandName[0]}</div>`
            }
            <div>
              <div class="header-title">${getReportTitle(reportType)} — ${city}</div>
              <div class="header-subtitle">${periodLabel} • ${reportDate}</div>
            </div>
          </div>
          <div class="header-right">
            <div class="header-badge">${brandName} Insights</div>
          </div>
        </div>
      </div>
      
      <div class="content">
        <p class="intro">
          This ${getReportTitle(reportType).toLowerCase()} provides key market indicators for <strong>${city}</strong>
          based on the most recent <strong>${data.lookback_days || 30} days</strong> of MLS activity.
        </p>
        
        ${contentHtml}
      </div>
      
      <!-- Branded Footer -->
      <div class="branded-footer">
        <div class="branded-footer-contact">
          ${branding.rep_photo_url 
            ? `<img src="${branding.rep_photo_url}" alt="Representative" class="branded-footer-photo" />`
            : ""
          }
          <div class="branded-footer-info">
            ${branding.contact_line1 ? `<div class="branded-footer-name">${branding.contact_line1}</div>` : ""}
            ${branding.contact_line2 ? `<div class="branded-footer-details">${branding.contact_line2}</div>` : ""}
            ${branding.website_url ? `<div class="branded-footer-website">${branding.website_url.replace("https://", "").replace("http://", "")}</div>` : ""}
          </div>
        </div>
        <div class="branded-footer-logo">
          ${logoUrl 
            ? `<img src="${logoUrl}" alt="${brandName}" />`
            : `<div class="branded-footer-logo-text">${brandName}</div>`
          }
        </div>
      </div>
      
      <!-- Gray Footer -->
      <div class="footer">
        Report generated by ${brandName} • Data source: MLS • ${reportDate}
      </div>
    </body>
    </html>
  `;
}

function getReportTitle(reportType: ReportType): string {
  const titles: Record<ReportType, string> = {
    market_snapshot: "Market Snapshot",
    new_listings: "New Listings",
    new_listings_gallery: "New Listings Gallery",
    featured_listings: "Featured Listings",
    inventory: "Inventory Report",
    closed: "Closed Sales",
    price_bands: "Price Bands",
    open_houses: "Open Houses",
  };
  return titles[reportType] || "Market Report";
}

