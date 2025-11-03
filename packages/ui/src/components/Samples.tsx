export default function Samples() {
  const types = [
    { name: "Market Snapshot", available: true },
    { name: "New Listings", available: true },
    { name: "Closings", available: true },
    { name: "Inventory by ZIP", available: true },
    { name: "Open Houses", available: true },
    { name: "Price Bands", available: true },
    { name: "Farm Polygon", available: false },
    { name: "Analytics", available: false },
  ];
  return (
    <section id="samples" className="mx-auto max-w-6xl px-6 py-12">
      <h2 className="mb-6 text-3xl font-bold tracking-tight">Report Templates</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {types.map((t) => (
          <div key={t.name} className={`rounded-lg border bg-white p-4 ${t.available ? "hover:shadow-sm cursor-pointer" : "opacity-60"}`}>
            <div className="aspect-[8.5/11] w-full rounded-md border bg-gradient-to-br from-slate-50 to-slate-100" />
            <div className="mt-2 flex items-center justify-between">
              <span className="text-sm font-medium">{t.name}</span>
              {t.available && <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">Available</span>}
              {!t.available && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">Coming Soon</span>}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}






