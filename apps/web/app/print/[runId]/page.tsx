type Props = { params: { runId: string } };

async function fetchData(runId: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE!;
  const acc  = process.env.NEXT_PUBLIC_DEMO_ACCOUNT_ID!;
  const res = await fetch(`${base}/v1/reports/${runId}/data`, {
    headers: { "X-Demo-Account": acc },
    cache: "no-store"
  });
  if (!res.ok) return null;
  return res.json();
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
        <body>
          <h1>Report Not Found</h1>
          <p>Run ID: {runId}</p>
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



