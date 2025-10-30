export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <a href="/" className="font-semibold">Market Reports</a>
          <nav className="flex gap-4 text-sm text-slate-600">
            <a href="/app">Overview</a>
            <a href="/app/reports">Reports</a>
            <a href="/app/reports/new" className="text-blue-600">New Report</a>
            <a href="/app/branding">Branding</a>
            <a href="/app/billing">Billing</a>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}

