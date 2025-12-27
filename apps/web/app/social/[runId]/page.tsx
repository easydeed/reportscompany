import fs from 'fs/promises';
import path from 'path';
import {
  buildSocialMarketSnapshotHtml,
  buildSocialNewListingsHtml,
  buildSocialClosedHtml,
  buildSocialInventoryHtml,
  buildSocialGalleryHtml,
  buildSocialPriceBandsHtml
} from '@/lib/social-templates';

type Props = { params: Promise<{ runId: string }> };

async function fetchData(runId: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE;

  if (!base) {
    console.error('[Social Page] NEXT_PUBLIC_API_BASE not set');
    return null;
  }

  const url = `${base}/v1/reports/${runId}/data`;
  console.log(`[Social Page] Fetching report data from: ${url}`);

  try {
    const res = await fetch(url, {
      cache: "no-store",
      headers: {
        'Accept': 'application/json',
      }
    });

    if (!res.ok) {
      console.error(`[Social Page] API error: ${res.status} ${res.statusText}`);
      return null;
    }

    const data = await res.json();
    console.log(`[Social Page] Successfully fetched data for: ${data.city || 'unknown'}`);
    return data;
  } catch (error) {
    console.error(`[Social Page] Failed to fetch report data:`, error);
    return null;
  }
}

async function loadTemplate(templateName: string): Promise<string> {
  const templatePath = path.join(process.cwd(), 'templates', 'social', templateName);
  try {
    const template = await fs.readFile(templatePath, 'utf-8');
    console.log(`[Social Page] Loaded template: ${templateName}`);
    return template;
  } catch (error) {
    console.error(`[Social Page] Failed to load template ${templateName}:`, error);
    throw new Error(`Template not found: ${templateName}`);
  }
}

// Map report type to display name
const REPORT_TITLES: Record<string, string> = {
  market_snapshot: "Market Snapshot",
  new_listings: "New Listings",
  closed: "Closed Sales",
  inventory: "Inventory Report",
  open_houses: "Open Houses",
  price_bands: "Price Bands",
  new_listings_gallery: "New Listings Gallery",
  featured_listings: "Featured Listings"
};

export default async function SocialReport({ params }: Props) {
  const { runId } = await params;
  const data = await fetchData(runId);

  if (!data) {
    return (
      <html lang="en">
        <head>
          <title>Report Not Found</title>
          <style>{`
            body {
              width: 1080px;
              height: 1920px;
              margin: 0;
              display: flex;
              align-items: center;
              justify-content: center;
              background: #f8fafc;
              font-family: system-ui, sans-serif;
            }
            .error {
              text-align: center;
              padding: 60px;
            }
            h1 { font-size: 48px; color: #0f172a; margin-bottom: 20px; }
            p { font-size: 24px; color: #64748b; }
          `}</style>
        </head>
        <body>
          <div className="error">
            <h1>Report Not Found</h1>
            <p>Report ID: {runId}</p>
          </div>
        </body>
      </html>
    );
  }

  const reportType = data.report_type || "market_snapshot";
  const reportTitle = REPORT_TITLES[reportType] || "Market Report";

  // Map report types to social templates
  const templateMap: Record<string, { filename: string; builder: (t: string, d: any) => string }> = {
    "market_snapshot": { filename: 'social-market-snapshot.html', builder: buildSocialMarketSnapshotHtml },
    "new_listings": { filename: 'social-new-listings.html', builder: buildSocialNewListingsHtml },
    "closed": { filename: 'social-closed.html', builder: buildSocialClosedHtml },
    "inventory": { filename: 'social-inventory.html', builder: buildSocialInventoryHtml },
    "open_houses": { filename: 'social-inventory.html', builder: buildSocialInventoryHtml },
    "price_bands": { filename: 'social-price-bands.html', builder: buildSocialPriceBandsHtml },
    "new_listings_gallery": { filename: 'social-gallery.html', builder: buildSocialGalleryHtml },
    "featured_listings": { filename: 'social-gallery.html', builder: buildSocialGalleryHtml },
  };

  const templateConfig = templateMap[reportType];

  if (templateConfig) {
    try {
      const template = await loadTemplate(templateConfig.filename);
      const html = templateConfig.builder(template, data);

      // The template already includes full HTML structure, return as-is
      // Note: dangerouslySetInnerHTML is safe here because:
      // 1. Template files are static and controlled by us
      // 2. All dynamic data is XSS-sanitized in the builder functions
      return (
        <html lang="en" suppressHydrationWarning>
          <head>
            <meta charSet="utf-8" />
            <meta name="viewport" content="width=1080" />
            <title>{reportTitle} - {data.city || 'Market'} | Social</title>
          </head>
          <body 
            dangerouslySetInnerHTML={{ __html: html }} 
            suppressHydrationWarning
            style={{ margin: 0, padding: 0 }}
          />
        </html>
      );
    } catch (error) {
      console.error(`[Social Page] Template error for ${reportType}:`, error);
    }
  }

  // Fallback - shouldn't normally reach here
  return (
    <html lang="en">
      <head>
        <title>Social Preview - {data.city}</title>
        <style>{`
          body {
            width: 1080px;
            height: 1920px;
            margin: 0;
            background: linear-gradient(135deg, #7C3AED 0%, #F26B2B 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: system-ui, sans-serif;
          }
          .content {
            text-align: center;
            color: white;
            padding: 60px;
          }
          h1 { font-size: 64px; margin-bottom: 20px; }
          p { font-size: 32px; opacity: 0.9; }
        `}</style>
      </head>
      <body>
        <div className="content">
          <h1>{reportTitle}</h1>
          <p>{data.city || "Market Report"}</p>
        </div>
      </body>
    </html>
  );
}
