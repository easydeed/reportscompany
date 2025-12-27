import fs from 'fs/promises';
import path from 'path';
import { NextRequest, NextResponse } from 'next/server';
import {
  buildSocialMarketSnapshotHtml,
  buildSocialNewListingsHtml,
  buildSocialClosedHtml,
  buildSocialInventoryHtml,
  buildSocialGalleryHtml,
  buildSocialPriceBandsHtml
} from '@/lib/social-templates';

/**
 * Social Media Image Route Handler
 * 
 * Serves properly formatted HTML for 1080x1920 social media images.
 * This route returns raw HTML with correct content-type, avoiding
 * the nested HTML issue that occurs with page.tsx.
 * 
 * URL: /api/social/{runId}
 * Response: text/html with full 1080x1920 template
 */

async function fetchReportData(runId: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE;
  
  if (!base) {
    console.error('[Social API] NEXT_PUBLIC_API_BASE not set');
    return null;
  }
  
  const url = `${base}/v1/reports/${runId}/data`;
  
  try {
    const res = await fetch(url, {
      cache: "no-store",
      headers: { 'Accept': 'application/json' }
    });
    
    if (!res.ok) {
      console.error(`[Social API] Error: ${res.status}`);
      return null;
    }
    
    return await res.json();
  } catch (error) {
    console.error(`[Social API] Fetch failed:`, error);
    return null;
  }
}

async function loadTemplate(templateName: string): Promise<string> {
  const templatePath = path.join(process.cwd(), 'templates', 'social', templateName);
  return await fs.readFile(templatePath, 'utf-8');
}

const TEMPLATE_MAP: Record<string, { filename: string; builder: (t: string, d: any) => string }> = {
  "market_snapshot": { filename: 'social-market-snapshot.html', builder: buildSocialMarketSnapshotHtml },
  "new_listings": { filename: 'social-new-listings.html', builder: buildSocialNewListingsHtml },
  "closed": { filename: 'social-closed.html', builder: buildSocialClosedHtml },
  "inventory": { filename: 'social-inventory.html', builder: buildSocialInventoryHtml },
  "open_houses": { filename: 'social-inventory.html', builder: buildSocialInventoryHtml },
  "price_bands": { filename: 'social-price-bands.html', builder: buildSocialPriceBandsHtml },
  "new_listings_gallery": { filename: 'social-gallery.html', builder: buildSocialGalleryHtml },
  "featured_listings": { filename: 'social-gallery.html', builder: buildSocialGalleryHtml },
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ runId: string }> }
) {
  const { runId } = await params;
  
  // Validate UUID format
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(runId)) {
    return new NextResponse('Invalid report ID', { status: 400 });
  }
  
  const data = await fetchReportData(runId);
  
  if (!data) {
    return new NextResponse(
      generateErrorHtml('Report Not Found', `Report ID: ${runId}`),
      { status: 404, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
    );
  }
  
  const reportType = data.report_type || "market_snapshot";
  const templateConfig = TEMPLATE_MAP[reportType];
  
  if (!templateConfig) {
    return new NextResponse(
      generateErrorHtml('Unsupported Report Type', reportType),
      { status: 400, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
    );
  }
  
  try {
    const template = await loadTemplate(templateConfig.filename);
    const html = templateConfig.builder(template, data);
    
    return new NextResponse(html, {
      status: 200,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
      }
    });
  } catch (error) {
    console.error(`[Social API] Template error:`, error);
    return new NextResponse(
      generateErrorHtml('Template Error', 'Failed to generate social image'),
      { status: 500, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
    );
  }
}

function generateErrorHtml(title: string, message: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=1080">
  <title>${title}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body {
      width: 1080px;
      height: 1920px;
      font-family: system-ui, sans-serif;
      background: linear-gradient(135deg, #7C3AED 0%, #F26B2B 100%);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .error {
      text-align: center;
      color: white;
      padding: 60px;
    }
    h1 { font-size: 48px; margin-bottom: 20px; }
    p { font-size: 24px; opacity: 0.9; }
  </style>
</head>
<body>
  <div class="error">
    <h1>${title}</h1>
    <p>${message}</p>
  </div>
</body>
</html>`;
}

