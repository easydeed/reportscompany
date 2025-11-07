export default function CodeTabs() {
  return (
    <section id="developers" className="mx-auto max-w-6xl px-6 py-12">
      <div className="rounded-lg border bg-white p-4">
        <p className="text-sm text-slate-600">API example:</p>
        <pre className="mt-3 overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">{`# Python
import requests
r = requests.post("https://api.example.com/v1/reports", json={
  "report_type": "market_snapshot", "cities": ["Los Angeles"], "lookback_days": 30
}, headers={"Authorization":"Bearer <API_KEY>"})`}</pre>
      </div>
    </section>
  );
}







