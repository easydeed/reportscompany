export default function HowItWorks() {
  const steps = [
    ["Choose area", "ZIPs, cities, or polygons."],
    ["Pick report type", "Eight polished templates."],
    ["Brand once", "Logo, colors, agent details."],
    ["Share instantly", "PDF, email, or link."],
  ];
  return (
    <section id="how" className="mx-auto max-w-6xl px-6 py-12">
      <ol className="grid gap-6 md:grid-cols-4">
        {steps.map(([t, d], i) => (
          <li key={i} className="rounded-lg border bg-white p-5">
            <div className="text-xs uppercase text-slate-500">Step {i + 1}</div>
            <div className="mt-1 font-medium">{t}</div>
            <p className="mt-2 text-sm text-slate-600">{d}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}











