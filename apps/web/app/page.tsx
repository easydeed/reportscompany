import Link from 'next/link';

const apiBase = process.env.NEXT_PUBLIC_API_BASE!;

async function getHealth() {
  try {
    const r = await fetch(`${apiBase}/health`, { cache: 'no-store' });
    if (!r.ok) return false;
    const j = await r.json();
    return !!j?.ok;
  } catch {
    return false;
  }
}

export default async function Home() {
  const apiOnline = await getHealth();

  return (
    <main className="mx-auto max-w-5xl px-6 py-20">
      <section className="grid gap-8 md:grid-cols-2 md:items-center">
        <div>
          <h1 className="text-4xl/tight font-bold tracking-tight">
            MLS data. <span className="text-blue-600">Beautiful reports</span>. Zero effort.
          </h1>
          <p className="mt-4 text-slate-600">
            Turn live housing data into stunning branded market reports in seconds.
          </p>
          <div className="mt-6 flex gap-3">
            <Link href="/reports" className="rounded-md bg-blue-600 px-5 py-3 text-white font-medium hover:bg-blue-700 transition">
              View Reports
            </Link>
            <Link href="/reports/new" className="rounded-md border px-5 py-3 font-medium hover:bg-slate-50 transition">
              + New Report
            </Link>
          </div>

          <p className="mt-8 text-sm text-slate-500">
            API status:{' '}
            <span className={apiOnline ? 'text-green-600' : 'text-red-600'}>
              {apiOnline ? 'online' : 'offline'}
            </span>
          </p>
        </div>

        <div className="rounded-xl border bg-white/60 p-6 shadow-sm backdrop-blur">
          <div className="aspect-[8.5/11] w-full rounded-lg border bg-white shadow-inner" />
          <p className="mt-3 text-center text-sm text-slate-500">Report preview (samples coming soon)</p>
        </div>
      </section>
    </main>
  );
}
