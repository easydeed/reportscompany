export default function Navbar() {
  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <a href="/" className="font-semibold">Market Reports</a>
        <nav className="flex gap-4 text-sm text-slate-600">
          <a href="#features">Features</a>
          <a href="#samples">Samples</a>
          <a href="#pricing">Pricing</a>
          <a href="#developers">Developers</a>
          <a href="/partners">Partners</a>
          <a href="/docs">Docs</a>
          <a href="/status">Status</a>
        </nav>
        <div className="flex gap-3">
          <a href="/login" className="text-sm text-slate-600">Login</a>
          <a href="/signup" className="rounded-md bg-blue-600 px-4 py-2 text-white text-sm">Start Free Trial</a>
        </div>
      </div>
    </header>
  );
}

