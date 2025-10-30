export default function Samples() {
  const types = ["Market Snapshot","Inventory by ZIP","Closings","New Listings","Open Houses","Price Bands","Farm Polygon","Analytics"];
  return (
    <section id="samples" className="mx-auto max-w-6xl px-6 py-12">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {types.map((t) => (
          <a key={t} className="block rounded-lg border bg-white p-4 hover:shadow-sm" href="#">
            <div className="aspect-[8.5/11] w-full rounded-md border bg-white" />
            <div className="mt-2 text-sm">{t}</div>
          </a>
        ))}
      </div>
    </section>
  );
}

