export default function Hero() {
  return (
    <section className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-10 px-6 py-16 md:grid-cols-2">
      <div>
        <h1 className="text-4xl/tight font-bold tracking-tight">
          MLS data. <span className="text-blue-600">Beautiful reports</span>. Zero effort.
        </h1>
        <p className="mt-4 text-slate-600">
          Turn live housing data into stunning branded market reports in seconds.
        </p>
        <div className="mt-6 flex gap-3">
          <a href="/signup" className="rounded-md bg-blue-600 px-5 py-3 text-white">Start Free Trial</a>
          <a href="#samples" className="rounded-md border px-5 py-3">View Samples</a>
        </div>
      </div>
      <div className="rounded-xl border bg-white/60 p-6 shadow-sm backdrop-blur">
        <div className="aspect-[8.5/11] w-full rounded-lg border bg-white shadow-inner" />
        <p className="mt-3 text-center text-sm text-slate-500">Report preview</p>
      </div>
    </section>
  );
}











