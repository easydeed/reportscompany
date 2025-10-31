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

export default async function PrintReport({ params }: Props) {
  const { runId } = params;
  const data = await fetchData(runId);

  return (
    <html lang="en">
      <head>
        <title>Report {runId}</title>
        <style>{`
          @page { size: Letter; margin: 0.5in; }
          body { font-family: ui-sans-serif, system-ui; -webkit-print-color-adjust: exact; }
          h1 { font-size: 22px; margin: 0 0 8px; }
          .kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 8px; }
          .kpi { border: 1px solid #e5e7eb; padding: 8px; border-radius: 8px; }
        `}</style>
      </head>
      <body>
        <h1>Market Snapshot — {data?.city ?? "—"}</h1>
        <p>Period: Last {data?.lookback_days ?? 0} days</p>

        <div className="kpis">
          <div className="kpi">Active: {data?.counts?.Active ?? 0}</div>
          <div className="kpi">Pending: {data?.counts?.Pending ?? 0}</div>
          <div className="kpi">Closed: {data?.counts?.Closed ?? 0}</div>
          <div className="kpi">Median Close Price: ${data?.metrics?.median_close_price?.toLocaleString?.() ?? 0}</div>
          <div className="kpi">Avg DOM: {data?.metrics?.avg_dom ?? 0}</div>
          <div className="kpi">MOI: {data?.metrics?.months_of_inventory ?? 0}</div>
        </div>
      </body>
    </html>
  );
}



