export default function FeatureGrid() {
  const items = [
    { title: "Accurate MLS data", desc: "RESO-friendly, cached aggregates." },
    { title: "Branded for you", desc: "Logo, colors, agent info auto-applied." },
    { title: "Print-perfect PDFs", desc: "8.5×11 Letter with crisp charts." },
  ];
  return (
    <section id="features" className="mx-auto max-w-6xl px-6 py-12">
      <div className="grid gap-6 md:grid-cols-3">
        {items.map((it) => (
          <div key={it.title} className="rounded-lg border bg-white p-5">
            <div className="text-base font-semibold">{it.title}</div>
            <p className="mt-2 text-sm text-slate-600">{it.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

