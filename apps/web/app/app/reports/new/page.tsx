"use client";

import AppLayout from "../../../app-layout";
import { API_BASE, DEMO_ACC } from "@/lib/api";
import { useState } from "react";

export default function NewReportPage() {
  const [cities, setCities] = useState("Los Angeles");
  const [type, setType] = useState("market_snapshot");
  const [lookback, setLookback] = useState(30);
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [links, setLinks] = useState<{html_url?: string; json_url?: string}>({});

  async function create() {
    setRunId(null); setStatus("pending"); setLinks({});
    const res = await fetch(`${API_BASE}/v1/reports`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Demo-Account": DEMO_ACC },
      body: JSON.stringify({ report_type: type, cities: cities.split(",").map(s=>s.trim()), lookback_days: lookback }),
    });
    const json = await res.json();
    const id = json.report_id;
    setRunId(id);
    // poll
    let tries = 0;
    const poll = async () => {
      tries++;
      const r = await fetch(`${API_BASE}/v1/reports/${id}`, { headers: { "X-Demo-Account": DEMO_ACC }});
      const j = await r.json();
      setStatus(j.status);
      if (j.status === "completed" || tries > 60) {
        setLinks({ html_url: j.html_url, json_url: j.json_url });
      } else {
        setTimeout(poll, 800);
      }
    };
    poll();
  }

  return (
    <AppLayout>
      <h1 className="text-2xl font-semibold">New Report</h1>
      <div className="mt-6 grid gap-4 max-w-xl">
        <label className="block">
          <span className="text-sm text-slate-600">Report Type</span>
          <select value={type} onChange={e=>setType(e.target.value)} className="mt-1 w-full rounded border px-3 py-2">
            <option value="market_snapshot">Market Snapshot</option>
            <option value="inventory_zip">Inventory by ZIP</option>
            <option value="closings">Closings</option>
          </select>
        </label>
        <label className="block">
          <span className="text-sm text-slate-600">Cities (comma-separated)</span>
          <input value={cities} onChange={e=>setCities(e.target.value)} className="mt-1 w-full rounded border px-3 py-2" />
        </label>
        <label className="block">
          <span className="text-sm text-slate-600">Lookback (days)</span>
          <input type="number" value={lookback} onChange={e=>setLookback(parseInt(e.target.value||"0",10))} className="mt-1 w-full rounded border px-3 py-2" />
        </label>
        <button onClick={create} className="mt-2 w-fit rounded bg-blue-600 px-5 py-2 text-white">Generate</button>
        {runId && (
          <div className="mt-4 rounded border bg-white p-4">
            <div className="text-sm">Run ID: <code>{runId}</code></div>
            <div className="mt-1 text-sm">Status: <span className={status==="completed"?"text-green-600":"text-amber-600"}>{status}</span></div>
            <div className="mt-2 flex gap-4">
              {links.html_url && <a className="text-blue-600 underline" href={links.html_url} target="_blank">Open HTML</a>}
              {links.json_url && <a className="text-blue-600 underline" href={links.json_url} target="_blank">Open JSON</a>}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}

