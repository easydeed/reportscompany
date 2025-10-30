import AppLayout from "../app-layout";
import { API_BASE, DEMO_ACC } from "@/lib/api";

async function fetchUsage() {
  const res = await fetch(`${API_BASE}/v1/usage`, {
    headers: { "X-Demo-Account": DEMO_ACC },
    cache: "no-store"
  });
  if (!res.ok) { return null; }
  return res.json();
}

export default async function Overview() {
  const data = await fetchUsage();
  const summary = data?.summary ?? { total_reports: 0, billable_reports: 0 };
  const byType = data?.by_type ?? [];
  const timeline = data?.timeline ?? [];
  const limits = data?.limits ?? {};

  return (
    <AppLayout>
      <h1 className="text-2xl font-semibold">Overview</h1>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border bg-white p-4">
          <p className="text-sm text-slate-500">Reports (period)</p>
          <p className="mt-1 text-2xl font-semibold">{summary.total_reports ?? 0}</p>
        </div>
        <div className="rounded-lg border bg-white p-4">
          <p className="text-sm text-slate-500">Billable Reports</p>
          <p className="mt-1 text-2xl font-semibold">{summary.billable_reports ?? 0}</p>
        </div>
        <div className="rounded-lg border bg-white p-4">
          <p className="text-sm text-slate-500">Monthly Limit</p>
          <p className="mt-1 text-2xl font-semibold">{limits.monthly_report_limit ?? "—"}</p>
        </div>
        <div className="rounded-lg border bg-white p-4">
          <p className="text-sm text-slate-500">API Rate (rpm)</p>
          <p className="mt-1 text-2xl font-semibold">{limits.api_rate_limit ?? "—"}</p>
        </div>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-white p-4">
          <p className="text-sm text-slate-500">Reports by Type</p>
          <div className="mt-4 space-y-2">
            {byType.length === 0 && <p className="text-sm text-slate-500">No data yet</p>}
            {byType.map((r: any) => (
              <div key={r.report_type} className="flex items-center justify-between">
                <span className="text-sm">{r.report_type}</span>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-40 rounded bg-slate-100">
                    <div className="h-2 rounded bg-blue-600" style={{ width: `${Math.min(100, (r.c / (byType[0]?.c || 1)) * 100)}%` }} />
                  </div>
                  <span className="text-xs text-slate-500">{r.c}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border bg-white p-4">
          <p className="text-sm text-slate-500">Daily Activity</p>
          <div className="mt-4 space-y-1">
            {timeline.length === 0 && <p className="text-sm text-slate-500">No data yet</p>}
            {timeline.map((d: any) => (
              <div key={d.date} className="flex items-center gap-3">
                <div className="w-28 text-xs text-slate-500">{new Date(d.date).toLocaleDateString()}</div>
                <div className="h-2 w-64 rounded bg-slate-100">
                  <div className="h-2 rounded bg-orange-500" style={{ width: `${Math.min(100, d.reports * 10)}%` }} />
                </div>
                <div className="text-xs text-slate-600">{d.reports}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

