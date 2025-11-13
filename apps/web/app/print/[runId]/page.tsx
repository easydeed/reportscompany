type Props = { params: { runId: string } };

async function fetchData(runId: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE;
  
  if (!base) {
    console.error('[Print Page] NEXT_PUBLIC_API_BASE not set');
    return null;
  }
  
  const url = `${base}/v1/reports/${runId}/data`;
  console.log(`[Print Page] Fetching report data from: ${url}`);
  
  try {
    const res = await fetch(url, {
      cache: "no-store",
      headers: {
        'Accept': 'application/json',
      }
    });
    
    console.log(`[Print Page] Response status: ${res.status}`);
    
    if (!res.ok) {
      console.error(`[Print Page] API error: ${res.status} ${res.statusText}`);
      return null;
    }
    
    const data = await res.json();
    console.log(`[Print Page] Successfully fetched data for: ${data.city || 'unknown'}`);
    return data;
  } catch (error) {
    console.error(`[Print Page] Failed to fetch report data:`, error);
    return null;
  }
}

// Map report type to display name
const REPORT_TITLES: Record<string, string> = {
  market_snapshot: "Market Snapshot",
  new_listings: "New Listings",
  closed: "Closed Sales",
  inventory: "Inventory Report",
  open_houses: "Open Houses",
  price_bands: "Price Bands"
};

export default async function PrintReport({ params }: Props) {
  const { runId } = params;
  const data = await fetchData(runId);

  if (!data) {
    return (
      <html lang="en">
        <head>
          <title>Report Not Found</title>
        </head>
        <body style={{
          fontFamily: 'system-ui, sans-serif',
          padding: '40px',
          textAlign: 'center'
        }}>
          <h1>Report Not Found</h1>
          <p>Report ID: <code>{runId}</code></p>
          <p style={{color: '#666', fontSize: '14px'}}>
            The report data could not be loaded. Please check:
          </p>
          <ul style={{textAlign: 'left', maxWidth: '400px', margin: '20px auto', color: '#666', fontSize: '14px'}}>
            <li>Report ID is correct</li>
            <li>Report has been generated</li>
            <li>API connection is working</li>
          </ul>
          <p style={{color: '#999', fontSize: '12px', marginTop: '40px'}}>
            API Base: {process.env.NEXT_PUBLIC_API_BASE || 'Not configured'}
          </p>
        </body>
      </html>
    );
  }

  const reportType = data.report_type || "market_snapshot";
  const reportTitle = REPORT_TITLES[reportType] || "Market Report";

  return (
    <html lang="en">
      <head>
        <title>{reportTitle} - {data.city}</title>
        <style>{`
          @page { size: Letter; margin: 0.5in; }
          body { font-family: ui-sans-serif, system-ui; -webkit-print-color-adjust: exact; }
          h1 { font-size: 22px; margin: 0 0 8px; }
          .subtitle { color: #6b7280; margin: 0 0 16px; }
          .kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 8px; }
          .kpi { border: 1px solid #e5e7eb; padding: 8px; border-radius: 8px; }
          .kpi-label { font-size: 12px; color: #6b7280; }
          .kpi-value { font-size: 18px; font-weight: 600; margin-top: 4px; }
          .listings { margin-top: 24px; }
          .listing { border: 1px solid #e5e7eb; padding: 12px; margin-bottom: 8px; border-radius: 8px; }
          .listing-address { font-weight: 600; margin-bottom: 4px; }
          .listing-details { font-size: 14px; color: #6b7280; }
        `}</style>
      </head>
      <body>
        <h1>{reportTitle} — {data.city ?? "—"}</h1>
        <p className="subtitle">Period: Last {data.lookback_days ?? 0} days</p>

        <div className="kpis">
          <div className="kpi">
            <div className="kpi-label">Active</div>
            <div className="kpi-value">{data.counts?.Active ?? 0}</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Pending</div>
            <div className="kpi-value">{data.counts?.Pending ?? 0}</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Closed</div>
            <div className="kpi-value">{data.counts?.Closed ?? 0}</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Median List Price</div>
            <div className="kpi-value">${data.metrics?.median_list_price?.toLocaleString?.() ?? 0}</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Median Close Price</div>
            <div className="kpi-value">${data.metrics?.median_close_price?.toLocaleString?.() ?? 0}</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Avg DOM</div>
            <div className="kpi-value">{data.metrics?.avg_dom?.toFixed(1) ?? 0} days</div>
          </div>
          <div className="kpi">
            <div className="kpi-label">Months of Inventory</div>
            <div className="kpi-value">{data.metrics?.months_of_inventory?.toFixed(1) ?? 0}</div>
          </div>
        </div>

        {data.listings_sample && data.listings_sample.length > 0 && (
          <div className="listings">
            <h2 style={{fontSize: '18px', marginBottom: '12px'}}>Sample Listings ({data.listings_sample.length})</h2>
            {data.listings_sample.slice(0, 10).map((listing: any, idx: number) => (
              <div key={idx} className="listing">
                <div className="listing-address">{listing.address || "Address unavailable"}</div>
                <div className="listing-details">
                  ${listing.list_price?.toLocaleString() ?? "N/A"} • 
                  {listing.beds ?? "—"} beds • 
                  {listing.baths ?? "—"} baths • 
                  {listing.sqft?.toLocaleString() ?? "—"} sqft • 
                  {listing.status ?? "—"}
                  {listing.days_on_market != null && ` • ${listing.days_on_market} days on market`}
                </div>
              </div>
            ))}
          </div>
        )}
      </body>
    </html>
  );
}



