import AppLayout from "../../app-layout";
import { apiFetch } from "@/lib/api";

export default async function ReportsPage() {
  let data: any = { reports: [], pagination: { limit: 20, offset: 0, count: 0 } };
  let offline = false;
  try {
    data = await apiFetch("/v1/reports");
  } catch (_) {
    offline = true;
  }
  const rows = data.reports || [];

  return (
    <AppLayout>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Reports</h1>
        <a href="/app/reports/new" className="rounded-md bg-blue-600 px-4 py-2 text-white">New Report</a>
      </div>

      {offline && (
        <div className="mt-4 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
          API temporarily unavailable. Showing cached/empty view. Retry in a moment.
        </div>
      )}

      <div className="mt-6 overflow-hidden rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="px-4 py-2">Created</th>
              <th className="px-4 py-2">Type</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Files</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r: any) => (
              <tr key={r.id} className="border-t">
                <td className="px-4 py-2">{new Date(r.generated_at ?? Date.now()).toLocaleString()}</td>
                <td className="px-4 py-2">{r.report_type}</td>
                <td className="px-4 py-2">{r.status}</td>
                <td className="px-4 py-2">
                  <div className="flex gap-3">
                    {r.html_url && <a className="text-blue-600 underline" href={r.html_url} target="_blank">HTML</a>}
                    {r.json_url && <a className="text-blue-600 underline" href={r.json_url} target="_blank">JSON</a>}
                    {r.pdf_url &&  <a className="text-blue-600 underline" href={r.pdf_url} target="_blank">PDF</a>}
                  </div>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td className="px-4 py-8 text-center text-slate-500" colSpan={4}>
                {offline ? "API offline. Try again shortly." : "No reports yet"}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </AppLayout>
  );
}

