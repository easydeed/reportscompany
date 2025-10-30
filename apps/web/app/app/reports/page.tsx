import AppLayout from "../../app-layout";
import { apiFetch } from "@/lib/api";

export default async function ReportsPage() {
  const data = await apiFetch("/v1/reports");
  const rows = data.reports || [];

  return (
    <AppLayout>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Reports</h1>
        <a href="/app/reports/new" className="rounded-md bg-blue-600 px-4 py-2 text-white">New Report</a>
      </div>
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
                    {r.csv_url && <span className="text-slate-400">CSV</span>}
                    {r.pdf_url && <span className="text-slate-400">PDF</span>}
                  </div>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td className="px-4 py-8 text-center text-slate-500" colSpan={4}>No reports yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </AppLayout>
  );
}

